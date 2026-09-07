# -*- coding: utf-8 -*-
# Test for ai.category.mapping model
import unittest
from unittest.mock import patch, MagicMock

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'multichannel')
class TestAICategoryMapping(TransactionCase):
    """Test ai.category.mapping model."""

    def setUp(self):
        super().setUp()
        self.AICategoryMapping = self.env['ai.category.mapping']
        self.AIEngine = self.env['ai.engine']

        # Create test AI engine
        self.engine = self.AIEngine.create({
            'name': 'Test Engine',
            'provider': 'openrouter',
        })

        # Create test Odoo category
        self.category = self.env['product.category'].create({
            'name': 'Electronics',
        })

    def test_create_category_mapping(self):
        """Test creating AI category mapping."""
        mapping = self.AICategoryMapping.create({
            'engine_id': self.engine.id,
            'product_name': 'iPhone 13',
            'category_id': self.category.id,
            'confidence': 0.95,
        })
        self.assertTrue(mapping.id)
        self.assertEqual(mapping.product_name, 'iPhone 13')
        self.assertEqual(mapping.confidence, 0.95)

    def test_search_by_product_name(self):
        """Test search by product name (indexed)."""
        self.AICategoryMapping.create({
            'engine_id': self.engine.id,
            'product_name': 'iPhone 13 Pro',
            'category_id': self.category.id,
        })
        results = self.AICategoryMapping.search([
            ('product_name', 'ilike', 'iphone'),
        ])
        self.assertGreaterEqual(len(results), 1)

    def test_confidence_range(self):
        """Test confidence is between 0 and 1."""
        # Valid confidence
        mapping = self.AICategoryMapping.create({
            'engine_id': self.engine.id,
            'product_name': 'Test',
            'category_id': self.category.id,
            'confidence': 0.5,
        })
        self.assertGreaterEqual(mapping.confidence, 0.0)
        self.assertLessEqual(mapping.confidence, 1.0)

    def test_search_high_confidence(self):
        """Test search for high confidence mappings."""
        # Create mappings with varying confidence
        for i, conf in enumerate([0.9, 0.5, 0.3]):
            self.AICategoryMapping.create({
                'engine_id': self.engine.id,
                'product_name': f'Product {i}',
                'category_id': self.category.id,
                'confidence': conf,
            })
        high_conf = self.AICategoryMapping.search([
            ('confidence', '>=', 0.8),
        ])
        self.assertGreaterEqual(len(high_conf), 1)


if __name__ == '__main__':
    unittest.main()