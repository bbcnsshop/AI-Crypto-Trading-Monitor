# -*- coding: utf-8 -*-
from odoo import models, api, fields, _


class CountsMixin(models.AbstractModel):
    """Mixin: computed counts + action views."""
    _name = 'channel.counts'
    _description = 'Channel Counts'

    product_count = fields.Integer(string='Products', compute='_compute_counts')
    order_count = fields.Integer(string='Orders', compute='_compute_counts')

    @api.depends()
    def _compute_counts(self):
        for rec in self:
            rec.product_count = self.env['channel.product'].search_count(
                [('channel_id', '=', rec.id)])
            rec.order_count = self.env['channel.order'].search_count(
                [('channel_id', '=', rec.id)])

    def action_view_products(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Products - %s' % self.name),
            'res_model': 'channel.product',
            'view_mode': 'tree,form',
            'domain': [('channel_id', '=', self.id)],
        }

    def action_view_orders(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Orders - %s' % self.name),
            'res_model': 'channel.order',
            'view_mode': 'tree,form',
            'domain': [('channel_id', '=', self.id)],
        }
