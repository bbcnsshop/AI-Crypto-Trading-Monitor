# -*- coding: utf-8 -*-
"""Test Channel Product Attribute Mapping models."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'multichannel', 'attribute')
class TestChannelProductAttribute(TransactionCase):
    """Test channel.product.attribute model."""

    def setUp(self):
        super().setUp()
        self.ChannelProductAttribute = self.env['channel.product.attribute']
        self.ChannelConfig = self.env['channel.config']

        channel_module = self.env['channel.list.module'].create({
            'name': 'Shopee',
            'code': 'shopee',
            'active': True,
        })
        self.channel = self.ChannelConfig.create({
            'name': 'Test Shopee',
            'code': 'shopee_test',
            'platform': 'shopee',
            'active': True,
            'api_url': 'sandbox',
        })

        # Create Odoo attribute and value
        self.color_attr = self.env['product.attribute'].create({
            'name': 'Color',
            'display_type': 'color',
        })
        self.red_value = self.env['product.attribute.value'].create({
            'name': 'Red',
            'attribute_id': self.color_attr.id,
        })

    def test_create_attribute_mapping(self):
        """Test creating attribute mapping."""
        mapping = self.ChannelProductAttribute.create({
            'channel_id': self.channel.id,
            'odoo_attribute_id': self.color_attr.id,
            'odoo_value_id': self.red_value.id,
            'platform_attr_name': 'Color',
            'platform_attr_value': 'แดง',
            'is_mandatory': True,
        })
        self.assertTrue(mapping.id)
        self.assertEqual(mapping.platform_attr_value, 'แดง')

    def test_onchange_attribute(self):
        """Test onchange sets platform_attr_name from attribute."""
        mapping = self.ChannelProductAttribute.new({
            'channel_id': self.channel.id,
        })
        mapping.odoo_attribute_id = self.color_attr
        mapping._onchange_attribute()
        self.assertEqual(mapping.platform_attr_name, 'Color')

    def test_onchange_value(self):
        """Test onchange sets platform_attr_value from value."""
        mapping = self.ChannelProductAttribute.new({
            'channel_id': self.channel.id,
        })
        mapping.odoo_value_id = self.red_value
        mapping._onchange_value()
        self.assertEqual(mapping.platform_attr_value, 'Red')

    def test_get_platform_variant_data(self):
        """Test getting platform variant data dict."""
        mapping = self.ChannelProductAttribute.create({
            'channel_id': self.channel.id,
            'odoo_attribute_id': self.color_attr.id,
            'odoo_value_id': self.red_value.id,
            'platform_attr_name': 'Color',
            'platform_attr_value': 'Red',
            'is_mandatory': True,
        })
        data = mapping.get_platform_variant_data()
        self.assertEqual(data['attr_name'], 'Color')
        self.assertEqual(data['attr_value'], 'Red')
        self.assertTrue(data['is_mandatory'])

    def test_compute_display_name(self):
        """Test display name computation."""
        mapping = self.ChannelProductAttribute.create({
            'channel_id': self.channel.id,
            'odoo_attribute_id': self.color_attr.id,
            'odoo_value_id': self.red_value.id,
            'platform_attr_name': 'Color',
            'platform_attr_value': 'แดง',
        })
        name = mapping._compute_display_name()
        self.assertIn('Color', name)
        self.assertIn('แดง', name)

    def test_find_mapping(self):
        """Test finding mapping by attributes."""
        mapping = self.ChannelProductAttribute.create({
            'channel_id': self.channel.id,
            'odoo_attribute_id': self.color_attr.id,
            'odoo_value_id': self.red_value.id,
            'platform_attr_name': 'Color',
            'platform_attr_value': 'Red',
        })
        found = self.ChannelProductAttribute.find_mapping(
            self.channel.id, self.color_attr.id, self.red_value.id
        )
        self.assertEqual(found.id, mapping.id)

    def test_action_duplicate_for_channel(self):
        """Test duplicating mapping to another channel."""
        channel2 = self.ChannelConfig.create({
            'name': 'Test Lazada',
            'code': 'lazada_test',
            'platform': 'lazada',
            'active': True,
            'api_url': 'sandbox',
        })

        original = self.ChannelProductAttribute.create({
            'channel_id': self.channel.id,
            'odoo_attribute_id': self.color_attr.id,
            'odoo_value_id': self.red_value.id,
            'platform_attr_name': 'Color',
            'platform_attr_value': 'Red',
            'is_mandatory': True,
        })

        duplicate = original.action_duplicate_for_channel(channel2.id)
        self.assertNotEqual(duplicate.id, original.id)
        self.assertEqual(duplicate.channel_id, channel2)
        self.assertEqual(duplicate.odoo_attribute_id, self.color_attr)


@tagged('post_install', '-at_install', 'multichannel', 'attribute')
class TestChannelProductVariant(TransactionCase):
    """Test channel.product.variant model."""

    def setUp(self):
        super().setUp()
        self.ChannelProductVariant = self.env['channel.product.variant']
        self.ChannelProduct = self.env['channel.product']
        self.ChannelConfig = self.env['channel.config']

        channel_module = self.env['channel.list.module'].create({
            'name': 'TikTok',
            'code': 'tiktok',
            'active': True,
        })
        self.channel = self.ChannelConfig.create({
            'name': 'Test TikTok',
            'code': 'tiktok_test',
            'platform': 'tiktok',
            'active': True,
            'api_url': 'sandbox',
        })

        # Create product with variants
        self.product_template = self.env['product.template'].create({
            'name': 'Test T-Shirt',
            'type': 'product',
        })

        self.color_attr = self.env['product.attribute'].create({
            'name': 'Color',
        })
        self.size_attr = self.env['product.attribute'].create({
            'name': 'Size',
        })

        self.product_template.attribute_line_ids = [(0, 0, {
            'attribute_id': self.color_attr.id,
        })]

        # Get variants
        self.variant = self.product_template.product_variant_ids[0]

        # Create channel product
        self.channel_product = self.ChannelProduct.create({
            'product_id': self.variant.id,
            'channel_id': self.channel.id,
        })

    def test_create_variant_mapping(self):
        """Test creating variant mapping."""
        variant_mapping = self.ChannelProductVariant.create({
            'channel_product_id': self.channel_product.id,
            'product_variant_id': self.variant.id,
            'channel_price': 299.0,
            'channel_qty': 100,
        })
        self.assertTrue(variant_mapping.id)
        self.assertEqual(variant_mapping.channel_price, 299.0)

    def test_variant_attr_display(self):
        """Test attribute display string."""
        variant_mapping = self.ChannelProductVariant.create({
            'channel_product_id': self.channel_product.id,
            'product_variant_id': self.variant.id,
        })
        display = variant_mapping._variant_attr_display()
        # Should return attribute string
        self.assertIsInstance(display, str)

    def test_name_get(self):
        """Test name_get returns proper format."""
        variant_mapping = self.ChannelProductVariant.create({
            'channel_product_id': self.channel_product.id,
            'product_variant_id': self.variant.id,
        })
        name = variant_mapping.name_get()
        self.assertTrue(len(name) > 0)
        self.assertEqual(name[0][0], variant_mapping.id)

    def test_variant_sync_status(self):
        """Test sync status field."""
        variant_mapping = self.ChannelProductVariant.create({
            'channel_product_id': self.channel_product.id,
            'product_variant_id': self.variant.id,
            'sync_status': 'pending',
        })
        self.assertEqual(variant_mapping.sync_status, 'pending')

        variant_mapping.sync_status = 'synced'
        self.assertEqual(variant_mapping.sync_status, 'synced')

    def test_variant_platform_fields(self):
        """Test platform-specific fields."""
        variant_mapping = self.ChannelProductVariant.create({
            'channel_product_id': self.channel_product.id,
            'product_variant_id': self.variant.id,
            'platform_variant_id': 'TT-12345',
            'platform_variant_url': 'https://tiktok.com/item/12345',
            'channel_weight': 0.5,
        })
        self.assertEqual(variant_mapping.platform_variant_id, 'TT-12345')
        self.assertEqual(variant_mapping.channel_weight, 0.5)
