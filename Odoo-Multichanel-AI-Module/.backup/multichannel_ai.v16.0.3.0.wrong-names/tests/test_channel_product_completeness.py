# -*- coding: utf-8 -*-
"""Test Channel Product Completeness model."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'multichannel', 'completeness')
class TestChannelProductCompleteness(TransactionCase):
    """Test channel.product.completeness model."""

    def setUp(self):
        super().setUp()
        self.Completeness = self.env['channel.product.completeness']
        self.ChannelProduct = self.env['channel.product']
        self.ChannelConfig = self.env['channel.config']
        self.Product = self.env['product.product']

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

        self.product = self.Product.create({
            'name': 'Test Product',
            'list_price': 100.0,
        })

        self.channel_product = self.ChannelProduct.create({
            'product_id': self.product.id,
            'channel_id': self.channel.id,
        })

    def test_create_completeness_record(self):
        """Test creating completeness record."""
        record = self.Completeness.create({
            'channel_product_id': self.channel_product.id,
            'channel_id': self.channel.id,
        })
        self.assertTrue(record.id)
        # Should auto-compute to 100% (no required fields)
        self.assertEqual(record.completeness_pct, 100.0)
        self.assertEqual(record.status, 'ready')

    def test_upsert_creates_new(self):
        """Test upsert creates new record when none exists."""
        result = self.Completeness.upsert(self.channel_product.id, self.channel.id)
        self.assertTrue(result)
        self.assertEqual(result.channel_product_id, self.channel_product)
        self.assertEqual(result.channel_id, self.channel)

    def test_upsert_updates_existing(self):
        """Test upsert updates existing record."""
        existing = self.Completeness.create({
            'channel_product_id': self.channel_product.id,
            'channel_id': self.channel.id,
        })
        result = self.Completeness.upsert(self.channel_product.id, self.channel.id)
        self.assertEqual(result.id, existing.id)

    def test_completeness_with_required_fields(self):
        """Test completeness with required field mappings."""
        # Create required field mapping
        self.env['channel.product.field.mapping'].create({
            'channel_id': self.channel.id,
            'odoo_field': 'name',
            'platform_field': 'item_name',
            'description': 'Item Name',
            'is_required': True,
            'active': True,
        })

        # Update channel product name to fill the required field
        self.channel_product.channel_title = 'Test Product'

        record = self.Completeness.upsert(self.channel_product.id, self.channel.id)
        self.assertEqual(record.total_required, 1)
        self.assertEqual(record.total_filled, 1)
        self.assertEqual(record.completeness_pct, 100.0)
        self.assertEqual(record.status, 'ready')

    def test_completeness_with_missing_fields(self):
        """Test completeness with missing required fields."""
        # Create required field mapping
        self.env['channel.product.field.mapping'].create({
            'channel_id': self.channel.id,
            'odoo_field': 'description',
            'platform_field': 'item_description',
            'description': 'Item Description',
            'is_required': True,
            'active': True,
        })

        record = self.Completeness.upsert(self.channel_product.id, self.channel.id)
        # description is empty by default
        self.assertEqual(record.total_required, 1)
        self.assertEqual(record.total_filled, 0)
        self.assertEqual(record.completeness_pct, 0.0)
        self.assertEqual(record.status, 'incomplete')
        self.assertIn('description', record.missing_field_names.lower())

    def test_completeness_partial_filled(self):
        """Test completeness with partial fields filled."""
        # Create 2 required mappings
        self.env['channel.product.field.mapping'].create({
            'channel_id': self.channel.id,
            'odoo_field': 'name',
            'platform_field': 'item_name',
            'description': 'Item Name',
            'is_required': True,
            'active': True,
        })
        self.env['channel.product.field.mapping'].create({
            'channel_id': self.channel.id,
            'odoo_field': 'description',
            'platform_field': 'item_description',
            'description': 'Item Description',
            'is_required': True,
            'active': True,
        })

        # Fill only name
        self.channel_product.channel_title = 'Test Product'

        record = self.Completeness.upsert(self.channel_product.id, self.channel.id)
        self.assertEqual(record.total_required, 2)
        self.assertEqual(record.total_filled, 1)
        self.assertEqual(record.completeness_pct, 50.0)
        self.assertEqual(record.status, 'incomplete')

    def test_sql_constraint_unique(self):
        """Test that duplicate completeness records are prevented."""
        from psycopg2 import IntegrityError
        self.Completeness.create({
            'channel_product_id': self.channel_product.id,
            'channel_id': self.channel.id,
        })
        # Should raise on duplicate
        with self.assertRaises(Exception):
            self.Completeness.create({
                'channel_product_id': self.channel_product.id,
                'channel_id': self.channel.id,
            })

    def test_compute_counts_no_channel(self):
        """Test _compute_counts when no channel set."""
        record = self.Completeness.create({
            'channel_product_id': self.channel_product.id,
        })
        # Should default to 100% ready
        self.assertEqual(record.total_required, 0)
        self.assertEqual(record.total_filled, 0)
        self.assertEqual(record.completeness_pct, 100.0)
        self.assertEqual(record.status, 'ready')

    def test_missing_field_names_format(self):
        """Test missing field names are comma-separated."""
        self.env['channel.product.field.mapping'].create({
            'channel_id': self.channel.id,
            'odoo_field': 'description',
            'platform_field': 'desc1',
            'description': 'Description Field 1',
            'is_required': True,
            'active': True,
        })
        self.env['channel.product.field.mapping'].create({
            'channel_id': self.channel.id,
            'odoo_field': 'default_code',
            'platform_field': 'sku1',
            'description': 'SKU Field',
            'is_required': True,
            'active': True,
        })

        record = self.Completeness.upsert(self.channel_product.id, self.channel.id)
        # Should have both missing fields listed
        self.assertIn('Description Field 1', record.missing_field_names)
        self.assertIn('SKU Field', record.missing_field_names)
