# -*- coding: utf-8 -*-
# Test for product.category.mapping model
import unittest
from unittest.mock import patch, MagicMock

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'multichannel')
class TestCategoryMapping(TransactionCase):
    """Test product.category.mapping model."""

    def setUp(self):
        super().setUp()
        self.CategoryMapping = self.env['product.category.mapping']

        # Create test channel
        channel_module = self.env.ref(
            'multichannel_ai.channel_module_shopee',
            raise_if_not_found=False,
        ) or self.env['channel.list.module'].create({
            'name': 'Shopee',
            'code': 'shopee',
            'active': True,
        })
        self.channel = self.env['channel.config'].create({
            'name': 'Test Shopee',
            'code': 'shopee',
            'channel_module_id': channel_module.id,
            'active': True,
            'api_url': 'sandbox',
        })

        # Create test Odoo category
        self.category = self.env['product.category'].create({
            'name': 'Electronics',
        })

    def test_create_category_mapping(self):
        """Test creating a category mapping."""
        mapping = self.CategoryMapping.create({
            'channel_id': self.channel.id,
            'odoo_category_id': self.category.id,
            'channel_category_id': 'shopee_electronics_001',
            'channel_category_name': 'Electronics & Gadgets',
            'confidence': 0.95,
        })
        self.assertTrue(mapping.id)
        self.assertEqual(mapping.channel_category_name, 'Electronics & Gadgets')
        self.assertEqual(mapping.confidence, 0.95)

    def test_category_mapping_rec_name(self):
        """Test _rec_name uses channel_category_name."""
        mapping = self.CategoryMapping.create({
            'channel_id': self.channel.id,
            'odoo_category_id': self.category.id,
            'channel_category_id': 'cat_001',
            'channel_category_name': 'Display Name',
        })
        self.assertEqual(mapping._rec_name, 'channel_category_name')
        # Verify rec_name field
        self.assertEqual(mapping.display_name, 'Display Name')

    def test_search_by_confidence(self):
        """Test searching high-confidence mappings."""
        # Create mappings with different confidence
        self.CategoryMapping.create({
            'channel_id': self.channel.id,
            'odoo_category_id': self.category.id,
            'channel_category_id': 'high',
            'channel_category_name': 'High Confidence',
            'confidence': 0.95,
        })
        self.CategoryMapping.create({
            'channel_id': self.channel.id,
            'odoo_category_id': self.category.id,
            'channel_category_id': 'low',
            'channel_category_name': 'Low Confidence',
            'confidence': 0.3,
        })
        high = self.CategoryMapping.search([
            ('confidence', '>=', 0.8),
        ])
        self.assertGreaterEqual(len(high), 1)

    def test_unique_mapping_per_channel(self):
        """Test unique mapping per channel for odoo category."""
        self.CategoryMapping.create({
            'channel_id': self.channel.id,
            'odoo_category_id': self.category.id,
            'channel_category_id': 'first',
            'channel_category_name': 'First',
        })
        # Duplicate mapping for same channel + odoo_category should fail
        with self.assertRaises(Exception):
            self.CategoryMapping.create({
                'channel_id': self.channel.id,
                'odoo_category_id': self.category.id,
                'channel_category_id': 'second',
                'channel_category_name': 'Second',
            })


if __name__ == '__main__':
    unittest.main()