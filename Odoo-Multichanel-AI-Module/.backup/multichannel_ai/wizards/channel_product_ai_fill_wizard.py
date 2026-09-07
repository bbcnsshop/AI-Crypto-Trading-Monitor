# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ChannelProductAIFillWizard(models.TransientModel):
    """Wizard for AI Auto-Fill Channel Product Fields"""
    _name = 'channel.product.ai.fill.wizard'
    _description = 'AI Auto-Fill Channel Product Fields'

    channel_ids = fields.Many2many(
        'channel.config',
        string='Channels',
        help='เลือก Channel ที่ต้องการให้ AI ช่วยเติมข้อมูล'
    )
    fill_barcode = fields.Boolean(
        string='Fill Barcode',
        default=True,
        help='เติม Barcode อัตโนมัติ'
    )
    fill_condition = fields.Boolean(
        string='Fill Condition',
        default=True,
        help='เติม Condition (new/used/refurbished) อัตโนมัติ'
    )
    fill_brand = fields.Boolean(
        string='Fill Brand',
        default=True,
        help='เติม Brand อัตโนมัติ'
    )
    limit = fields.Integer(
        string='Limit Records',
        default=100,
        help='จำนวนสินค้าสูงสุดที่จะประมวลผล (0 = ไม่จำกัด)'
    )
    only_incomplete = fields.Boolean(
        string='Only Incomplete Products',
        default=True,
        help='เฉพาะสินค้าที่ขาดข้อมูล'
    )

    # Results
    processed_count = fields.Integer(string='Processed', readonly=True)
    filled_count = fields.Integer(string='Filled', readonly=True)
    error_count = fields.Integer(string='Errors', readonly=True)
    results_log = fields.Text(string='Results Log', readonly=True)

    @api.model
    def default_get(self, fields_list):
        """Pre-fill with current record's channel if available."""
        res = super().default_get(fields_list)
        active_ids = self._context.get('active_ids', [])
        if active_ids:
            cp = self.env['channel.product'].browse(active_ids[0])
            if cp.channel_id:
                res['channel_ids'] = [(4, cp.channel_id.id)]
        return res

    def action_preview(self):
        """Preview how many products will be affected."""
        products = self._get_products_to_fill()
        return {
            'type': 'ir.actions.act_window.message',
            'title': _('Preview'),
            'message': _(
                'จะมี %d สินค้าที่ได้รับผลกระทบจากการ Auto-Fill'
            ) % len(products),
            'close_button_title': _('OK'),
        }

    def _get_products_to_fill(self):
        """Get products that match the criteria."""
        domain = [('state', 'in', ('draft', 'active'))]

        # Filter by selected channels
        if self.channel_ids:
            domain.append(('channel_id', 'in', self.channel_ids.ids))

        # Filter only incomplete products
        if self.only_incomplete:
            domain.append('|')
            if self.fill_barcode:
                domain.append(('barcode', '=', False))
            if self.fill_condition:
                domain.append(('condition', '=', 'new'))
            if self.fill_brand:
                domain.append(('channel_brand', '=', False))

        # Search with limit
        limit = self.limit if self.limit > 0 else None
        return self.env['channel.product'].search(domain, limit=limit)

    def action_fill(self):
        """Execute AI Auto-Fill for selected products."""
        self.ensure_one()

        products = self._get_products_to_fill()
        processed = 0
        filled = 0
        errors = 0
        logs = []

        for cp in products:
            processed += 1
            try:
                # Check which fields will be filled
                will_fill = []
                if self.fill_barcode and not cp.barcode:
                    will_fill.append('barcode')
                if self.fill_condition and (not cp.condition or cp.condition == 'new'):
                    will_fill.append('condition')
                if self.fill_brand and not cp.channel_brand:
                    will_fill.append('brand')

                if not will_fill:
                    continue

                # Apply fills based on settings
                if self.fill_barcode and not cp.barcode:
                    cp.barcode = cp.ai_suggest_barcode()
                if self.fill_condition and (not cp.condition or cp.condition == 'new'):
                    cp.condition = cp.ai_suggest_condition()
                if self.fill_brand and not cp.channel_brand:
                    brand = cp.ai_suggest_brand()
                    if brand:
                        cp.channel_brand = brand

                # Update tracking
                cp.write({
                    'ai_auto_fill_date': fields.Datetime.now(),
                    'ai_auto_fill_status': 'filled',
                })

                filled += 1
                logs.append(
                    '[%s] %s - Filled: %s' % (
                        cp.channel_id.code or 'N/A',
                        cp.name,
                        ', '.join(will_fill)
                    )
                )

            except Exception as e:
                errors += 1
                logs.append(
                    '[ERROR] %s - %s' % (cp.name, str(e))
                )

        # Update wizard results
        self.write({
            'processed_count': processed,
            'filled_count': filled,
            'error_count': errors,
            'results_log': '\n'.join(logs) if logs else 'No products matched criteria.',
        })

        return {
            'name': _('AI Auto-Fill Results'),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self._context,
        }

    def action_view_products(self):
        """View products that will be affected."""
        products = self._get_products_to_fill()
        return {
            'name': _('Products to Fill'),
            'type': 'ir.actions.act_window',
            'res_model': 'channel.product',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', products.ids)],
            'target': 'current',
        }