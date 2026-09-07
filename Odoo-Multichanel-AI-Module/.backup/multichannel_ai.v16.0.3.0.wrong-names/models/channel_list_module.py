# -*- coding: utf-8 -*-
"""
Channel List Module - จัดการ Platform Channel ที่รองรับ

หลักการ: Channel เป็น Module ที่เพิ่ม/ลบ/เปิด/ปิด ได้
- มี Channel Module แยกแต่ละ Platform (Shopee, Lazada, TikTok)
- เปิด/ปิด active=True/False ได้ใน Channel Config
- สามารถเพิ่ม Platform ใหม่ได้โดยไม่ต้องแก้โค้ดหลัก
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ChannelListModule(models.Model):
    """จัดการรายการ Platform Channel ที่รองรับ
    
    ตัวอย่าง:
    - Shopee (code: shopee)
    - Lazada (code: lazada)
    - TikTok Shop (code: tiktok)
    
    สามารถเพิ่ม Platform ใหม่ได้ เช่น LINE Shopping, Amazon, Shopify
    """
    _name = 'channel.list.module'
    _description = 'Channel List Module - Platform Manager'
    _order = 'sequence, name'
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Channel code must be unique!'),
    ]

    # ========================
    # Basic Information
    # ========================
    name = fields.Char(
        string='Channel Name',
        required=True,
        help='ชื่อ Platform เช่น Shopee, Lazada, TikTok Shop'
    )
    code = fields.Char(
        string='Code',
        required=True,
        help='รหัสสั้น เช่น shopee, lazada, tiktok (ใช้ในโค้ด)'
    )
    icon = fields.Char(
        string='Icon',
        default='🛒',
        help='Emoji icon เช่น 🛒 🏪 📱 💬'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='ลำดับการแสดงผล'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='เปิด/ปิดการใช้งาน Channel นี้'
    )
    is_installed = fields.Boolean(
        string='Installed',
        default=True,
        help='ติดตั้งแล้วหรือยัง'
    )

    # ========================
    # API Configuration
    # ========================
    api_class = fields.Char(
        string='API Connector Class',
        help='ชื่อ Connector class เช่น shopee.api.connector'
    )
    webhook_url = fields.Char(
        string='Webhook URL',
        help='URL สำหรับรับ webhook เช่น /multichannel/shopee/webhook'
    )
    sync_method = fields.Char(
        string='Sync Method',
        help='ชื่อ method ที่ใช้ sync เช่น _sync_shopee'
    )
    config_model = fields.Char(
        string='Config Model',
        help='ชื่อ model ที่เก็บ config เช่น channel.config'
    )

    # ========================
    # Platform Info
    # ========================
    country_code = fields.Char(
        string='Country Code',
        default='TH',
        help='รหัสประเทศ เช่น TH, MY, SG'
    )
    currency_code = fields.Char(
        string='Currency Code',
        default='THB',
        help='สกุลเงิน เช่น THB, MYR, SGD'
    )
    platform_url = fields.Char(
        string='Platform URL',
        help='URL หลักของ Platform เช่น https://shopee.co.th'
    )
    developer_url = fields.Char(
        string='Developer Portal',
        help='URL สำหรับ Developer Portal'
    )

    # ========================
    # Fee Configuration (Default)
    # ========================
    default_commission_rate = fields.Float(
        string='Commission Rate (%)',
        default=5.0,
        digits=(5, 2),
        help='อัตราค่าคอมมิชชั่นเริ่มต้น %'
    )
    default_payment_fee_rate = fields.Float(
        string='Payment Fee (%)',
        default=2.0,
        digits=(5, 2),
        help='อัตราค่าธรรมเนียมการชำระเงิน %'
    )
    default_shipping_fee_rate = fields.Float(
        string='Shipping Subsidy (%)',
        default=2.5,
        digits=(5, 2),
        help='อัตราค่าสนับสนุนค่าจัดส่ง %'
    )

    # ========================
    # Description & Notes
    # ========================
    description = fields.Text(
        string='Description',
        help='คำอธิบาย Platform'
    )
    note = fields.Text(
        string='Internal Note',
        help='บันทึกภายใน'
    )

    # ========================
    # Color for UI
    # ========================
    color = fields.Integer(
        string='Color Index',
        default=0,
        help='สีสำหรับแสดงผลใน Kanban'
    )

    # ========================
    # Computed Fields
    # ========================
    config_count = fields.Integer(
        string='Configurations',
        compute='_compute_config_count',
        help='จำนวน config ที่ใช้ Channel นี้'
    )
    product_count = fields.Integer(
        string='Products',
        compute='_compute_product_count',
        help='จำนวนสินค้าใน Channel นี้'
    )
    order_count = fields.Integer(
        string='Orders',
        compute='_compute_order_count',
        help='จำนวนออร์เดอร์ใน Channel นี้'
    )

    # ========================
    # Computed Methods
    # ========================
    @api.depends('code')
    def _compute_config_count(self):
        for rec in self:
            if rec.code:
                rec.config_count = self.env['channel.config'].search_count([
                    ('code', '=', rec.code)
                ])
            else:
                rec.config_count = 0

    @api.depends('code')
    def _compute_product_count(self):
        for rec in self:
            if rec.code:
                rec.product_count = self.env['channel.product'].search_count([
                    ('channel_id.code', '=', rec.code)
                ])
            else:
                rec.product_count = 0

    @api.depends('code')
    def _compute_order_count(self):
        for rec in self:
            if rec.code:
                rec.order_count = self.env['channel.order'].search_count([
                    ('channel_id.code', '=', rec.code)
                ])
            else:
                rec.order_count = 0

    # ========================
    # Action Buttons
    # ========================
    def action_activate(self):
        """เปิดใช้งาน Channel"""
        for rec in self:
            rec.write({'active': True})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Channel Activated'),
                'message': _('Selected channels have been activated'),
                'type': 'success',
            }
        }

    def action_deactivate(self):
        """ปิดใช้งาน Channel"""
        for rec in self:
            rec.write({'active': False})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Channel Deactivated'),
                'message': _('Selected channels have been deactivated'),
                'type': 'warning',
            }
        }

    def action_view_configs(self):
        """ดู Configs ที่ใช้ Channel นี้"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('%s Configurations' % self.name),
            'res_model': 'channel.config',
            'view_mode': 'tree,form',
            'domain': [('code', '=', self.code)],
            'context': {'default_code': self.code},
        }

    def action_view_products(self):
        """ดู Products ใน Channel นี้"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('%s Products' % self.name),
            'res_model': 'channel.product',
            'view_mode': 'tree,form,kanban',
            'domain': [('channel_id.code', '=', self.code)],
        }

    def action_view_orders(self):
        """ดู Orders ใน Channel นี้"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('%s Orders' % self.name),
            'res_model': 'channel.order',
            'view_mode': 'tree,form',
            'domain': [('channel_id.code', '=', self.code)],
        }

    def action_test_connection(self):
        """ทดสอบการเชื่อมต่อ API"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Connection Test'),
                'message': _('Connection test for %s - Feature coming soon' % self.name),
                'type': 'info',
            }
        }

    def action_open_developer_portal(self):
        """เปิด Developer Portal"""
        self.ensure_one()
        if not self.developer_url:
            raise ValidationError(_('Developer Portal URL not configured'))
        return {
            'type': 'ir.actions.act_url',
            'url': self.developer_url,
            'target': 'new',
        }

    def action_open_add_channel_wizard(self):
        """เปิด Wizard สำหรับเพิ่ม Channel ใหม่"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add New Channel'),
            'res_model': 'channel.list.add.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    # ========================
    # Override Methods
    # ========================
    @api.model
    def create(self, vals):
        """สร้าง Channel ใหม่"""
        if not vals.get('code') and vals.get('name'):
            vals['code'] = vals['name'].lower().replace(' ', '_')
        return super().create(vals)

    def write(self, vals):
        """อัปเดต Channel"""
        if vals.get('name') and not vals.get('code'):
            vals['code'] = vals['name'].lower().replace(' ', '_')
        return super().write(vals)

    def unlink(self):
        """ลบ Channel"""
        for rec in self:
            if rec.config_count > 0:
                raise ValidationError(
                    _('Cannot delete channel "%s" because it has %d configuration(s). '
                      'Please remove the configurations first.') % (
                          rec.name, rec.config_count
                      )
                )
            if rec.product_count > 0:
                raise ValidationError(
                    _('Cannot delete channel "%s" because it has %d product(s). '
                      'Please remove the products first.') % (
                          rec.name, rec.product_count
                      )
                )
        return super().unlink()

    # ========================
    # Helper Methods
    # ========================
    def get_channel_by_code(self, code):
        """Get channel record by code"""
        return self.search([('code', '=', code), ('active', '=', True)], limit=1)

    def get_active_channels(self):
        """Get all active channels"""
        return self.search([('active', '=', True), ('is_installed', '=', True)])

    def is_channel_active(self, code):
        """Check if channel is active"""
        channel = self.get_channel_by_code(code)
        return bool(channel)


# Note: ChannelListAddWizard extracted to wizards/channel_list_add_wizard.py (Phase 11.1)


