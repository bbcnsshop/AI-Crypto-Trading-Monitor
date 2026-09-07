# -*- coding: utf-8 -*-
# Test for product.product (with channel extension via _inherit)
import unittest
from unittest.mock import patch, MagicMock

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'multichannel')
class TestProductProductChannel(TransactionCase):
    """Test product.product with channel extension."""

    def setUp(self):
        super().setUp()
        self.ProductProduct = self.env['product.product']

    def test_create_product(self):
        """Test creating a product."""
        product = self.ProductProduct.create({
            'name': 'Test Product',
            'list_price': 100.0,
            'standard_price': 50.0,
        })
        self.assertTrue(product.id)
        self.assertEqual(product.name, 'Test Product')

    def test_product_with_channel_count(self):
        """Test product has channel_product_count field."""
        product = self.ProductProduct.create({
            'name': 'Channel Count Test',
            'list_price': 100.0,
        })
        # Field should exist (added by _inherit)
        self.assertTrue(hasattr(product, 'channel_product_ids'))
        # Initially 0
        self.assertEqual(product.channel_product_count, 0)

    def test_channel_product_count_computation(self):
        """Test channel_product_count is computed."""
        # Create channel
        channel_module = self.env.ref(
            'multichannel_ai.channel_module_shopee',
            raise_if_not_found=False,
        ) or self.env['channel.list.module'].create({
            'name': 'Shopee',
            'code': 'shopee',
            'active': True,
        })
        channel = self.env['channel.config'].create({
            'name': 'Test',
            'code': 'shopee',
            'channel_module_id': channel_module.id,
            'active': True,
            'api_url': 'sandbox',
        })

        # Create product
        product = self.ProductProduct.create({
            'name': 'Multi Channel Test',
            'list_price': 100.0,
        })

        # Create channel products
        for i in range(3):
            self.env['channel.product'].create({
                'name': f'Channel Product {i}',
                'channel_id': channel.id,
                'product_id': product.id,
                'channel_state': 'active',
            })

        # Recompute
        product._compute_channel_product_count()
        self.assertEqual(product.channel_product_count, 3)

    def test_action_view_channel_products(self):
        """Test action_view_channel_products returns action."""
        product = self.ProductProduct.create({
            'name': 'Action Test',
            'list_price': 50.0,
        })
        result = product.action_view_channel_products()
        self.assertEqual(result['type'], 'ir.actions.act_window')


if __name__ == '__main__':
    unittest.main()