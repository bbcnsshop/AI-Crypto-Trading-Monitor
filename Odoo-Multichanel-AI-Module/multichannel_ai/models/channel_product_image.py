# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging, base64, requests
from io import BytesIO

_logger = logging.getLogger(__name__)


class ChannelProductImage(models.Model):
    """Images for a channel product - linked to channel.product."""
    _name = 'channel.product.image'
    _description = 'Channel Product Image'
    _order = 'sequence, id'
    _sql_constraints = [
        ('cp_sequence_unique', 'unique(channel_product_id, sequence)',
         'Sequence must be unique per product-channel!')
    ]

    channel_product_id = fields.Many2one(
        'channel.product', string='Channel Product',
        required=True, ondelete='cascade', index=True
    )
    channel_id = fields.Many2one(
        'channel.config', string='Channel',
        related='channel_product_id.channel_id', store=True, index=True
    )
    product_id = fields.Many2one(
        'product.product', string='Product',
        related='channel_product_id.product_id', store=True
    )
    sequence = fields.Integer(string='Sequence', default=10)
    is_primary = fields.Boolean(string='Primary Image', default=False)

    # Odoo source
    source_type = fields.Selection([
        ('product', 'Product Image'),
        ('variant', 'Variant Image'),
        ('url', 'External URL'),
        ('binary', 'Uploaded'),
    ], string='Source Type', default='product')
    odoo_image_field = fields.Char(
        string='Odoo Image Field',
        help='Field name on product.product, e.g. image_1920, image_128'
    )

    # Image data
    image_url = fields.Char(string='Image URL')
    image_id_on_platform = fields.Char(string='Platform Image ID')
    platform_image_url = fields.Char(string='Platform Image URL')
    upload_status = fields.Selection([
        ('pending', 'Pending Upload'),
        ('uploading', 'Uploading'),
        ('uploaded', 'Uploaded'),
        ('error', 'Upload Error'),
    ], string='Upload Status', default='pending', index=True)
    upload_message = fields.Text(string='Upload Message')
    last_upload = fields.Datetime(string='Last Upload Attempt')

    # Metadata
    width = fields.Integer(string='Width')
    height = fields.Integer(string='Height')
    file_size = fields.Integer(string='File Size (bytes)')
    checksum = fields.Char(string='Checksum (MD5)')

    # SEO & Image Type
    alt_text = fields.Char(
        string='Alt Text',
        size=255,
        help='Alt text สำหรับ SEO - คำอธิบายรูปภาพ'
    )
    image_type = fields.Selection([
        ('main', 'Main Image'),
        ('gallery', 'Gallery'),
        ('detail', 'Detail Image'),
        ('thumbnail', 'Thumbnail'),
    ], string='Image Type', default='gallery',
        help='ประเภทของรูปภาพ (main, gallery, detail, thumbnail)')

    # Platform-specific IDs
    shopee_image_id = fields.Char(string='Shopee Image ID', readonly=True)
    lazada_image_id = fields.Char(string='Lazada Image ID', readonly=True)
    tiktok_image_id = fields.Char(string='TikTok Image ID', readonly=True)

    @api.onchange('source_type')
    def _onchange_source_type(self):
        if self.source_type == 'product':
            self.odoo_image_field = 'image_1920'
        elif self.source_type == 'variant':
            self.odoo_image_field = 'image_variant_1920'
        else:
            self.odoo_image_field = False

    @api.onchange('channel_product_id')
    def _onchange_channel_product_id(self):
        """Auto-generate alt_text เมื่อเปลี่ยน channel_product."""
        if self.channel_product_id:
            self._compute_default_alt_text()

    @api.onchange('sequence', 'is_primary')
    def _onchange_sequence_primary(self):
        """Auto-set image_type จาก sequence/is_primary."""
        self._compute_default_image_type()

    def _compute_default_alt_text(self):
        """Generate alt_text อัตโนมัติ: '{product_name} - {channel_name}'."""
        self.ensure_one()
        if not self.channel_product_id:
            return

        product_name = self.channel_product_id.product_id.name or 'Product'
        channel_name = self.channel_product_id.channel_id.name or 'Channel'

        self.alt_text = '%s - %s' % (product_name, channel_name)

    def _compute_default_image_type(self):
        """Set image_type จาก sequence/is_primary.

        Logic:
        - is_primary = True → 'main'
        - sequence = 1 → 'main'
        - 2 ≤ sequence ≤ 10 → 'gallery'
        - sequence > 10 → 'thumbnail'
        """
        self.ensure_one()
        if self.is_primary or self.sequence == 1:
            self.image_type = 'main'
        elif 2 <= self.sequence <= 10:
            self.image_type = 'gallery'
        elif self.sequence > 10:
            self.image_type = 'thumbnail'
        # ถ้า sequence < 1 (ไม่ควรเกิด) ปล่อย default

    def action_regenerate_alt_text(self):
        """ปุ่มสำหรับ regenerate alt_text ใหม่.

        Returns: notification message
        """
        self.ensure_one()
        old_alt = self.alt_text
        self._compute_default_alt_text()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Alt Text Regenerated'),
                'message': _('Alt text updated: "%s" → "%s"') % (old_alt, self.alt_text),
                'type': 'success',
                'sticky': False,
            }
        }

    def _get_image_data(self):
        """Resolve image binary from source."""
        self.ensure_one()
        product = self.product_id
        if not product:
            return False, False

        if self.source_type == 'product':
            field = self.odoo_image_field or 'image_1920'
            img = getattr(product, field, False)
            return img, field
        elif self.source_type == 'variant':
            field = self.odoo_image_field or 'image_variant_1920'
            img = getattr(product, field, False)
            return img, field
        elif self.source_type == 'url':
            return False, 'external_url'
        else:
            return False, False

    def _download_from_url(self, url):
        """Download image from external URL."""
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                return resp.content
        except Exception as e:
            _logger.error('Failed to download image from %s: %s', url, e)
        return False

    def _prepare_image_for_upload(self, raw_bytes):
        """Prepare image: resize if needed, get metadata."""
        import hashlib
        md5 = hashlib.md5(raw_bytes).hexdigest()
        return raw_bytes, md5, len(raw_bytes)

    def _upload_to_shopee(self, raw_bytes, filename='image.jpg'):
        """Upload to Shopee API. Returns (platform_image_id, platform_image_url)."""
        channel_config = self.env['channel.config'].browse(self.channel_id.id)
        connector = self.channel_id.get_connector() if hasattr(self.channel_id, 'get_connector') else None
        if not connector:
            # Fallback: use mock
            from odoo.addons.multichannel_ai.models.connectors.shopee import ShopeeConnector
            connector = ShopeeConnector(channel_config)
        result = connector.upload_image(raw_bytes, filename)
        return result.get('image_id'), result.get('image_url')

    def _upload_to_lazada(self, raw_bytes, filename='image.jpg'):
        channel_config = self.env['channel.config'].browse(self.channel_id.id)
        connector = self.channel_id.get_connector() if hasattr(self.channel_id, 'get_connector') else None
        if not connector:
            from odoo.addons.multichannel_ai.models.connectors.lazada import LazadaConnector
            connector = LazadaConnector(channel_config)
        result = connector.upload_image(raw_bytes, filename)
        return result.get('image_id'), result.get('image_url')

    def _upload_to_tiktok(self, raw_bytes, filename='image.jpg'):
        channel_config = self.env['channel.config'].browse(self.channel_id.id)
        connector = self.channel_id.get_connector() if hasattr(self.channel_id, 'get_connector') else None
        if not connector:
            from odoo.addons.multichannel_ai.models.connectors.tiktok import TikTokConnector
            connector = TikTokConnector(channel_config)
        result = connector.upload_image(raw_bytes, filename)
        return result.get('image_id'), result.get('image_url')

    def action_upload(self):
        """Upload this image to the platform."""
        for rec in self:
            try:
                rec.write({'upload_status': 'uploading'})

                # Get image binary
                img_binary, src = rec._get_image_data()
                if rec.source_type == 'url':
                    img_binary = rec._download_from_url(rec.image_url or '')
                    src = 'downloaded'

                if not img_binary:
                    rec.write({
                        'upload_status': 'error',
                        'upload_message': 'Could not resolve image data',
                        'last_upload': fields.Datetime.now()
                    })
                    continue

                prepared, checksum, fsize = rec._prepare_image_for_upload(img_binary)
                rec.write({'checksum': checksum, 'file_size': fsize})

                # Upload per channel
                channel_code = rec.channel_id.code
                if channel_code == 'shopee':
                    pid, purl = rec._upload_to_shopee(prepared)
                elif channel_code == 'lazada':
                    pid, purl = rec._upload_to_lazada(prepared)
                elif channel_code == 'tiktok':
                    pid, purl = rec._upload_to_tiktok(prepared)
                else:
                    rec.write({
                        'upload_status': 'error',
                        'upload_message': 'Unknown channel: %s' % channel_code,
                        'last_upload': fields.Datetime.now()
                    })
                    continue

                rec.write({
                    'image_id_on_platform': pid,
                    'platform_image_url': purl,
                    'upload_status': 'uploaded',
                    'upload_message': 'Uploaded successfully',
                    'last_upload': fields.Datetime.now()
                })
                _logger.info('Uploaded image for %s to %s: %s', rec.name, channel_code, pid)

            except Exception as e:
                rec.write({
                    'upload_status': 'error',
                    'upload_message': str(e),
                    'last_upload': fields.Datetime.now()
                })
                _logger.error('Image upload failed for %s: %s', rec.name, e)
        return True

    def action_retry_upload(self):
        self.filtered(lambda r: r.upload_status == 'error').action_upload()
        return True

# Note: Old API Connectors (ChannelApiConnector, ShopeeApiConnector,
# LazadaApiConnector, TikTokApiConnector) have been removed.
# Use models/connectors/ instead:
# - ShopeeConnector, LazadaConnector, TikTokConnector
# - Use ConnectionMixin.get_connector() to get connector instance


