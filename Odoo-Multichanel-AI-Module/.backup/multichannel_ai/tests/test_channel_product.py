# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install', 'multichannel')
class TestChannelProduct(TransactionCase):
    """Test channel.product model."""

    def setUp(self):
        super(TestChannelProduct, self).setUp()
        self.ChannelConfig = self.env['channel.config']
        self.ProductTemplate = self.env['product.template']
        self.ChannelProduct = self.env['channel.product']

        self.channel = self.ChannelConfig.create({
            'name': 'Test Shopee',
            'code': 'shopee_test_2',
        })

        self.product = self.ProductTemplate.create({
            'name': 'Test Laptop',
            'list_price': 30000.0,
            'standard_price': 20000.0,
            'type': 'product',
        })
        self.variant = self.product.product_variant_ids[0]

    def test_create_channel_product(self):
        """Test creating a channel product."""
        cp = self.ChannelProduct.create({
            'name': 'Test Laptop (Shopee)',
            'product_id': self.variant.id,
            'channel_id': self.channel.id,
            'channel_price': 29500.0,
            'channel_qty': 10,
        })
        self.assertTrue(cp.id)
        self.assertEqual(cp.state, 'draft')
        self.assertEqual(cp.sync_status, 'never')

    def test_compute_name(self):
        """Test that name is auto-computed."""
        cp = self.ChannelProduct.create({
            'product_id': self.variant.id,
            'channel_id': self.channel.id,
            'channel_price': 25000.0,
        })
        self.assertIn('Test Laptop', cp.name)
        self.assertIn('Test Shopee', cp.name)

    def test_state_transitions(self):
        """Test state transitions."""
        cp = self.ChannelProduct.create({
            'product_id': self.variant.id,
            'channel_id': self.channel.id,
            'channel_price': 25000.0,
        })
        self.assertEqual(cp.state, 'draft')
        cp.state = 'active'
        self.assertEqual(cp.state, 'active')
        cp.state = 'inactive'
        self.assertEqual(cp.state, 'inactive')

    def test_sync_status_changes(self):
        """Test sync_status changes."""
        cp = self.ChannelProduct.create({
            'product_id': self.variant.id,
            'channel_id': self.channel.id,
            'channel_price': 25000.0,
            'sync_status': 'pending',
        })
        self.assertEqual(cp.sync_status, 'pending')
        cp.write({'sync_status': 'synced'})
        self.assertEqual(cp.sync_status, 'synced')

    def test_completeness_pct(self):
        """Test completeness percentage."""
        cp = self.ChannelProduct.create({
            'product_id': self.variant.id,
            'channel_id': self.channel.id,
            'channel_price': 25000.0,
        })
        # Should be some value
        self.assertIsNotNone(cp.completeness_pct)
        self.assertGreaterEqual(cp.completeness_pct, 0)
        self.assertLessEqual(cp.completeness_pct, 100)

    def test_channel_product_by_product(self):
        """Test finding channel products by product."""
        cp = self.ChannelProduct.create({
            'product_id': self.variant.id,
            'channel_id': self.channel.id,
            'channel_price': 25000.0,
        })
        results = self.ChannelProduct.search([
            ('product_id', '=', self.variant.id)
        ])
        self.assertIn(cp, results)
        self.assertEqual(len(results), 1)

    def test_unlink_protection(self):
        """Test unlink behavior."""
        cp = self.ChannelProduct.create({
            'product_id': self.variant.id,
            'channel_id': self.channel.id,
            'channel_price': 25000.0,
            'sync_status': 'synced',
        })
        # Should be deletable but logs warning
        cp.unlink()
        self.assertFalse(cp.exists())