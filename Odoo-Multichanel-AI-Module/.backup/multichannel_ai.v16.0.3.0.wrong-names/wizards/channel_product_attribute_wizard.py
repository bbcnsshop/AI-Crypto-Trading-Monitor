# -*- coding: utf-8 -*-
"""
Channel Product Attribute Wizard
Bulk auto-generate attribute mappings based on Odoo attribute values.
(Extracted from models/channel_product_attribute.py - Phase 11.1)
"""
from odoo import _, fields, models


class ChannelProductAttributeWizard(models.TransientModel):
    """Bulk auto-generate attribute mappings based on Odoo attribute values."""
    _name = 'channel.product.attribute.wizard'
    _description = 'Auto-generate Attribute Mappings'

    channel_product_id = fields.Many2one(
        'channel.product', string='Channel Product', required=True
    )
    use_default_name = fields.Boolean(
        string='Use Odoo Names', default=True,
        help='If checked, platform_attr_name = odoo_attribute.name'
    )
    override_platform_name = fields.Char(
        string='Override Attribute Name',
        help='If set, all platform_attr_name will use this value'
    )

    def action_generate(self):
        self.ensure_one()
        cp = self.channel_product_id
        product = cp.product_id
        AttributeMapping = self.env['channel.product.attribute']

        existing = AttributeMapping.search([('channel_product_id', '=', cp.id)])
        existing.unlink()

        created = 0
        seen = set()
        for line in product.product_template_attribute_value_ids:
            attr = line.attribute_id
            value = line.product_attribute_value_id
            key = (attr.id, value.id)
            if key in seen:
                continue
            seen.add(key)

            vals = {
                'channel_id': cp.channel_id.id,
                'channel_product_id': cp.id,
                'odoo_attribute_id': attr.id,
                'odoo_value_id': value.id,
                'platform_attr_name': self.override_platform_name if self.override_platform_name else attr.name,
                'platform_attr_value': value.name,
                'is_mandatory': True,
            }
            AttributeMapping.create(vals)
            created += 1
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Attribute Mappings Created'),
                'message': _('Created %d attribute mappings') % created,
                'type': 'success',
            }
        }
