# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ChannelProductAttribute(models.Model):
    """Map Odoo product attribute values to channel-specific attribute names.

    Example: Odoo "Color/Red" -> Shopee "Color/แดง"
    """
    _name = 'channel.product.attribute'
    _description = 'Channel Product Attribute Mapping'
    _order = 'channel_id, sequence, id'
    _sql_constraints = [
        ('channel_attr_value_unique',
         'unique(channel_id, odoo_attribute_id, odoo_value_id, platform_attr_name)',
         'This attribute mapping already exists!')
    ]

    active = fields.Boolean(string='Active', default=True)
    channel_id = fields.Many2one(
        'channel.config', string='Channel', required=True, index=True, ondelete='cascade'
    )
    sequence = fields.Integer(string='Sequence', default=10)
    channel_product_id = fields.Many2one(
        'channel.product', string='Channel Product', ondelete='cascade', index=True
    )
    odoo_attribute_id = fields.Many2one(
        'product.attribute', string='Odoo Attribute', required=True,
        help='Source attribute (e.g. Color, Size)'
    )
    odoo_value_id = fields.Many2one(
        'product.attribute.value', string='Odoo Value', required=True,
        domain="[('attribute_id', '=', odoo_attribute_id)]"
    )
    platform_attr_name = fields.Char(
        string='Platform Attribute Name', required=True,
        help='Attribute name as it should appear on the platform (e.g. Color, สี)'
    )
    platform_attr_value = fields.Char(
        string='Platform Attribute Value', required=True,
        help='Value as it should appear on the platform (e.g. Red, แดง)'
    )
    is_mandatory = fields.Boolean(string='Mandatory', default=True)
    is_custom = fields.Boolean(
        string='Custom Attribute',
        help='True if this is a custom attribute (not part of variant)'
    )

    @api.onchange('odoo_attribute_id')
    def _onchange_attribute(self):
        if self.odoo_attribute_id:
            self.platform_attr_name = self.odoo_attribute_id.name

    @api.onchange('odoo_value_id')
    def _onchange_value(self):
        if self.odoo_value_id:
            self.platform_attr_value = self.odoo_value_id.name

    def get_platform_variant_data(self):
        """Return dict suitable for Shopee/Lazada/TikTok variant API."""
        return {
            'attr_name': self.platform_attr_name,
            'attr_value': self.platform_attr_value,
            'is_mandatory': self.is_mandatory,
        }

    # ========== Additional Methods ==========
    def _compute_display_name(self):
        """Generate display name for attribute mapping."""
        self.ensure_one()
        return '%s / %s' % (self.platform_attr_name or '?', self.platform_attr_value or '?')

    def action_duplicate_for_channel(self, target_channel_id):
        """Duplicate this mapping to another channel."""
        self.ensure_one()
        new_mapping = self.copy({
            'channel_id': target_channel_id,
        })
        return new_mapping

    @api.model
    def find_mapping(self, channel_id, odoo_attribute_id, odoo_value_id):
        """Find existing mapping by attribute and value."""
        return self.search([
            ('channel_id', '=', channel_id),
            ('odoo_attribute_id', '=', odoo_attribute_id),
            ('odoo_value_id', '=', odoo_value_id),
        ], limit=1)


class ChannelProductVariant(models.Model):
    """Track variants (product.product records) per channel product."""
    _name = 'channel.product.variant'
    _description = 'Channel Product Variant'
    _rec_name = 'product_variant_id'
    _sql_constraints = [
        ('cp_variant_unique',
         'unique(channel_product_id, product_variant_id)',
         'Variant already mapped to this channel product!')
    ]

    channel_product_id = fields.Many2one(
        'channel.product', string='Channel Product',
        required=True, ondelete='cascade', index=True
    )
    channel_id = fields.Many2one(
        'channel.config', string='Channel',
        related='channel_product_id.channel_id', store=True
    )
    product_variant_id = fields.Many2one(
        'product.product', string='Odoo Variant', required=True,
        domain="[('product_tmpl_id', '=', parent.product_id.product_tmpl_id)]"
    )
    product_tmpl_id = fields.Many2one(
        'product.template', string='Template',
        related='product_variant_id.product_tmpl_id', store=True
    )
    variant_sku = fields.Char(
        string='Variant SKU', related='product_variant_id.default_code', store=True
    )
    platform_variant_id = fields.Char(
        string='Platform Variant ID',
        help='ID returned by platform after variant creation'
    )
    platform_variant_url = fields.Char(string='Platform Variant URL')
    channel_price = fields.Float(string='Variant Price')
    channel_qty = fields.Integer(string='Variant Stock', default=0)
    channel_weight = fields.Float(string='Variant Weight (kg)')
    attribute_mapping_ids = fields.One2many(
        'channel.product.attribute', 'channel_product_id',
        string='Attribute Mappings',
        domain=lambda self: [('channel_id', '=', self.channel_id.id)]
    )
    sync_status = fields.Selection([
        ('pending', 'Pending'),
        ('synced', 'Synced'),
        ('error', 'Error'),
    ], string='Sync Status', default='pending')

    def _variant_attr_display(self):
        """Return variant attribute display like: Color: Red, Size: L."""
        self.ensure_one()
        attrs = []
        for line in self.product_variant_id.product_template_attribute_value_ids:
            attr = line.attribute_id
            value = line.product_attribute_value_id
            platform_attr = self.attribute_mapping_ids.filtered(
                lambda a: a.odoo_attribute_id == attr and a.odoo_value_id == value
            )
            if platform_attr:
                attrs.append('%s: %s' % (platform_attr.platform_attr_name, platform_attr.platform_attr_value))
            else:
                attrs.append('%s: %s' % (attr.name, value.name))
        return ', '.join(attrs)

    def name_get(self):
        result = []
        for rec in self:
            name = rec.product_variant_id.display_name
            attrs = rec._variant_attr_display()
            if attrs:
                name = '%s (%s)' % (name, attrs)
            result.append((rec.id, name))
        return result

    # ============================================================
    # ACTIONS
    # ============================================================
    def action_sync_variant(self):
        """Sync variant ไป platform (generic - legacy)"""
        for rec in self:
            try:
                _logger.info('Syncing variant %s to %s', rec.product_variant_id.display_name, rec.channel_id.code)
                rec.write({'sync_status': 'synced'})
            except Exception as e:
                rec.write({'sync_status': 'error'})
                _logger.error('Variant sync failed: %s', e)
        return True

    def action_sync_to_platform(self):
        """Sync variant ไป platform (Shopee/Lazada/TikTok)"""
        for rec in self:
            try:
                if not rec.channel_id:
                    raise ValidationError(_('No channel configured.'))
                
                channel = rec.channel_id
                payload = rec.get_platform_payload()
                
                _logger.info('Syncing variant %s to %s', rec.display_name, channel.code)
                
                if channel.code == 'shopee':
                    result = rec._sync_to_shopee(payload)
                elif channel.code == 'lazada':
                    result = rec._sync_to_lazada(payload)
                elif channel.code == 'tiktok':
                    result = rec._sync_to_tiktok(payload)
                else:
                    result = {'success': True, 'platform_variant_id': f'MOCK-{rec.id}'}
                
                if result.get('success'):
                    rec.write({
                        'sync_status': 'synced',
                        'platform_variant_id': result.get('platform_variant_id', rec.platform_variant_id),
                    })
                else:
                    rec.write({'sync_status': 'error'})
                    
            except ValidationError:
                raise
            except Exception as e:
                rec.write({'sync_status': 'error'})
                _logger.error('Variant sync failed: %s', str(e))
        return True

    def action_create_on_platform(self):
        """สร้าง variant ใหม่บน platform"""
        for rec in self:
            try:
                rec.ensure_can_create_on_platform()
                channel = rec.channel_id
                payload = rec.get_platform_payload()
                
                _logger.info('Creating variant %s on %s', rec.display_name, channel.code)
                
                if channel.code == 'shopee':
                    result = rec._create_on_shopee(payload)
                elif channel.code == 'lazada':
                    result = rec._create_on_lazada(payload)
                elif channel.code == 'tiktok':
                    result = rec._create_on_tiktok(payload)
                else:
                    result = {'success': True, 'platform_variant_id': f'NEW-{rec.id}'}
                
                if result.get('success'):
                    rec.write({
                        'sync_status': 'synced',
                        'platform_variant_id': result.get('platform_variant_id'),
                        'platform_variant_url': result.get('platform_variant_url', ''),
                    })
                else:
                    rec.write({'sync_status': 'error'})
                    raise ValidationError(result.get('error', 'Failed to create'))
                    
            except ValidationError:
                raise
            except Exception as e:
                rec.write({'sync_status': 'error'})
                _logger.error('Create variant failed: %s', str(e))
                raise ValidationError(str(e))
        return True

    def action_update_on_platform(self):
        """อัปเดต variant ที่มีอยู่บน platform"""
        for rec in self:
            try:
                if not rec.platform_variant_id:
                    raise ValidationError(_('Not created on platform yet. Use "Create" first.'))
                
                channel = rec.channel_id
                payload = rec.get_platform_payload()
                
                _logger.info('Updating variant %s on %s', rec.display_name, channel.code)
                
                if channel.code == 'shopee':
                    result = rec._update_on_shopee(rec.platform_variant_id, payload)
                elif channel.code == 'lazada':
                    result = rec._update_on_lazada(rec.platform_variant_id, payload)
                elif channel.code == 'tiktok':
                    result = rec._update_on_tiktok(rec.platform_variant_id, payload)
                else:
                    result = {'success': True}
                
                if result.get('success'):
                    rec.write({'sync_status': 'synced'})
                else:
                    rec.write({'sync_status': 'error'})
                    raise ValidationError(result.get('error', 'Failed to update'))
                    
            except ValidationError:
                raise
            except Exception as e:
                rec.write({'sync_status': 'error'})
                _logger.error('Update variant failed: %s', str(e))
                raise ValidationError(str(e))
        return True

    def action_delete_from_platform(self):
        """ลบ variant ออกจาก platform"""
        for rec in self:
            try:
                if not rec.platform_variant_id:
                    _logger.info('Variant %s not on platform, skipping delete', rec.display_name)
                    continue
                
                channel = rec.channel_id
                _logger.info('Deleting variant %s from %s', rec.display_name, channel.code)
                
                if channel.code == 'shopee':
                    result = rec._delete_from_shopee(rec.platform_variant_id)
                elif channel.code == 'lazada':
                    result = rec._delete_from_lazada(rec.platform_variant_id)
                elif channel.code == 'tiktok':
                    result = rec._delete_from_tiktok(rec.platform_variant_id)
                else:
                    result = {'success': True}
                
                if result.get('success'):
                    rec.write({
                        'sync_status': 'pending',
                        'platform_variant_id': False,
                        'platform_variant_url': False,
                    })
                else:
                    raise ValidationError(result.get('error', 'Failed to delete'))
                    
            except ValidationError:
                raise
            except Exception as e:
                _logger.error('Delete variant failed: %s', str(e))
                raise ValidationError(str(e))
        return True

    def action_retry_sync(self):
        """Retry sync สำหรับ variants ที่ fail"""
        failed = self.filtered(lambda r: r.sync_status == 'error')
        if not failed:
            return True
        
        for rec in failed:
            if rec.platform_variant_id:
                rec.action_update_on_platform()
            else:
                rec.action_create_on_platform()
        return True

    def action_view_on_platform(self):
        """เปิด URL ของ variant บน platform"""
        self.ensure_one()
        if not self.platform_variant_url:
            raise ValidationError(_('No platform URL available. Sync the variant first.'))
        
        return {
            'type': 'ir.actions.act_url',
            'url': self.platform_variant_url,
            'target': 'new',
        }

    # ============================================================
    # VALIDATION
    # ============================================================
    def ensure_can_create_on_platform(self):
        """Validate ว่า variant พร้อมสำหรับ create บน platform"""
        self.ensure_one()
        if not self.channel_id:
            raise ValidationError(_('No channel configured.'))
        if not self.product_variant_id:
            raise ValidationError(_('No Odoo variant selected.'))
        if not self.channel_price or self.channel_price <= 0:
            raise ValidationError(_('Channel price must be set and > 0.'))
        parent = self.channel_product_id
        if parent and parent.state != 'active':
            raise ValidationError(_('Parent channel product must be active.'))
        return True

    @api.constrains('channel_price', 'channel_qty')
    def _check_variant_values(self):
        for rec in self:
            if rec.channel_price < 0:
                raise ValidationError(_('Variant price cannot be negative.'))
            if rec.channel_qty < 0:
                raise ValidationError(_('Variant quantity cannot be negative.'))

    # ============================================================
    # PLATFORM PAYLOAD
    # ============================================================
    def get_platform_payload(self):
        """Return dict for Shopee/Lazada/TikTok variant API."""
        self.ensure_one()
        
        variant = self.product_variant_id
        product = self.channel_product_id
        
        payload = {
            'sku': self.variant_sku or variant.default_code or f'VAR-{self.id}',
            'price': self.channel_price,
            'quantity': self.channel_qty,
            'weight': self.channel_weight or 0,
            'variant_id': variant.id,
        }
        
        # Attribute mappings
        attrs = []
        for attr_line in variant.product_template_attribute_value_ids:
            attr = attr_line.attribute_id
            value = attr_line.product_attribute_value_id
            
            mapping = self.attribute_mapping_ids.filtered(
                lambda m: m.odoo_attribute_id == attr.id and m.odoo_value_id == value.id
            )
            
            if mapping:
                attrs.append({'name': mapping.platform_attr_name, 'value': mapping.platform_attr_value})
            else:
                attrs.append({'name': attr.name, 'value': value.name})
        
        payload['attributes'] = attrs
        
        if product:
            payload.update({
                'parent_product_id': product.platform_product_id,
                'parent_sku': product.product_sku,
            })
        
        return payload

    # ============================================================
    # PLATFORM MOCK METHODS
    # ============================================================
    def _sync_to_shopee(self, payload):
        import time
        _logger.info('Shopee sync: %s', payload.get('sku'))
        return {'success': True, 'platform_variant_id': f'SHOPEE-{int(time.time())}-{self.id}'}

    def _sync_to_lazada(self, payload):
        import time
        _logger.info('Lazada sync: %s', payload.get('sku'))
        return {'success': True, 'platform_variant_id': f'LAZADA-{int(time.time())}-{self.id}'}

    def _sync_to_tiktok(self, payload):
        import time
        _logger.info('TikTok sync: %s', payload.get('sku'))
        return {'success': True, 'platform_variant_id': f'TIKTOK-{int(time.time())}-{self.id}'}

    def _create_on_shopee(self, payload):
        return self._sync_to_shopee(payload)

    def _create_on_lazada(self, payload):
        return self._sync_to_lazada(payload)

    def _create_on_tiktok(self, payload):
        return self._sync_to_tiktok(payload)

    def _update_on_shopee(self, platform_variant_id, payload):
        _logger.info('Shopee update: %s', platform_variant_id)
        return {'success': True}

    def _update_on_lazada(self, platform_variant_id, payload):
        _logger.info('Lazada update: %s', platform_variant_id)
        return {'success': True}

    def _update_on_tiktok(self, platform_variant_id, payload):
        _logger.info('TikTok update: %s', platform_variant_id)
        return {'success': True}

    def _delete_from_shopee(self, platform_variant_id):
        _logger.info('Shopee delete: %s', platform_variant_id)
        return {'success': True}

    def _delete_from_lazada(self, platform_variant_id):
        _logger.info('Lazada delete: %s', platform_variant_id)
        return {'success': True}

    def _delete_from_tiktok(self, platform_variant_id):
        _logger.info('TikTok delete: %s', platform_variant_id)
        return {'success': True}


