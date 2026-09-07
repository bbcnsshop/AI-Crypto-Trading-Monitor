# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ChannelProductFieldMapping(models.Model):
    _name = 'channel.product.field.mapping'
    _description = 'Field Mapping: Odoo to Platform'
    _order = 'channel_id, sequence, id'
    _sql_constraints = [
        ('mapping_unique', 'unique(channel_id, odoo_model, odoo_field)',
         'This field mapping already exists for this channel!')
    ]

    active = fields.Boolean(string='Active', default=True)
    channel_id = fields.Many2one(
        'channel.config', string='Channel', required=True, index=True, ondelete='cascade'
    )
    sequence = fields.Integer(string='Priority', default=10)
    odoo_model = fields.Selection([
        ('product.product', 'Product (product.product)'),
        ('product.template', 'Product Template'),
    ], string='Odoo Model', default='product.product', required=True)
    odoo_field = fields.Char(string='Odoo Field', required=True,
                             help='Field name on product.product or product.template, e.g. name, list_price, barcode')
    platform_field = fields.Char(string='Platform Field Name', required=True,
                                 help='Field name used in platform API, e.g. title, price, weight')
    transform_type = fields.Selection([
        ('direct', 'Direct (no change)'),
        ('multiply', 'Multiply by value'),
        ('divide', 'Divide by value'),
        ('lookup', 'Lookup table (old:new pairs)'),
        ('custom', 'Custom Python code'),
        ('ignore', 'Ignore (use default only)'),
    ], string='Transform Type', default='direct', required=True)
    transform_value = fields.Char(string='Transform Value',
                                  help='e.g. "0.001" to multiply kg to tonne, or "A:B,C:D" for lookup')
    default_value = fields.Char(string='Default Value',
                               help='Used when Odoo field is empty or None')
    is_required = fields.Boolean(string='Required for Sync', default=False)
    validation_rule = fields.Char(string='Validation Rule',
                                  help='e.g. "min:0.01" or "regex:^[0-9]+$"')
    description = fields.Char(string='Description')
    missing_count = fields.Integer(
        string='Products Missing This Field',
        compute='_compute_missing_count', store=False
    )

    def _compute_missing_count(self):
        for rec in self:
            if not (rec.is_required and rec.channel_id and rec.odoo_model and rec.odoo_field):
                rec.missing_count = 0
                continue
            cp_domain = [('channel_id', '=', rec.channel_id.id), ('state', '!=', 'inactive')]
            channel_products = self.env['channel.product'].search(cp_domain)
            count = 0
            for cp in channel_products:
                val = self._get_raw_value(cp)
                if val is False or val == '' or val is None:
                    count += 1
            rec.missing_count = count

    def _get_raw_value(self, channel_product):
        product = channel_product.product_id
        if self.odoo_field == 'channel_weight':
            return channel_product.channel_weight
        elif self.odoo_field == 'channel_description':
            return channel_product.channel_description
        elif self.odoo_field == 'channel_video_url':
            return channel_product.channel_video_url
        elif self.odoo_field == 'channel_brand':
            return channel_product.channel_brand
        elif self.odoo_field == 'barcode':
            return channel_product.barcode
        elif self.odoo_field == 'condition':
            return channel_product.condition
        elif self.odoo_field == 'channel_length':
            return channel_product.channel_length
        elif self.odoo_field == 'channel_width':
            return channel_product.channel_width
        elif self.odoo_field == 'channel_height':
            return channel_product.channel_height
        elif hasattr(product, self.odoo_field):
            val = getattr(product, self.odoo_field, False)
            if isinstance(val, models.Model):
                return val.ids[:1] if val.ids else False
            return val
        return False

    def get_platform_value(self, channel_product):
        self.ensure_one()
        raw = self._get_raw_value(channel_product)
        if raw is False or raw is None or raw == '':
            return self.default_value or False

        if self.transform_type == 'direct':
            return raw
        elif self.transform_type == 'multiply':
            try:
                return float(raw) * float(self.transform_value or 1)
            except (ValueError, TypeError):
                return raw
        elif self.transform_type == 'divide':
            try:
                divisor = float(self.transform_value or 1)
                return float(raw) / divisor if divisor else raw
            except (ValueError, TypeError):
                return raw
        elif self.transform_type == 'lookup':
            if not self.transform_value:
                return raw
            pairs = [p.strip() for p in self.transform_value.split(',')]
            for pair in pairs:
                if ':' in pair:
                    old, new = pair.split(':', 1)
                    if str(raw).strip() == old.strip():
                        return new.strip()
            return raw
        elif self.transform_type == 'custom':
            return raw
        else:
            return self.default_value or False


class ChannelProductCompleteness(models.Model):
    _name = 'channel.product.completeness'
    _description = 'Channel Product Data Completeness'
    _sql_constraints = [
        ('cp_channel_unique', 'unique(channel_product_id, channel_id)',
         'Only one completeness record per product-channel!')
    ]

    channel_product_id = fields.Many2one(
        'channel.product', required=True, ondelete='cascade', index=True
    )
    channel_id = fields.Many2one('channel.config', string='Channel', index=True)
    total_required = fields.Integer(string='Total Required', compute='_compute_counts', store=True)
    total_filled = fields.Integer(string='Total Filled', compute='_compute_counts', store=True)
    completeness_pct = fields.Float(string='% Complete', digits=(5, 1),
                                     compute='_compute_counts', store=True)
    missing_field_names = fields.Text(string='Missing Fields')
    status = fields.Selection([
        ('ready', 'Ready to Sync'),
        ('incomplete', 'Incomplete'),
        ('error', 'Has Errors'),
    ], string='Status', default='incomplete', compute='_compute_counts', store=True)

    @api.depends('channel_product_id', 'channel_id')
    def _compute_counts(self):
        for rec in self:
            if not (rec.channel_product_id and rec.channel_id):
                rec.total_required = 0
                rec.total_filled = 0
                rec.completeness_pct = 100.0
                rec.missing_field_names = ''
                rec.status = 'ready'
                continue

            mappings = self.env['channel.product.field.mapping'].search([
                ('channel_id', '=', rec.channel_id.id),
                ('active', '=', True),
                ('is_required', '=', True),
            ])
            total = len(mappings)
            filled = 0
            missing = []
            cp = rec.channel_product_id

            for mapping in mappings:
                val = mapping.get_platform_value(cp)
                if val is not False and val != '' and val is not None:
                    filled += 1
                else:
                    missing.append(mapping.description or mapping.platform_field)

            pct = (filled / total * 100) if total > 0 else 100.0
            rec.total_required = total
            rec.total_filled = filled
            rec.completeness_pct = round(pct, 1)
            rec.missing_field_names = ', '.join(missing)
            if total == 0:
                rec.status = 'ready'
            elif pct >= 100:
                rec.status = 'ready'
            else:
                rec.status = 'incomplete'

    @api.model
    def upsert(self, channel_product_id, channel_id):
        existing = self.search([
            ('channel_product_id', '=', channel_product_id),
            ('channel_id', '=', channel_id)
        ], limit=1)
        if existing:
            existing._compute_counts()
            return existing
        record = self.create({
            'channel_product_id': channel_product_id,
            'channel_id': channel_id,
        })
        return record
