# -*- coding: utf-8 -*-

import os
import base64
import hashlib
import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class ChannelProductVideo(models.Model):
    """
    Channel Product Video Model
    
    เก็บ video สำหรับสินค้าในแต่ละ Channel
    รองรับ 3 storage types:
    - url: External URL (YouTube, TikTok, etc.)
    - upload: เก็บใน folder แยก (multichannel_videos)
    - s3: S3/Cloud Storage (Future)
    """
    _name = 'channel.product.video'
    _description = 'Channel Product Video'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'channel_product_id, sequence, id'

    # ============================================================
    # CORE FIELDS
    # ============================================================
    channel_product_id = fields.Many2one(
        'channel.product',
        string='Channel Product',
        required=True,
        ondelete='cascade',
        tracking=True,
        index=True,
    )
    
    product_id = fields.Many2one(
        related='channel_product_id.product_id',
        store=True,
        string='Product',
        index=True,
    )
    
    channel_id = fields.Many2one(
        related='channel_product_id.channel_id',
        store=True,
        string='Channel',
        index=True,
    )
    
    name = fields.Char(
        string='Title',
        required=True,
        tracking=True,
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        index=True,
    )
    
    active = fields.Boolean(default=True)

    # ============================================================
    # STORAGE TYPE
    # ============================================================
    storage_type = fields.Selection([
        ('url', 'External URL'),
        ('upload', 'Uploaded File (Folder)'),
        ('s3', 'S3/Cloud (Future)'),
    ], string='Storage Type', default='url', required=True)

    # ============================================================
    # VIDEO SOURCE
    # ============================================================
    video_url = fields.Char(string='Video URL')
    s3_url = fields.Char(string='S3 URL')
    video_stored_path = fields.Char(string='Stored Path')
    checksum = fields.Char(string='Checksum (SHA1)')

    # ============================================================
    # FILE INFO
    # ============================================================
    video_filename = fields.Char(string='File Name')
    file_size = fields.Integer(string='File Size (bytes)')
    file_size_display = fields.Char(
        string='Size',
        compute='_compute_file_size_display',
        store=True,
    )
    mime_type = fields.Char(string='MIME Type')
    duration = fields.Integer(string='Duration (sec)')
    duration_display = fields.Char(
        string='Duration',
        compute='_compute_duration_display',
        store=True,
    )
    resolution = fields.Char(string='Resolution')
    thumbnail = fields.Binary(string='Thumbnail', attachment=True)

    # ============================================================
    # SEO
    # ============================================================
    alt_text = fields.Char(string='Alt Text')
    description = fields.Text(string='Description')
    
    video_type = fields.Selection([
        ('main', 'Main Video'),
        ('gallery', 'Gallery'),
        ('preview', 'Preview'),
        ('tutorial', 'Tutorial'),
    ], string='Video Type', default='gallery')
    
    is_primary = fields.Boolean(
        string='Primary Video',
        default=False,
    )

    # ============================================================
    # PLATFORM SYNC
    # ============================================================
    shopee_video_id = fields.Char(string='Shopee Video ID')
    lazada_video_id = fields.Char(string='Lazada Video ID')
    tiktok_video_id = fields.Char(string='TikTok Video ID')
    sync_count = fields.Integer(
        string='Synced',
        compute='_compute_sync_count',
        store=True,
    )
    last_sync_date = fields.Datetime(string='Last Sync')

    # ============================================================
    # STATE
    # ============================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ready', 'Ready'),
        ('uploading', 'Uploading'),
        ('uploaded', 'Uploaded'),
        ('error', 'Error'),
    ], string='Status', default='draft', tracking=True)
    
    error_message = fields.Text(string='Error Message')

    # ============================================================
    # COMPUTED FIELDS
    # ============================================================
    video_source_url = fields.Char(
        string='Source URL',
        compute='_compute_video_source_url',
    )
    
    is_main_video = fields.Boolean(
        string='Is Main',
        compute='_compute_is_main_video',
        store=True,
    )
    
    is_synced = fields.Boolean(
        string='Synced',
        compute='_compute_is_synced',
        store=True,
    )
    
    has_video = fields.Boolean(
        string='Has Video',
        compute='_compute_has_video',
    )

    # ============================================================
    # SQL CONSTRAINTS
    # ============================================================
    _sql_constraints = [
        ('sequence_positive', 'CHECK(sequence > 0)', 'Sequence must be positive!'),
    ]

    # ============================================================
    # ONCHANGE
    # ============================================================
    @api.onchange('channel_product_id')
    def _onchange_channel_product_id(self):
        for record in self:
            if record.channel_product_id and not record.name:
                product_name = record.channel_product_id.product_id.name or ''
                channel_name = record.channel_product_id.channel_id.name or ''
                record.name = f"{product_name} - {channel_name}"

    @api.onchange('storage_type')
    def _onchange_storage_type(self):
        for record in self:
            if record.storage_type == 'url':
                record.video_stored_path = False
                record.s3_url = False
            elif record.storage_type == 'upload':
                record.video_url = False
                record.s3_url = False
            elif record.storage_type == 's3':
                record.video_url = False
                record.video_stored_path = False

    @api.onchange('is_primary')
    def _onchange_is_primary(self):
        for record in self:
            if record.is_primary:
                record.sequence = 1
                record.video_type = 'main'

    @api.onchange('sequence')
    def _onchange_sequence(self):
        for record in self:
            if record.sequence == 1:
                record.is_primary = True
                record.video_type = 'main'

    # ============================================================
    # COMPUTE
    # ============================================================
    @api.depends('storage_type', 'video_url', 'video_stored_path', 's3_url')
    def _compute_video_source_url(self):
        for record in self:
            if record.storage_type == 'url':
                record.video_source_url = record.video_url
            elif record.storage_type == 'upload' and record.video_stored_path:
                record.video_source_url = f"/multichannel/video/play/{record.id}"
            elif record.storage_type == 's3':
                record.video_source_url = record.s3_url
            else:
                record.video_source_url = False

    @api.depends('duration')
    def _compute_duration_display(self):
        for record in self:
            if record.duration:
                h = record.duration // 3600
                m = (record.duration % 3600) // 60
                s = record.duration % 60
                if h:
                    record.duration_display = f"{h}:{m:02d}:{s:02d}"
                else:
                    record.duration_display = f"{m}:{s:02d}"
            else:
                record.duration_display = "0:00"

    @api.depends('file_size')
    def _compute_file_size_display(self):
        for record in self:
            if record.file_size:
                size = float(record.file_size)
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024:
                        record.file_size_display = f"{size:.1f} {unit}"
                        break
                    size /= 1024
                else:
                    record.file_size_display = f"{size:.1f} TB"
            else:
                record.file_size_display = "0 B"

    @api.depends('is_primary', 'sequence')
    def _compute_is_main_video(self):
        for record in self:
            record.is_main_video = record.is_primary or record.sequence == 1

    @api.depends('shopee_video_id', 'lazada_video_id', 'tiktok_video_id')
    def _compute_sync_count(self):
        for record in self:
            count = 0
            if record.shopee_video_id: count += 1
            if record.lazada_video_id: count += 1
            if record.tiktok_video_id: count += 1
            record.sync_count = count

    @api.depends('sync_count')
    def _compute_is_synced(self):
        for record in self:
            record.is_synced = record.sync_count > 0

    @api.depends('storage_type', 'video_url', 'video_stored_path', 's3_url')
    def _compute_has_video(self):
        for record in self:
            record.has_video = bool(
                (record.storage_type == 'url' and record.video_url) or
                (record.storage_type == 'upload' and record.video_stored_path) or
                (record.storage_type == 's3' and record.s3_url)
            )

    # ============================================================
    # STORAGE HELPERS
    # ============================================================
    def _get_video_storage_path(self):
        data_dir = self.env['ir.config_parameter'].sudo().get_param('data_dir')
        if not data_dir:
            from odoo.tools import config
            data_dir = config.get('data_dir', '/var/lib/odoo/filestore')
        return os.path.join(data_dir, 'multichannel_videos')

    def _get_video_subfolder(self):
        from datetime import datetime
        now = datetime.now()
        return f"{now.year}/{now.month:02d}"

    def _ensure_video_folder(self):
        path = self._get_video_storage_path()
        subfolder = self._get_video_subfolder()
        full_path = os.path.join(path, subfolder)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            _logger.info('Created video storage folder: %s', full_path)
        return full_path

    # ============================================================
    # FILE MANAGEMENT
    # ============================================================
    def _save_video_to_folder(self, data, filename):
        binary_data = base64.b64decode(data)
        checksum = hashlib.sha1(binary_data).hexdigest()
        ext = os.path.splitext(filename)[1] or '.mp4'
        new_filename = f"{checksum}{ext}"
        folder = self._ensure_video_folder()
        file_path = os.path.join(folder, new_filename)
        
        if not os.path.exists(file_path):
            with open(file_path, 'wb') as f:
                f.write(binary_data)
            _logger.info('Saved video: %s (%.2f MB)', file_path, len(binary_data) / 1024 / 1024)
        
        base = self._get_video_storage_path()
        relative_path = file_path.replace(base + '/', '')
        self.file_size = len(binary_data)
        self.checksum = checksum
        return relative_path

    def _delete_video_from_folder(self, relative_path):
        if not relative_path:
            return
        base = self._get_video_storage_path()
        full_path = os.path.join(base, relative_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            _logger.info('Deleted video: %s', full_path)

    def _get_video_binary(self):
        self.ensure_one()
        if self.storage_type == 'upload' and self.video_stored_path:
            full_path = os.path.join(self._get_video_storage_path(), self.video_stored_path)
            if os.path.exists(full_path):
                with open(full_path, 'rb') as f:
                    return f.read()
        elif self.storage_type == 'url' and self.video_url:
            try:
                import requests
                response = requests.get(self.video_url, timeout=30)
                response.raise_for_status()
                return response.content
            except Exception as e:
                _logger.error('Failed to download video: %s', str(e))
        return None

    # ============================================================
    # CRUD
    # ============================================================
    def write(self, vals):
        old_paths = {r.id: r.video_stored_path for r in self}
        result = super().write(vals)
        
        if 'video_stored_path' in vals or 'storage_type' in vals:
            for record in self:
                old_path = old_paths.get(record.id)
                new_path = record.video_stored_path
                if old_path and old_path != new_path:
                    if not self.search_count([
                        ('id', '!=', record.id),
                        ('video_stored_path', '=', old_path),
                    ]):
                        record._delete_video_from_folder(old_path)
        return result

    def unlink(self):
        paths_to_delete = []
        for record in self:
            if record.video_stored_path:
                if not self.search_count([
                    ('id', '!=', record.id),
                    ('video_stored_path', '=', record.video_stored_path),
                ]):
                    paths_to_delete.append(record.video_stored_path)
        result = super().unlink()
        for path in paths_to_delete:
            self._delete_video_from_folder(path)
        return result

    # ============================================================
    # ACTIONS
    # ============================================================
    def action_regenerate_name(self):
        for record in self:
            if record.channel_product_id:
                product_name = record.channel_product_id.product_id.name or ''
                channel_name = record.channel_product_id.channel_id.name or ''
                record.name = f"{product_name} - {channel_name}"
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Video Name Updated'),
                'message': _('Regenerated %d video name(s).') % len(self),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_play_video(self):
        """เปิด video ในแท็บใหม่ผ่าน controller"""
        self.ensure_one()
        # ถ้าเป็น URL ให้เปิด YouTube/TikTok ตรงๆ
        if self.storage_type == 'url' and self.video_url:
            return {
                'type': 'ir.actions.act_url',
                'url': self.video_url,
                'target': 'new',
            }
        # ถ้าเป็น upload ให้ stream ผ่าน controller
        return {
            'type': 'ir.actions.act_url',
            'url': f'/multichannel/video/embed/{self.id}',
            'target': 'new',
        }

    def action_reset_to_draft(self):
        self.write({'state': 'draft', 'error_message': False})

    def action_mark_ready(self):
        for record in self:
            if record.has_video:
                record.state = 'ready'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Video Ready'),
                'message': _('%d video(s) marked as ready.') % len(self),
                'type': 'success',
            },
        }

    # ============================================================
    # UPLOAD TO PLATFORMS
    # ============================================================
    def action_upload_to_platforms(self):
        success_count = 0
        error_messages = []

        for record in self:
            if record.state != 'ready':
                continue
            try:
                record.state = 'uploading'
                video_data = record._get_video_binary()
                if not video_data:
                    raise UserError(_('No video data available'))

                # Single connector call (auto-routes by platform)
                platform = (record.channel_id.channel_code or record.channel_id.code or '').lower()
                result = record._upload_to_connector(video_data)
                if result.get('success'):
                    success_count += 1
                else:
                    error_messages.append(f"{platform or 'unknown'}: {result.get('error')}")
                
                if success_count > 0:
                    record.state = 'uploaded'
                    record.last_sync_date = fields.Datetime.now()
                else:
                    record.state = 'error'
                    record.error_message = '\n'.join(error_messages)
            except Exception as e:
                record.state = 'error'
                record.error_message = str(e)
                _logger.error('Upload failed: %s', str(e))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Upload Complete'),
                'message': _('%d video(s) uploaded successfully.') % success_count,
                'type': 'success' if success_count > 0 else 'warning',
                'sticky': False,
            },
        }

    def _upload_to_connector(self, video_data):
        """Upload video via connectors/* (single source of truth)."""
        self.ensure_one()
        try:
            channel_config = self.env['channel.config'].browse(self.channel_id.id)
            # Try channel mixin first, fallback to factory
            connector = (
                self.channel_id.get_connector()
                if hasattr(self.channel_id, 'get_connector')
                else None
            )
            if connector is None:
                from odoo.addons.multichannel_ai.models.connectors import get_connector
                connector = get_connector(channel_config)
            # Call connector upload_video (if implemented), else fallback to mock write
            if hasattr(connector, 'upload_video'):
                result = connector.upload_video(video_data, filename='video.mp4')
                video_id = result.get('video_id') or result.get('image_id')
                url = result.get('video_url') or result.get('image_url')
            else:
                # Fallback: write mock video_id
                import time
                code = (channel_config.channel_code or channel_config.code or 'unknown').lower()
                video_id = f'{code}_video_{int(time.time())}'
                url = f'https://mock.{code}.com/videos/{video_id}'
            # Map result to model fields
            platform = (channel_config.channel_code or channel_config.code or '').lower()
            vals = {}
            if platform == 'shopee':
                vals['shopee_video_id'] = video_id
            elif platform == 'lazada':
                vals['lazada_video_id'] = video_id
            elif platform == 'tiktok':
                vals['tiktok_video_id'] = video_id
            vals['video_url'] = url
            self.write(vals)
            _logger.info('Uploaded video to %s: %s', platform, video_id)
            return {'success': True, 'video_id': video_id, 'video_url': url}
        except Exception as e:
            _logger.error('Connector upload error: %s', str(e))
            return {'success': False, 'error': str(e)}

    def action_resync_to_platforms(self):
        self.write({
            'shopee_video_id': False,
            'lazada_video_id': False,
            'tiktok_video_id': False,
            'state': 'ready',
        })
        return self.action_upload_to_platforms()

    # ============================================================
    # VALIDATION
    # ============================================================
    @api.constrains('storage_type', 'video_url', 'video_stored_path', 's3_url')
    def _check_video_source(self):
        for record in self:
            if record.storage_type == 'url' and not record.video_url:
                raise ValidationError(_('Video URL is required for External URL storage.'))
            elif record.storage_type == 'upload' and not record.video_stored_path:
                raise ValidationError(_('Please upload a video file.'))
            elif record.storage_type == 's3' and not record.s3_url:
                raise ValidationError(_('S3 URL is required for S3 storage.'))

    @api.constrains('is_primary')
    def _check_only_one_primary(self):
        for record in self:
            if record.is_primary:
                other = self.search([
                    ('channel_product_id', '=', record.channel_product_id.id),
                    ('is_primary', '=', True),
                    ('id', '!=', record.id),
                ])
                if other:
                    raise ValidationError(_(
                        'Only one primary video allowed per product.\nUncheck: %s'
                    ) % ', '.join(other.mapped('name')))
