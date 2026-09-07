# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ProductProduct(models.Model):
    _inherit = 'product.product'
    _name = 'product.product'
    
    channel_ids = fields.Many2many(
        'channel.config', 'product_channel_rel', 'product_id', 'channel_id',
        string='Sell on Channels', help='Channels where this product is available'
    )
    channel_product_ids = fields.One2many(
        'channel.product', 'product_id', string='Channel Products', copy=False
    )
    is_sold_online = fields.Boolean(
        string='Sold Online', default=False, index=True,
        help='Indicates if this product is sold through online channels'
    )
    is_on_shopee = fields.Boolean(compute='_compute_channel_status', inverse='_inverse_shopee', string='Shopee')
    is_on_lazada = fields.Boolean(compute='_compute_channel_status', inverse='_inverse_lazada', string='Lazada')
    is_on_tiktok = fields.Boolean(compute='_compute_channel_status', inverse='_inverse_tiktok', string='TikTok')
    online_channel_count = fields.Integer(string='Channel Count', compute='_compute_online_channel_count')
    online_total_stock = fields.Integer(string='Total Online Stock', compute='_compute_online_channel_count')
    online_revenue_potential = fields.Float(string='Online Revenue Potential', compute='_compute_online_channel_count')
    
    @api.depends('channel_product_ids.channel_id', 'channel_product_ids.state')
    def _compute_channel_status(self):
        for rec in self:
            channels = rec.channel_product_ids.filtered(lambda c: c.state in ('active', 'draft')).mapped('channel_id')
            rec.is_on_shopee = bool(channels.filtered(lambda c: c.code == 'shopee'))
            rec.is_on_lazada = bool(channels.filtered(lambda c: c.code == 'lazada'))
            rec.is_on_tiktok = bool(channels.filtered(lambda c: c.code == 'tiktok'))
    
    @api.depends('channel_product_ids', 'channel_product_ids.channel_id', 'channel_product_ids.state',
                 'channel_product_ids.channel_price', 'channel_product_ids.channel_qty')
    def _compute_online_channel_count(self):
        for rec in self:
            active_cps = rec.channel_product_ids.filtered(lambda c: c.state in ('active', 'draft'))
            rec.online_channel_count = len(active_cps)
            rec.online_total_stock = sum(active_cps.mapped('channel_qty'))
            rec.online_revenue_potential = sum(
                (c.channel_price or 0) * (c.channel_qty or 0) for c in active_cps
            )
            rec.is_sold_online = bool(active_cps)
    
    def _inverse_shopee(self):
        self._toggle_channel('shopee', 'is_on_shopee')
    
    def _inverse_lazada(self):
        self._toggle_channel('lazada', 'is_on_lazada')
    
    def _inverse_tiktok(self):
        self._toggle_channel('tiktok', 'is_on_tiktok')
    
    def _toggle_channel(self, channel_code, field_name):
        channel = self.env['channel.config'].search([('code', '=', channel_code)], limit=1)
        if not channel:
            return
        for product in self:
            existing = self.env['channel.product'].search(
                [('product_id', '=', product.id), ('channel_id', '=', channel.id)], limit=1
            )
            is_checked = getattr(product, field_name, False)
            if is_checked and not existing:
                price = product.list_price
                try:
                    ai = self.env['ai.engine'].get_default_engine()
                    result = ai.recommend_price({'name': product.name, 'cost': product.standard_price}, channel_code)
                    price = result.get('selling_price', product.list_price)
                except Exception:
                    pass
                self.env['channel.product'].create({
                    'product_id': product.id,
                    'channel_id': channel.id,
                    'channel_price': price,
                    'channel_qty': int(product.qty_available),
                    'state': 'draft',
                })
            elif not is_checked and existing:
                existing.unlink()
    
    def action_add_all_channels(self):
        channels = self.env['channel.config'].search([('active', '=', True)])
        created = 0
        for channel in channels:
            existing = self.env['channel.product'].search(
                [('product_id', '=', self.id), ('channel_id', '=', channel.id)], limit=1
            )
            if not existing:
                self.env['channel.product'].create({
                    'product_id': self.id,
                    'channel_id': channel.id,
                    'channel_price': self.list_price,
                    'channel_qty': int(self.qty_available),
                    'state': 'draft',
                })
                created += 1
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Added to Channels'),
                'message': _('Created %d channel products' % created),
                'type': 'success'
            }
        }
    
    def action_sync_to_channels(self):
        synced = 0
        errors = 0
        for cp in self.channel_product_ids:
            try:
                cp.sync_to_channel()
                synced += 1
            except Exception:
                errors += 1
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sync Complete'),
                'message': _('Synced: %d, Errors: %d' % (synced, errors)),
                'type': 'success' if errors == 0 else 'warning'
            }
        }