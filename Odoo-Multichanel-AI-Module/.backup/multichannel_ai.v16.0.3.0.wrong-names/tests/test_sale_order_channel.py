# -*- coding: utf-8 -*-
"""Test Sale Order Channel Integration.

Tests for sale.order.channel inheritance covering:
- Channel fields
- Computed fields
- Action methods
- Sync methods
- Channel totals calculation
- Report data
- Sale Order Line channel info
"""
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError


@tagged('post_install', '-at_install', 'multichannel', 'sale')
class TestSaleOrderChannelFields(TransactionCase):
    """Test channel fields on sale.order."""

    def setUp(self):
        super().setUp()
        self.SaleOrder = self.env['sale.order']
        self.ChannelConfig = self.env['channel.config']

        # Create test channel
        channel_module = self.env['channel.list.module'].create({
            'name': 'Shopee',
            'code': 'shopee',
            'active': True,
        })
        self.channel = self.ChannelConfig.create({
            'name': 'Test Shopee Channel',
            'code': 'shopee',
            'channel_module_id': channel_module.id,
            'active': True,
            'api_url': 'sandbox',
        })

        # Create test partner
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'test@example.com',
        })

    def test_create_sale_order_with_channel(self):
        """Test creating sale order with channel."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'channel_id': self.channel.id,
        })
        self.assertEqual(order.channel_id, self.channel)
        self.assertTrue(order.is_from_channel)

    def test_sale_order_without_channel(self):
        """Test sale order without channel has is_from_channel=False."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
        })
        self.assertFalse(order.channel_id)
        self.assertFalse(order.is_from_channel)

    def test_channel_fields_default_values(self):
        """Test default values of channel fields."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
        })
        self.assertEqual(order.channel_shipping_fee, 0.0)
        self.assertEqual(order.channel_discount, 0.0)
        self.assertFalse(order.channel_order_id)
        self.assertFalse(order.channel_order_code)


@tagged('post_install', '-at_install', 'multichannel', 'sale')
class TestSaleOrderChannelOnchange(TransactionCase):
    """Test onchange methods for sale.order.channel."""

    def setUp(self):
        super().setUp()
        self.SaleOrder = self.env['sale.order']
        self.ChannelConfig = self.env['channel.config']

        # Create warehouse and pricelist for channel
        self.warehouse = self.env['stock.warehouse'].create({
            'name': 'Test WH',
            'code': 'TWH',
        })

        self.pricelist = self.env['product.pricelist'].create({
            'name': 'Test Pricelist',
            'currency_id': self.env.ref('base.THB').id,
        })

        # Create test channel
        channel_module = self.env['channel.list.module'].create({
            'name': 'Lazada',
            'code': 'lazada',
            'active': True,
        })
        self.channel = self.ChannelConfig.create({
            'name': 'Test Lazada',
            'code': 'lazada',
            'channel_module_id': channel_module.id,
            'active': True,
            'api_url': 'sandbox',
            'default_warehouse_id': self.warehouse.id,
            'default_pricelist_id': self.pricelist.id,
        })

        self.partner = self.env['res.partner'].create({'name': 'Test'})

    def test_onchange_channel_sets_warehouse(self):
        """Test that changing channel sets the default warehouse."""
        order = self.SaleOrder.new({'partner_id': self.partner.id})
        order.channel_id = self.channel
        order._onchange_channel_id()
        self.assertEqual(order.warehouse_id, self.warehouse)

    def test_onchange_channel_sets_pricelist(self):
        """Test that changing channel sets the default pricelist."""
        order = self.SaleOrder.new({'partner_id': self.partner.id})
        order.channel_id = self.channel
        order._onchange_channel_id()
        self.assertEqual(order.pricelist_id, self.pricelist)

    def test_onchange_channel_order_id_syncs_data(self):
        """Test onchange channel_order_id syncs data from channel order."""
        # Create channel order
        channel_order = self.env['channel.order'].create({
            'channel_order_id': 'TEST-001',
            'channel_id': self.channel.id,
            'customer_name': 'Test Buyer',
            'shipping_cost': 50.0,
            'platform_fee': 10.0,
            'state': 'pending',
        })

        order = self.SaleOrder.new({'partner_id': self.partner.id})
        order.channel_order_id = channel_order
        order._onchange_channel_order_id()

        self.assertEqual(order.channel_order_code, 'TEST-001')
        self.assertEqual(order.channel_shipping_fee, 50.0)
        self.assertEqual(order.channel_discount, 10.0)
        self.assertEqual(order.channel_id, self.channel)


@tagged('post_install', '-at_install', 'multichannel', 'sale')
class TestSaleOrderChannelActions(TransactionCase):
    """Test action methods for sale.order.channel."""

    def setUp(self):
        super().setUp()
        self.SaleOrder = self.env['sale.order']
        self.ChannelConfig = self.env['channel.config']

        channel_module = self.env['channel.list.module'].create({
            'name': 'TikTok',
            'code': 'tiktok',
            'active': True,
        })
        self.channel = self.ChannelConfig.create({
            'name': 'Test TikTok',
            'code': 'tiktok',
            'channel_module_id': channel_module.id,
            'active': True,
            'api_url': 'sandbox',
        })

        self.partner = self.env['res.partner'].create({'name': 'Test Customer'})

    def test_action_view_channel_order_no_link(self):
        """Test action_view_channel_order raises when no linked order."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
        })
        with self.assertRaises(UserError):
            order.action_view_channel_order()

    def test_action_view_channel_order_with_link(self):
        """Test action_view_channel_order returns action when linked."""
        channel_order = self.env['channel.order'].create({
            'channel_order_id': 'TT-001',
            'channel_id': self.channel.id,
            'customer_name': 'Test',
            'state': 'pending',
        })

        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'channel_order_id': channel_order.id,
        })

        result = order.action_view_channel_order()
        self.assertEqual(result['res_model'], 'channel.order')
        self.assertEqual(result['res_id'], channel_order.id)

    def test_action_sync_from_channel_no_link(self):
        """Test action_sync_from_channel raises when no linked order."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
        })
        with self.assertRaises(UserError):
            order.action_sync_from_channel()

    def test_action_sync_from_channel_with_link(self):
        """Test action_sync_from_channel syncs data when linked."""
        channel_order = self.env['channel.order'].create({
            'channel_order_id': 'TT-002',
            'channel_id': self.channel.id,
            'customer_name': 'Test',
            'shipping_cost': 75.0,
            'platform_fee': 15.0,
            'state': 'pending',
        })

        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'channel_order_id': channel_order.id,
        })

        result = order.action_sync_from_channel()
        self.assertEqual(result['type'], 'ir.actions.client')

        order.invalidate_recordset()
        self.assertEqual(order.channel_shipping_fee, 75.0)
        self.assertEqual(order.channel_discount, 15.0)


@tagged('post_install', '-at_install', 'multichannel', 'sale')
class TestSaleOrderChannelTotals(TransactionCase):
    """Test channel totals calculation."""

    def setUp(self):
        super().setUp()
        self.SaleOrder = self.env['sale.order']
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'standard_price': 80.0,
            'list_price': 100.0,
        })

        self.partner = self.env['res.partner'].create({'name': 'Test Customer'})

    def test_get_channel_total_amount_basic(self):
        """Test basic channel total amount calculation."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'channel_shipping_fee': 50.0,
            'channel_discount': 10.0,
            'channel_platform_fee': 5.0,
            'channel_payment_fee': 3.0,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': 'Test',
                'product_uom_qty': 2,
                'price_unit': 100.0,
            })],
        })

        totals = order._get_channel_total_amount()
        self.assertEqual(totals['subtotal'], 200.0)
        self.assertEqual(totals['shipping'], 50.0)
        self.assertEqual(totals['discount'], 10.0)
        self.assertEqual(totals['platform_fee'], 5.0)
        self.assertEqual(totals['payment_fee'], 3.0)
        self.assertEqual(totals['net_amount'], 232.0)

    def test_get_channel_total_amount_no_fees(self):
        """Test channel totals with zero fees."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': 'Test',
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        })

        totals = order._get_channel_total_amount()
        self.assertEqual(totals['subtotal'], 100.0)
        self.assertEqual(totals['net_amount'], 100.0)


@tagged('post_install', '-at_install', 'multichannel', 'sale')
class TestSaleOrderChannelReport(TransactionCase):
    """Test channel report data method."""

    def setUp(self):
        super().setUp()
        self.SaleOrder = self.env['sale.order']
        self.ChannelConfig = self.env['channel.config']

        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'standard_price': 50.0,
            'list_price': 100.0,
        })

        channel_module = self.env['channel.list.module'].create({
            'name': 'Shopee',
            'code': 'shopee',
            'active': True,
        })
        self.channel = self.ChannelConfig.create({
            'name': 'Test Shopee',
            'code': 'shopee',
            'channel_module_id': channel_module.id,
            'active': True,
            'api_url': 'sandbox',
        })

        self.partner = self.env['res.partner'].create({'name': 'Test'})

    def test_get_channel_report_data_basic(self):
        """Test basic report data."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'channel_id': self.channel.id,
            'channel_shipping_fee': 30.0,
            'channel_discount': 5.0,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': 'Test',
                'product_uom_qty': 2,
                'price_unit': 100.0,
            })],
        })

        report = order._get_channel_report_data()
        self.assertEqual(report['channel_name'], 'Test Shopee')
        self.assertEqual(report['sale_amount'], 200.0)
        self.assertEqual(report['shipping_fee'], 30.0)
        self.assertEqual(report['discount'], 5.0)
        self.assertEqual(report['total_cost'], 100.0)  # 50 * 2
        self.assertEqual(report['gross_profit'], 100.0)

    def test_get_channel_report_data_no_channel(self):
        """Test report data without channel."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
        })

        report = order._get_channel_report_data()
        self.assertEqual(report['channel_name'], 'Unknown')


@tagged('post_install', '-at_install', 'multichannel', 'sale')
class TestSaleOrderChannelCreate(TransactionCase):
    """Test creating channel order from sale order."""

    def setUp(self):
        super().setUp()
        self.SaleOrder = self.env['sale.order']
        self.ChannelConfig = self.env['channel.config']

        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100.0,
        })

        channel_module = self.env['channel.list.module'].create({
            'name': 'Shopee',
            'code': 'shopee',
            'active': True,
        })
        self.channel = self.ChannelConfig.create({
            'name': 'Test Shopee',
            'code': 'shopee',
            'channel_module_id': channel_module.id,
            'active': True,
            'api_url': 'sandbox',
        })

        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'test@example.com',
            'phone': '0812345678',
        })

    def test_action_create_channel_order(self):
        """Test creating channel order from sale order."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'channel_id': self.channel.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': 'Test',
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        })

        result = order.action_create_channel_order()
        self.assertEqual(result['res_model'], 'channel.order')

        order.invalidate_recordset()
        self.assertTrue(order.channel_order_id)
        self.assertTrue(order.channel_order_code)

    def test_action_create_channel_order_already_linked(self):
        """Test creating channel order when already linked raises."""
        existing_channel_order = self.env['channel.order'].create({
            'channel_order_id': 'EXIST-001',
            'channel_id': self.channel.id,
            'state': 'pending',
        })

        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'channel_order_id': existing_channel_order.id,
        })

        with self.assertRaises(UserError):
            order.action_create_channel_order()

    def test_action_create_channel_order_no_lines(self):
        """Test creating channel order without lines raises."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'channel_id': self.channel.id,
        })

        with self.assertRaises(UserError):
            order.action_create_channel_order()


@tagged('post_install', '-at_install', 'multichannel', 'sale')
class TestSaleOrderLineChannel(TransactionCase):
    """Test sale.order.line channel fields and methods."""

    def setUp(self):
        super().setUp()
        self.SaleOrder = self.env['sale.order']
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'standard_price': 70.0,
            'list_price': 100.0,
        })

        self.partner = self.env['res.partner'].create({'name': 'Test'})

    def test_sale_order_line_channel_fields(self):
        """Test sale.order.line has channel fields."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': 'Test',
                'product_uom_qty': 1,
                'price_unit': 100.0,
                'channel_price': 95.0,
                'channel_discount_rate': 5.0,
            })],
        })

        line = order.order_line[0]
        self.assertEqual(line.channel_price, 95.0)
        self.assertEqual(line.channel_discount_rate, 5.0)

    def test_sale_order_line_margin_calculation(self):
        """Test channel margin calculation."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': 'Test',
                'product_uom_qty': 1,
                'price_unit': 100.0,
                'channel_price': 100.0,
            })],
        })

        line = order.order_line[0]
        # Margin = (channel_price - cost) / channel_price * 100
        # = (100 - 70) / 100 * 100 = 30%
        self.assertEqual(line.channel_margin, 30.0)

    def test_sale_order_line_margin_no_channel_price(self):
        """Test margin is 0 when no channel price."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': 'Test',
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        })

        line = order.order_line[0]
        self.assertEqual(line.channel_margin, 0.0)


@tagged('post_install', '-at_install', 'multichannel', 'sale')
class TestSaleOrderChannelInvoice(TransactionCase):
    """Test invoice integration."""

    def setUp(self):
        super().setUp()
        self.SaleOrder = self.env['sale.order']
        self.ChannelConfig = self.env['channel.config']

        channel_module = self.env['channel.list.module'].create({
            'name': 'Shopee',
            'code': 'shopee',
            'active': True,
        })
        self.channel = self.ChannelConfig.create({
            'name': 'Test Shopee',
            'code': 'shopee',
            'channel_module_id': channel_module.id,
            'active': True,
            'api_url': 'sandbox',
        })

        self.partner = self.env['res.partner'].create({'name': 'Test'})

    def test_prepare_invoice_vals_with_channel(self):
        """Test invoice vals include channel order code."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'channel_id': self.channel.id,
            'channel_order_code': 'SO-001',
        })

        vals = order._prepare_invoice_vals()
        self.assertIn('SO-001', vals.get('invoice_origin', ''))


@tagged('post_install', '-at_install', 'multichannel', 'sale')
class TestChannelOrderStateUpdate(TransactionCase):
    """Test channel.order state update method."""

    def setUp(self):
        super().setUp()
        self.ChannelOrder = self.env['channel.order']
        self.SaleOrder = self.env['sale.order']
        self.ChannelConfig = self.env['channel.config']

        channel_module = self.env['channel.list.module'].create({
            'name': 'Shopee',
            'code': 'shopee',
            'active': True,
        })
        self.channel = self.ChannelConfig.create({
            'name': 'Test Shopee',
            'code': 'shopee',
            'channel_module_id': channel_module.id,
            'active': True,
            'api_url': 'sandbox',
        })

        self.partner = self.env['res.partner'].create({'name': 'Test'})

    def test_update_sale_order_state_no_sale_order(self):
        """Test update_sale_order_state does nothing when no sale order."""
        channel_order = self.ChannelOrder.create({
            'channel_order_id': 'CO-001',
            'channel_id': self.channel.id,
            'state': 'pending',
        })

        # Should not raise
        channel_order._update_sale_order_state('sale_confirmed')

    def test_update_sale_order_state_with_sale_order(self):
        """Test update_sale_order_state updates state correctly."""
        sale_order = self.SaleOrder.create({
            'partner_id': self.partner.id,
        })

        channel_order = self.ChannelOrder.create({
            'channel_order_id': 'CO-002',
            'channel_id': self.channel.id,
            'sale_order_id': sale_order.id,
            'state': 'pending',
        })

        channel_order._update_sale_order_state('sale_confirmed')
        self.assertEqual(channel_order.state, 'confirmed')

        channel_order._update_sale_order_state('cancelled')
        self.assertEqual(channel_order.state, 'cancelled')

        channel_order._update_sale_order_state('done')
        self.assertEqual(channel_order.state, 'delivered')
