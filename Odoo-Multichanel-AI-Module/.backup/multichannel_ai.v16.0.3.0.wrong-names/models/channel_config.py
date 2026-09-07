# -*- coding: utf-8 -*-
# Main Channel Config Model - Fields only
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ChannelConfig(models.Model):
    """Main Channel Configuration Model.
    
    Methods are organized in mixins for better maintainability:
    - SyncActionsMixin: sync products/orders
    - TokenActionsMixin: token refresh
    - ConnectionMixin: test connection
    """
    _name = 'channel.config'
    _description = 'E-Commerce Channel'
    _order = 'sequence, name'
    _inherit = ['mail.thread', 'channel.sync.actions', 'channel.token.actions',
                 'channel.connection', 'channel.counts']

    name = fields.Char(string='Channel Name', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)

    # Platform / Channel Type
    platform = fields.Selection([
        ('shopee', 'Shopee'),
        ('lazada', 'Lazada'),
        ('tiktok', 'TikTok Shop'),
        ('line', 'LINE Shopping'),
        ('facebook', 'Facebook Shop'),
    ], string='Platform', required=True, tracking=True)

    # API / Connection
    api_url = fields.Selection([
        ('sandbox', 'Sandbox (MOCK)'),
        ('production', 'Production (Real API)'),
    ], string='API Mode', default='sandbox', required=True)

    base_url = fields.Char(string='Base URL')
    partner_id = fields.Char(string='Partner ID')
    partner_key = fields.Char(string='Partner Key')
    shop_id = fields.Char(string='Shop ID')
    access_token = fields.Char(string='Access Token', tracking=True)
    refresh_token = fields.Char(string='Refresh Token')
    token_expire_date = fields.Datetime(string='Token Expiry', tracking=True)

    # ===========================
    # AI Availability (computed, not stored)
    # ===========================
    ai_available = fields.Boolean(
        string='AI Available',
        compute='_compute_ai_available',
        store=False,
        help='Indicates if AI Engine module is installed'
    )
    ai_pricing_enabled = fields.Boolean(
        string='AI Pricing Enabled',
        compute='_compute_ai_available',
        store=False,
        help='AI-powered pricing is available when this is True'
    )

    @api.depends()
    def _compute_ai_available(self):
        """Check if AI Engine module is available."""
        for rec in self:
            try:
                # Try to access ai.engine model
                rec.env['multichannel.ai.engine'].search([], limit=1)
                rec.ai_available = True
                rec.ai_pricing_enabled = True
            except Exception:
                rec.ai_available = False
                rec.ai_pricing_enabled = False

    # ===========================
    # Onchange & Constraints
    # ===========================
    @api.onchange('platform')
    def _onchange_platform(self):
        base_urls = {
            'shopee': 'https://partner.shopeemobile.com',
            'lazada': 'https://api.lazada.co.id/rest',
            'tiktok': 'https://open-api.tiktokglobalshop.com',
            'line': 'https://api.line.me',
            'facebook': 'https://graph.facebook.com',
        }
        for rec in self:
            if rec.platform:
                rec.base_url = base_urls.get(rec.platform, '')

    @api.constrains('code')
    def _check_code_unique(self):
        for rec in self:
            if self.search_count([('code', '=', rec.code), ('id', '!=', rec.id)]) > 0:
                raise ValidationError(_('Channel code must be unique! Code: %s') % rec.code)

    @api.constrains('api_url', 'partner_key', 'shop_id')
    def _check_production_required(self):
        for rec in self:
            if rec.api_url == 'production' and not (rec.partner_key and rec.shop_id):
                raise ValidationError(_('Production mode requires Partner Key and Shop ID.'))
