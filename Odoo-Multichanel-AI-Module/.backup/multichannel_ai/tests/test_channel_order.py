# -*- coding: utf-8 -*-
# Test for channel.order model
import unittest
from unittest.mock import patch, MagicMock

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'multichannel')
class TestChannelOrder(TransactionCase):
    """Test channel.order model."""

    def setUp(self):
        super().setUp()
        # Create test channel
        self.ChannelConfig = self.env['channel.config']
        self.ChannelOrder = self.env['channel.order']

        # Get or create module
        self.channel_module = self.env.ref(
            'multichannel_ai.channel_module_shopee',
            raise_if_not_found=False
        )
        if not self.channel_module:
            self.channel_module = self.env['channel.list.module'].create({
                'name': 'Shopee',
                'code': 'shopee',
                'active': True,
            })

        # Create test config
        self.test_channel = self.ChannelConfig.create({
            'name': 'Test Shopee',
            'code': 'shopee',
            'channel_module_id': self.channel_module.id,
            'active': True,
            'api_url': 'sandbox',  # MOCK mode
        })

    def test_create_order_from_webhook(self):
        """Test create order from webhook data."""
        order_data = {
            'order_id': 'TEST-ORDER-001',
            'platform': 'shopee',
            'buyer_username': 'test_buyer',
            'total_amount': 1000.0,
            'currency': 'THB',
            'status': 'pending',
        }
        order = self.ChannelOrder.create_from_webhook(
            'shopee',
            order_data,
        )
        self.assertTrue(order.id)
        self.assertEqual(order.platform_order_id, 'TEST-ORDER-001')
        self.assertEqual(order.channel_id.code, 'shopee')
        self.assertEqual(order.state, 'pending')

    def test_state_mapping(self):
        """Test _map_channel_state_to_odoo covers all states."""
        Order = self.ChannelOrder
        state_map = {
            'pending': 'pending',
            'awaiting_payment': 'pending',
            'awaiting_shipment': 'confirmed',
            'shipped': 'shipped',
            'delivered': 'delivered',
            'cancelled': 'cancelled',
            'refunded': 'refunded',
            'processing': 'processing',
        }
        for channel_state, expected_odoo in state_map.items():
            result = Order._map_channel_state_to_odoo(channel_state)
            self.assertEqual(
                result, expected_odoo,
                "State '%s' should map to '%s'" % (channel_state, expected_odoo),
            )

    def test_state_mapping_unknown_defaults_to_pending(self):
        """Test unknown channel state defaults to pending."""
        Order = self.ChannelOrder
        self.assertEqual(Order._map_channel_state_to_odoo('unknown_state'), 'pending')
        self.assertEqual(Order._map_channel_state_to_odoo(''), 'pending')
        self.assertEqual(Order._map_channel_state_to_odoo(None), 'pending')

    def test_state_mapping_case_insensitive(self):
        """Test state mapping is case-insensitive."""
        Order = self.ChannelOrder
        self.assertEqual(Order._map_channel_state_to_odoo('SHIPPED'), 'shipped')
        self.assertEqual(Order._map_channel_state_to_odoo('Delivered'), 'delivered')

    def test_order_totals_computation(self):
        """Test order total computation with line items."""
        order = self.ChannelOrder.create_from_webhook('shopee', {
            'order_id': 'TEST-TOTAL',
            'platform': 'shopee',
            'total_amount': 1000.0,
        })
        # Add line items
        self.env['channel.order.line'].create({
            'order_id': order.id,
            'product_name': 'Test Product',
            'quantity': 2,
            'unit_price': 500.0,
        })
        # Trigger recompute
        order._compute_totals()
        self.assertGreater(order.amount_total, 0)

    @patch('odoo.addons.multichannel_ai.models.connectors.get_connector')
    def test_action_refresh_status_calls_connector(self, mock_get_connector):
        """Test action_refresh_status uses connector.get_order_detail."""
        mock_connector = MagicMock()
        mock_connector.get_order_detail.return_value = {
            'status': 'shipped',
            'tracking_number': 'TRK123',
        }
        mock_get_connector.return_value = mock_connector

        order = self.ChannelOrder.create_from_webhook('shopee', {
            'order_id': 'TEST-REFRESH',
            'platform': 'shopee',
            'total_amount': 100.0,
        })
        order.action_refresh_status()
        mock_connector.get_order_detail.assert_called_once()

    def test_action_cancel_validates_state(self):
        """Test action_cancel_on_platform validates state."""
        order = self.ChannelOrder.create_from_webhook('shopee', {
            'order_id': 'TEST-CANCEL',
            'platform': 'shopee',
            'total_amount': 100.0,
        })
        # Mark as shipped - should not allow cancel
        order.write({'state': 'shipped'})
        with self.assertRaises(Exception):
            order.action_cancel_on_platform()

    def test_action_refund_validates_state(self):
        """Test action_refund_on_platform requires delivered state."""
        order = self.ChannelOrder.create_from_webhook('shopee', {
            'order_id': 'TEST-REFUND',
            'platform': 'shopee',
            'total_amount': 100.0,
        })
        # Not delivered yet - should not allow refund
        with self.assertRaises(Exception):
            order.action_refund_on_platform()


@tagged('post_install', '-at_install', 'multichannel')
class TestChannelOrderLine(TransactionCase):
    """Test channel.order.line model."""

    def setUp(self):
        super().setUp()
        self.ChannelOrder = self.env['channel.order']
        self.channel_module = self.env.ref(
            'multichannel_ai.channel_module_shopee',
            raise_if_not_found=False,
        ) or self.env['channel.list.module'].create({
            'name': 'Shopee',
            'code': 'shopee',
            'active': True,
        })
        self.test_channel = self.env['channel.config'].create({
            'name': 'Test',
            'code': 'shopee',
            'channel_module_id': self.channel_module.id,
            'active': True,
        })

    def test_line_subtotal_computation(self):
        """Test order line subtotal = quantity * unit_price."""
        order = self.ChannelOrder.create_from_webhook('shopee', {
            'order_id': 'TEST-LINE',
            'platform': 'shopee',
            'total_amount': 500.0,
        })
        line = self.env['channel.order.line'].create({
            'order_id': order.id,
            'product_name': 'Widget',
            'quantity': 3,
            'unit_price': 100.0,
        })
        line._compute_subtotal()
        self.assertEqual(line.subtotal, 300.0)