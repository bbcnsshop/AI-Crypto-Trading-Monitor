# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    channel_product_ids = fields.One2many(
        'channel.product', compute='_compute_channel_product_ids', string='Channel Products'
    )
    channel_product_count = fields.Integer(
        string='Channel Count', compute='_compute_channel_product_ids'
    )
    is_on_shopee = fields.Boolean(
        string='Shopee', compute='_compute_channel_status'
    )
    is_on_lazada = fields.Boolean(
        string='Lazada', compute='_compute_channel_status'
    )
    is_on_tiktok = fields.Boolean(
        string='TikTok', compute='_compute_channel_status'
    )
    is_sold_online = fields.Boolean(
        string='Sold Online', compute='_compute_channel_status'
    )
    online_total_stock = fields.Integer(
        string='Total Online Stock', compute='_compute_channel_status'
    )
    online_revenue_potential = fields.Float(
        string='Online Revenue Potential', compute='_compute_channel_status'
    )

    @api.depends('product_variant_ids.channel_product_ids',
                 'product_variant_ids.channel_product_ids.channel_id',
                 'product_variant_ids.channel_product_ids.state',
                 'product_variant_ids.channel_product_ids.channel_price',
                 'product_variant_ids.channel_product_ids.channel_qty')
    def _compute_channel_product_ids(self):
        for tmpl in self:
            cps = self.env['channel.product'].search([
                ('product_id.product_tmpl_id', '=', tmpl.id)
            ])
            tmpl.channel_product_ids = cps
            active_cps = cps.filtered(lambda c: c.state in ('active', 'draft'))
            tmpl.channel_product_count = len(active_cps)

    @api.depends('channel_product_ids', 'channel_product_ids.channel_id',
                 'channel_product_ids.state', 'channel_product_ids.channel_price',
                 'channel_product_ids.channel_qty')
    def _compute_channel_status(self):
        for tmpl in self:
            active_cps = tmpl.channel_product_ids.filtered(
                lambda c: c.state in ('active', 'draft')
            )
            channels = active_cps.mapped('channel_id')
            tmpl.is_on_shopee = bool(channels.filtered(lambda c: c.code == 'shopee'))
            tmpl.is_on_lazada = bool(channels.filtered(lambda c: c.code == 'lazada'))
            tmpl.is_on_tiktok = bool(channels.filtered(lambda c: c.code == 'tiktok'))
            tmpl.is_sold_online = bool(active_cps)
            tmpl.online_total_stock = sum(active_cps.mapped('channel_qty'))
            tmpl.online_revenue_potential = sum(
                (c.channel_price or 0) * (c.channel_qty or 0) for c in active_cps
            )

    def _get_first_variant(self):
        self.ensure_one()
        return self.product_variant_ids[:1]

    def action_open_add_to_channel_wizard(self):
        self.ensure_one()
        variant = self._get_first_variant()
        if not variant:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Variant'),
                    'message': _('This product has no variant.'),
                    'type': 'warning',
                },
            }
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add to Channel'),
            'res_model': 'add.to.channel.bulk.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_selection_type': 'selected',
                'active_ids': [variant.id],
            },
        }

    def action_view_channel_products(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Channel Products'),
            'res_model': 'channel.product',
            'view_mode': 'tree,form',
            'domain': [('product_id.product_tmpl_id', '=', self.id)],
            'context': {'default_product_id': self._get_first_variant().id if self._get_first_variant() else False},
        }
