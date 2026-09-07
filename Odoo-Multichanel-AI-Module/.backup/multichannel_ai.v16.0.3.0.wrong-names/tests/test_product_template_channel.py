# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'multichannel')
class TestProductTemplateChannel(TransactionCase):
    """Test product.template channel extensions."""

    def setUp(self):
        super(TestProductTemplateChannel, self).setUp()
        self.ProductTemplate = self.env['product.template']
        self.ChannelConfig = self.env['channel.config']
        self.ChannelProduct = self.env['channel.product']

        self.shopee = self.ChannelConfig.create({
            'name': 'Shopee',
            'code': 'shopee_tpl_test',
        })
        self.lazada = self.ChannelConfig.create({
            'name': 'Lazada',
            'code': 'lazada_tpl_test',
        })
        self.tiktok = self.ChannelConfig.create({
            'name': 'TikTok',
            'code': 'tiktok_tpl_test',
        })

        self.product = self.ProductTemplate.create({
            'name': 'Test Product',
            'list_price': 1000.0,
            'standard_price': 500.0,
            'type': 'product',
        })

    def test_initial_state(self):
        """Test initial channel state - all False."""
        self.assertFalse(self.product.is_on_shopee)
        self.assertFalse(self.product.is_on_lazada)
        self.assertFalse(self.product.is_on_tiktok)
        self.assertFalse(self.product.is_sold_online)
        self.assertEqual(self.product.channel_product_count, 0)

    def test_add_to_shopee(self):
        """Test adding product to Shopee."""
        variant = self.product.product_variant_ids[0]
        self.ChannelProduct.create({
            'product_id': variant.id,
            'channel_id': self.shopee.id,
            'channel_price': 1000.0,
            'channel_qty': 5,
            'state': 'active',
        })
        # Force recompute
        self.product.invalidate_recordset()
        self.assertTrue(self.product.is_on_shopee)
        self.assertFalse(self.product.is_on_lazada)
        self.assertEqual(self.product.channel_product_count, 1)
        self.assertTrue(self.product.is_sold_online)

    def test_add_to_multiple_channels(self):
        """Test product on multiple channels."""
        variant = self.product.product_variant_ids[0]
        self.ChannelProduct.create({
            'product_id': variant.id,
            'channel_id': self.shopee.id,
            'channel_price': 1000.0,
            'state': 'active',
        })
        self.ChannelProduct.create({
            'product_id': variant.id,
            'channel_id': self.lazada.id,
            'channel_price': 1000.0,
            'state': 'active',
        })
        self.product.invalidate_recordset()
        self.assertTrue(self.product.is_on_shopee)
        self.assertTrue(self.product.is_on_lazada)
        self.assertFalse(self.product.is_on_tiktok)
        self.assertEqual(self.product.channel_product_count, 2)

    def test_channel_product_ids(self):
        """Test channel_product_ids returns related records."""
        variant = self.product.product_variant_ids[0]
        cp = self.ChannelProduct.create({
            'product_id': variant.id,
            'channel_id': self.shopee.id,
            'channel_price': 1000.0,
            'state': 'active',
        })
        self.product.invalidate_recordset()
        self.assertIn(cp, self.product.channel_product_ids)

    def test_online_total_stock(self):
        """Test total online stock computation."""
        variant = self.product.product_variant_ids[0]
        self.ChannelProduct.create({
            'product_id': variant.id,
            'channel_id': self.shopee.id,
            'channel_price': 1000.0,
            'channel_qty': 50,
            'state': 'active',
        })
        self.ChannelProduct.create({
            'product_id': variant.id,
            'channel_id': self.lazada.id,
            'channel_price': 1000.0,
            'channel_qty': 30,
            'state': 'active',
        })
        self.product.invalidate_recordset()
        self.assertEqual(self.product.online_total_stock, 80)

    def test_online_revenue_potential(self):
        """Test revenue potential calculation."""
        variant = self.product.product_variant_ids[0]
        self.ChannelProduct.create({
            'product_id': variant.id,
            'channel_id': self.shopee.id,
            'channel_price': 1000.0,
            'channel_qty': 10,
            'state': 'active',
        })
        self.product.invalidate_recordset()
        self.assertEqual(self.product.online_revenue_potential, 10000.0)

    def test_get_first_variant(self):
        """Test _get_first_variant method."""
        variant = self.product._get_first_variant()
        self.assertTrue(variant.exists())
        self.assertIn(variant, self.product.product_variant_ids)