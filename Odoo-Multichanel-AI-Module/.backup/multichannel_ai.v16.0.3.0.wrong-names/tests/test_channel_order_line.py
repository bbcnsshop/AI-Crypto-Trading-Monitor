# -*- coding: utf-8 -*-
"""Test Channel Order Line model."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'multichannel', 'order')
class TestChannelOrderLineFields(TransactionCase):
    """Test channel.order.line fields."""

    def setUp(self):
        super().setUp()
        self.ChannelOrderLine = self.env['channel.order.line']
        self.ChannelOrder = self.env['channel.order']
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

        self.channel_order = self.ChannelOrder.create({
            'channel_order_id': 'SO-001',
            'channel_id': self.channel.id,
            'customer_name': 'Test Customer',
            'state': 'pending',
        })

        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'standard_price': 50.0,
            'list_price': 100.0,
        })

    def test_line_creation(self):
        """Test basic line creation."""
        line = self.ChannelOrderLine.create({
            'order_id': self.channel_order.id,
            'name': 'Test Product Line',
            'quantity': 2,
            'unit_price': 100.0,
        })
        self.assertTrue(line.id)
        self.assertEqual(line.quantity, 2)
        self.assertEqual(line.unit_price, 100.0)

    def test_line_fields(self):
        """Test additional line fields exist."""
        line = self.ChannelOrderLine.create({
            'order_id': self.channel_order.id,
            'name': 'Test',
            'discount_amount': 10.0,
            'variation_name': 'Size L',
            'sku': 'SKU-001',
            'image_url': 'https://example.com/img.jpg',
        })
        self.assertEqual(line.discount_amount, 10.0)
        self.assertEqual(line.variation_name, 'Size L')
        self.assertEqual(line.sku, 'SKU-001')
        self.assertEqual(line.image_url, 'https://example.com/img.jpg')

    def test_compute_subtotal(self):
        """Test subtotal calculation."""
        line = self.ChannelOrderLine.create({
            'order_id': self.channel_order.id,
            'name': 'Test',
            'quantity': 3,
            'unit_price': 100.0,
        })
        self.assertEqual(line.subtotal, 300.0)
        self.assertEqual(line.tax_amount, 21.0)  # 7% VAT
        self.assertEqual(line.total_amount, 321.0)


@tagged('post_install', '-at_install', 'multichannel', 'order')
class TestChannelOrderLineCompute(TransactionCase):
    """Test computed fields on channel.order.line."""

    def setUp(self):
        super().setUp()
        self.ChannelOrderLine = self.env['channel.order.line']
        self.ChannelOrder = self.env['channel.order']
        self.ChannelConfig = self.env['channel.config']

        channel_module = self.env['channel.list.module'].create({
            'name': 'Lazada',
            'code': 'lazada',
            'active': True,
        })
        self.channel = self.ChannelConfig.create({
            'name': 'Test Lazada',
            'code': 'lazada_test',
            'platform': 'lazada',
            'active': True,
            'api_url': 'sandbox',
        })

        self.channel_order = self.ChannelOrder.create({
            'channel_order_id': 'LZ-001',
            'channel_id': self.channel.id,
            'state': 'pending',
        })

        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'standard_price': 60.0,
            'list_price': 120.0,
        })

    def test_compute_margin(self):
        """Test margin calculation."""
        line = self.ChannelOrderLine.create({
            'order_id': self.channel_order.id,
            'product_id': self.product.id,
            'name': 'Test',
            'quantity': 2,
            'unit_price': 120.0,
        })
        # subtotal = 240, cost = 60 * 2 = 120
        # margin = (240 - 120) / 240 * 100 = 50%
        self.assertEqual(line.margin, 50.0)

    def test_compute_margin_no_product(self):
        """Test margin is 0 when no product."""
        line = self.ChannelOrderLine.create({
            'order_id': self.channel_order.id,
            'name': 'Test',
            'quantity': 2,
            'unit_price': 120.0,
        })
        self.assertEqual(line.margin, 0.0)

    def test_compute_has_product(self):
        """Test has_product computed field."""
        line_with = self.ChannelOrderLine.create({
            'order_id': self.channel_order.id,
            'product_id': self.product.id,
            'name': 'Test',
        })
        self.assertTrue(line_with.has_product)

        line_without = self.ChannelOrderLine.create({
            'order_id': self.channel_order.id,
            'name': 'Test No Product',
        })
        self.assertFalse(line_without.has_product)


@tagged('post_install', '-at_install', 'multichannel', 'order')
class TestChannelOrderLineActions(TransactionCase):
    """Test action methods on channel.order.line."""

    def setUp(self):
        super().setUp()
        self.ChannelOrderLine = self.env['channel.order.line']
        self.ChannelOrder = self.env['channel.order']
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

        self.channel_order = self.ChannelOrder.create({
            'channel_order_id': 'TT-001',
            'channel_id': self.channel.id,
            'state': 'pending',
        })

        self.product = self.env['product.product'].create({
            'name': 'SKU Test Product',
            'default_code': 'SKU-12345',
        })

    def test_action_link_odoo_product_already_linked(self):
        """Test linking returns info when already linked."""
        line = self.ChannelOrderLine.create({
            'order_id': self.channel_order.id,
            'product_id': self.product.id,
            'name': 'Test',
        })
        result = line.action_link_odoo_product()
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['params']['type'], 'info')

    def test_action_link_odoo_product_by_sku(self):
        """Test linking product by SKU."""
        line = self.ChannelOrderLine.create({
            'order_id': self.channel_order.id,
            'name': 'Test',
            'sku': 'SKU-12345',
        })
        result = line.action_link_odoo_product()
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['params']['type'], 'success')
        self.assertEqual(line.product_id, self.product)

    def test_action_link_odoo_product_not_found(self):
        """Test linking when product not found raises error."""
        from odoo.exceptions import UserError
        line = self.ChannelOrderLine.create({
            'order_id': self.channel_order.id,
            'name': 'Unknown Product XYZ',
            'sku': 'NONEXISTENT',
        })
        with self.assertRaises(UserError):
            line.action_link_odoo_product()


@tagged('post_install', '-at_install', 'multichannel', 'order')
class TestChannelOrderLinePrepare(TransactionCase):
    """Test helper methods on channel.order.line."""

    def setUp(self):
        super().setUp()
        self.ChannelOrderLine = self.env['channel.order.line']
        self.ChannelOrder = self.env['channel.order']
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

        self.channel_order = self.ChannelOrder.create({
            'channel_order_id': 'SO-LINE-001',
            'channel_id': self.channel.id,
            'state': 'pending',
        })

        self.product = self.env['product.product'].create({
            'name': 'Test Product',
        })

    def test_prepare_sale_order_line_vals(self):
        """Test preparing vals for sale order line."""
        line = self.ChannelOrderLine.create({
            'order_id': self.channel_order.id,
            'product_id': self.product.id,
            'name': 'Test Line',
            'quantity': 3,
            'unit_price': 150.0,
        })
        vals = line._prepare_sale_order_line_vals()
        self.assertEqual(vals['product_id'], self.product.id)
        self.assertEqual(vals['name'], 'Test Line')
        self.assertEqual(vals['product_uom_qty'], 3)
        self.assertEqual(vals['price_unit'], 150.0)

    def test_compute_discount_pct(self):
        """Test discount percentage calculation."""
        line = self.ChannelOrderLine.create({
            'order_id': self.channel_order.id,
            'name': 'Test',
            'quantity': 1,
            'unit_price': 100.0,
            'discount_amount': 10.0,
        })
        pct = line._compute_discount_pct()
        self.assertEqual(pct, 10.0)

    def test_compute_discount_pct_no_discount(self):
        """Test discount percentage when no discount."""
        line = self.ChannelOrderLine.create({
            'order_id': self.channel_order.id,
            'name': 'Test',
            'quantity': 1,
            'unit_price': 100.0,
            'discount_amount': 0.0,
        })
        pct = line._compute_discount_pct()
        self.assertEqual(pct, 0.0)
