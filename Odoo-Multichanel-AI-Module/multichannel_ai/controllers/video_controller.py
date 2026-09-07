# -*- coding: utf-8 -*-
"""
Video Controller - Stream Video จาก Folder แยก

Routes:
- /multichannel/video/play/<id>  - Stream video
- /multichannel/video/download/<id> - Download video
- /multichannel/video/thumbnail/<id> - Get thumbnail
"""

import os
import logging
from odoo import http, _
from odoo.http import request, content_disposition
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


class VideoController(http.Controller):

    # ============================================================
    # HELPER: ดึง path
    # ============================================================
    def _get_video_storage_path(self):
        """ดึง path folder เก็บ video"""
        data_dir = request.env['ir.config_parameter'].sudo().get_param('data_dir')
        if not data_dir:
            from odoo.tools import config
            data_dir = config.get('data_dir', '/var/lib/odoo/filestore')
        return os.path.join(data_dir, 'multichannel_videos')

    def _get_video_full_path(self, video):
        """ดึง full path ของ video file"""
        if not video.video_stored_path:
            return None
        base = self._get_video_storage_path()
        return os.path.join(base, video.video_stored_path)

    def _read_video_file(self, video):
        """Read video file from disk"""
        if video.storage_type != 'upload' or not video.video_stored_path:
            return None, None
        
        full_path = self._get_video_full_path(video)
        if not full_path or not os.path.exists(full_path):
            return None, None
        
        try:
            with open(full_path, 'rb') as f:
                data = f.read()
            return data, os.path.getsize(full_path)
        except Exception as e:
            _logger.error('Error reading video file %s: %s', full_path, str(e))
            return None, None

    # ============================================================
    # ROUTE: Stream Video
    # ============================================================
    @http.route([
        '/multichannel/video/play/<int:video_id>',
    ], type='http', auth='user', website=False)
    def play_video(self, video_id, **kwargs):
        """Stream video ไป browser"""
        try:
            video = request.env['channel.product.video'].sudo().browse(video_id)
            if not video.exists():
                return request.not_found()
            
            # URL type - redirect
            if video.storage_type == 'url' and video.video_url:
                return request.redirect(video.video_url, code=301)
            
            # Get file
            video_data, file_size = self._read_video_file(video)
            if not video_data:
                return request.not_found()
            
            headers = [
                ('Content-Type', video.mime_type or 'video/mp4'),
                ('Content-Length', file_size),
                ('Content-Disposition', f'inline; filename="{video.video_filename or "video.mp4"}"'),
                ('Cache-Control', 'max-age=3600'),
            ]
            return request.make_response(video_data, headers=headers)
            
        except Exception as e:
            _logger.error('Error playing video %s: %s', video_id, str(e))
            return request.not_found()

    # ============================================================
    # ROUTE: Download Video
    # ============================================================
    @http.route([
        '/multichannel/video/download/<int:video_id>',
    ], type='http', auth='user', website=False)
    def download_video(self, video_id, **kwargs):
        """Download video file"""
        try:
            video = request.env['channel.product.video'].sudo().browse(video_id)
            if not video.exists():
                return request.not_found()
            
            if video.storage_type == 'url' and video.video_url:
                return request.redirect(video.video_url, code=301)
            
            video_data, file_size = self._read_video_file(video)
            if not video_data:
                return request.not_found()
            
            filename = video.video_filename or 'video.mp4'
            headers = [
                ('Content-Type', 'application/octet-stream'),
                ('Content-Length', file_size),
                ('Content-Disposition', content_disposition(filename)),
            ]
            return request.make_response(video_data, headers=headers)
            
        except Exception as e:
            _logger.error('Error downloading video %s: %s', video_id, str(e))
            return request.not_found()

    # ============================================================
    # ROUTE: Thumbnail
    # ============================================================
    @http.route([
        '/multichannel/video/thumbnail/<int:video_id>',
    ], type='http', auth='user', website=False)
    def get_thumbnail(self, video_id, **kwargs):
        """Get video thumbnail image"""
        try:
            video = request.env['channel.product.video'].sudo().browse(video_id)
            if not video.exists() or not video.thumbnail:
                return request.not_found()
            
            thumbnail_data = video.thumbnail
            if isinstance(thumbnail_data, str):
                import base64
                thumbnail_data = base64.b64decode(thumbnail_data)
            
            headers = [
                ('Content-Type', 'image/png'),
                ('Content-Length', len(thumbnail_data)),
                ('Cache-Control', 'max-age=86400'),
            ]
            return request.make_response(thumbnail_data, headers=headers)
            
        except Exception as e:
            _logger.error('Error getting thumbnail %s: %s', video_id, str(e))
            return request.not_found()

    # ============================================================
    # ROUTE: Video Info (JSON)
    # ============================================================
    @http.route([
        '/multichannel/video/info/<int:video_id>',
    ], type='json', auth='user', website=False)
    def video_info(self, video_id, **kwargs):
        """Get video info as JSON"""
        try:
            video = request.env['channel.product.video'].sudo().browse(video_id)
            if not video.exists():
                return {'error': 'Video not found'}
            
            return {
                'id': video.id,
                'name': video.name,
                'duration': video.duration,
                'duration_display': video.duration_display,
                'file_size': video.file_size,
                'file_size_display': video.file_size_display,
                'mime_type': video.mime_type,
                'video_source_url': video.video_source_url,
                'state': video.state,
                'sync_count': video.sync_count,
            }
        except Exception as e:
            _logger.error('Error getting video info %s: %s', video_id, str(e))
            return {'error': str(e)}

    # ============================================================
    # ROUTE: Embed Video (HTML)
    # ============================================================
    @http.route([
        '/multichannel/video/embed/<int:video_id>',
    ], type='http', auth='user', website=False)
    def embed_video(self, video_id, **kwargs):
        """Return HTML page with video player"""
        try:
            video = request.env['channel.product.video'].sudo().browse(video_id)
            if not video.exists():
                return request.not_found()
            
            video_url = video.video_source_url or f'/multichannel/video/play/{video.id}'
            mime_type = video.mime_type or 'video/mp4'
            
            html = f"""<!DOCTYPE html>
<html><head><title>{video.name}</title>
<style>body{{margin:0;background:#000;display:flex;justify-content:center;align-items:center;height:100vh}}video{{max-width:100%;max-height:100%}}</style>
</head><body>
<video controls autoplay><source src="{video_url}" type="{mime_type}">Not supported</video>
</body></html>"""
            
            return request.make_response(html, headers=[('Content-Type', 'text/html')])
            
        except Exception as e:
            _logger.error('Error embedding video %s: %s', video_id, str(e))
            return request.not_found()