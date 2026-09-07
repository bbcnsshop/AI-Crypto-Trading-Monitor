# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class AddToChannelBulkWizard(models.TransientModel):
    _name = 'add.to.channel.bulk.wizard'
    _description = 'Add Products to Channel'
    
    channel_id = fields.Many2one('channel.config', string='Channel', required=True, domain=[('active', '=', True)])
    selection_type = fields.Selection([('selected', 'Selected'), ('category', 'Category'), ('all', 'All Products')], string='Selection Type', default='selected', required=True)
    category_id = fields.Many2one('product.category', string='Product Category')
    only_with_stock = fields.Boolean(string='Only with Stock', default=True)
    use_ai_price = fields.Boolean(string='Use AI Price', default=True)
    target_margin = fields.Float(string='Target Margin (%)', default=30.0)
    override_all_price = fields.Float(string='Fixed Price (optional)')
    channel_qty_mode = fields.Selection([('actual', 'Use Actual Stock'), ('unlimited', 'Unlimited (999)'), ('custom', 'Custom')], string='Stock Mode', default='actual')
    custom_qty = fields.Integer(string='Custom Qty', default=10)
    
    product_ids = fields.Many2many('product.product', string='Products', compute='_compute_products')
    product_count = fields.Integer(string='Count', compute='_compute_products')
    
    @api.depends('selection_type', 'category_id', 'only_with_stock')
    def _compute_products(self):
        for rec in self:
            domain = [('type', '!=', 'service')]
            if rec.selection_type == 'category' and rec.category_id:
                domain.append(('categ_id', '=', rec.category_id.id))
            if rec.only_with_stock:
                domain.append(('qty_available', '>', 0))
            products = self.env['product.product'].search(domain)
            if rec.selection_type == 'selected':
                active_ids = rec.env.context.get('active_ids', [])
                if active_ids:
                    products = products.filtered(lambda p: p.id in active_ids)
            rec.product_ids = products
            rec.product_count = len(products)
    
    def action_preview(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Preview - %d Products' % self.product_count),
            'res_model': 'product.product',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.product_ids.ids)],
            'target': 'new',
        }
    
    def action_add_to_channel(self):
        self.ensure_one()
        
        # Check AI availability with fallback
        try:
            ai_engine = self.env['ai.engine'].get_default_engine()
            ai_available = True
        except Exception:
            ai_engine = None
            ai_available = False
            _logger.info('AI engine not available for bulk add, using default prices')
        
        created = 0
        updated = 0
        for product in self.product_ids:
            if self.override_all_price:
                price = self.override_all_price
            elif self.use_ai_price and ai_available:
                try:
                    result = ai_engine.recommend_price(
                        {'name': product.name, 'cost': product.standard_price or 0},
                        self.channel_id.code
                    )
                    price = result.get('selling_price', product.list_price or 0)
                except Exception as e:
                    _logger.warning('AI price failed for %s: %s, using default', product.name, str(e))
                    price = product.list_price or 0
            else:
                price = product.list_price or 0
            if self.channel_qty_mode == 'actual':
                qty = int(product.qty_available or 0)
            elif self.channel_qty_mode == 'unlimited':
                qty = 999
            else:
                qty = self.custom_qty
            existing = self.env['channel.product'].search([('product_id', '=', product.id), ('channel_id', '=', self.channel_id.id)], limit=1)
            if existing:
                existing.write({'channel_price': price, 'channel_qty': qty})
                updated += 1
            else:
                self.env['channel.product'].create({
                    'name': product.name,
                    'product_id': product.id,
                    'channel_id': self.channel_id.id,
                    'channel_price': price,
                    'channel_qty': qty,
                    'state': 'draft',
                })
                created += 1
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': _('Add Complete'), 'message': _('Created: %d, Updated: %d' % (created, updated)), 'type': 'success'}
        }