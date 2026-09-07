# -*- coding: utf-8 -*-
"""
Channel List Add Wizard
Wizard สำหรับเพิ่ม Channel ใหม่
(Extracted from models/channel_list_module.py - Phase 11.1)
"""
from odoo import _, fields, models
from odoo.exceptions import ValidationError


class ChannelListAddWizard(models.TransientModel):
    """Wizard สำหรับเพิ่ม Channel ใหม่"""
    _name = 'channel.list.add.wizard'
    _description = 'Add New Channel Wizard'

    name = fields.Char(
        string='Channel Name',
        required=True,
        help='ชื่อ Platform เช่น LINE Shopping, Amazon'
    )
    code = fields.Char(
        string='Code',
        required=True,
        help='รหัสสั้น เช่น line, amazon'
    )
    icon = fields.Char(
        string='Icon',
        default='🛍️',
        help='Emoji icon'
    )
    description = fields.Text(
        string='Description',
        help='คำอธิบาย Platform'
    )
    platform_url = fields.Char(
        string='Platform URL',
        help='URL หลักของ Platform'
    )
    developer_url = fields.Char(
        string='Developer Portal URL',
        help='URL สำหรับ Developer Portal'
    )

    def action_add_channel(self):
        """เพิ่ม Channel ใหม่"""
        self.ensure_one()
        ChannelList = self.env['channel.list.module']

        existing = ChannelList.search([('code', '=', self.code)], limit=1)
        if existing:
            raise ValidationError(
                _('Channel with code "%s" already exists!') % self.code
            )

        ChannelList.create({
            'name': self.name,
            'code': self.code,
            'icon': self.icon,
            'description': self.description,
            'platform_url': self.platform_url,
            'developer_url': self.developer_url,
            'active': True,
            'is_installed': False,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Channel Added'),
                'message': _('Channel "%s" has been added. Please configure API settings.') % self.name,
                'type': 'success',
            }
        }
