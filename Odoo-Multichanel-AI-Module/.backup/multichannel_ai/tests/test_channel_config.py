# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'multichannel')
class TestChannelConfig(TransactionCase):
    """Test channel.config model."""

    def setUp(self):
        super(TestChannelConfig, self).setUp()
        self.ChannelConfig = self.env['channel.config']
        self.channel_shopee = self.ChannelConfig.create({
            'name': 'Shopee Test',
            'code': 'shopee_test',
            'active': True,
            'platform_fee': 5.0,
            'payment_fee': 2.0,
        })

    def test_create_channel(self):
        """Test creating a new channel."""
        channel = self.ChannelConfig.create({
            'name': 'Lazada Test',
            'code': 'lazada_test',
        })
        self.assertTrue(channel.id, 'Channel should be created')
        self.assertEqual(channel.code, 'lazada_test')
        self.assertFalse(channel.active, 'Should be inactive by default')

    def test_unique_code(self):
        """Test that channel codes are unique."""
        with self.assertRaises(Exception):
            self.ChannelConfig.create({
                'name': 'Duplicate Shopee',
                'code': 'shopee_test',
            })

    def test_channel_active(self):
        """Test activating/deactivating channel."""
        self.assertTrue(self.channel_shopee.active)
        self.channel_shopee.active = False
        self.assertFalse(self.channel_shopee.active)

    def test_search_active_channels(self):
        """Test searching for active channels."""
        active = self.ChannelConfig.search([('active', '=', True)])
        self.assertIn(self.channel_shopee, active)

    def test_fee_config(self):
        """Test fee configuration fields."""
        self.assertEqual(self.channel_shopee.platform_fee, 5.0)
        self.assertEqual(self.channel_shopee.payment_fee, 2.0)
        self.assertEqual(self.channel_shopee.shipping_fee, 0.0)