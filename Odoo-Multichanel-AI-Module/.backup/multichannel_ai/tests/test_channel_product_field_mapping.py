# -*- coding: utf-8 -*-
# Test for channel.product.field.mapping and channel.product.completeness models
import unittest
from unittest.mock import patch, MagicMock

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'multichannel')
class TestChannelProductFieldMapping(TransactionCase):
    """Test channel.product.field.mapping model."""

    def setUp(self):
        super().setUp()
        self.Mapping = self.env['channel.product.field.mapping']

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

    def test_create_field_mapping(self):
        """Test creating a field mapping."""
        mapping = self.Mapping.create({
            'channel_id': self.channel.id,
            'odoo_field_name': 'name',
            'platform_field_name': 'product_name',
            'field_type': 'char',
            'required': True,
        })
        self.assertTrue(mapping.id)
        self.assertEqual(mapping.odoo_field_name, 'name')
        self.assertEqual(mapping.platform_field_name, 'product_name')

    def test_field_mapping_unique_per_channel(self):
        """Test field mapping is unique per channel."""
        self.Mapping.create({
            'channel_id': self.channel.id,
            'odoo_field_name': 'description',
            'platform_field_name': 'desc',
            'field_type': 'text',
        })
        # Creating duplicate should fail
        with self.assertRaises(Exception):
            self.Mapping.create({
                'channel_id': self.channel.id,
                'odoo_field_name': 'description',
                'platform_field_name': 'desc_dup',
                'field_type': 'text',
            })

    def test_get_mapping_for_channel(self):
        """Test getting all mappings for a channel."""
        # Create multiple mappings
        fields = ['name', 'description', 'list_price']
        for i, field in enumerate(fields):
            self.Mapping.create({
                'channel_id': self.channel.id,
                'odoo_field_name': field,
                'platform_field_name': f'platform_{field}',
                'field_type': 'char',
            })
        mappings = self.Mapping.search([
            ('channel_id', '=', self.channel.id),
        ])
        self.assertEqual(len(mappings), 3)

    def test_mapping_active_state(self):
        """Test active/inactive field mappings."""
        mapping = self.Mapping.create({
            'channel_id': self.channel.id,
            'odoo_field_name': 'weight',
            'platform_field_name': 'weight_gram',
            'field_type': 'float',
            'active': True,
        })
        mapping.write({'active': False})
        self.assertFalse(mapping.active)


@tagged('post_install', '-at_install', 'multichannel')
class TestChannelProductCompleteness(TransactionCase):
    """Test channel.product.completeness model."""

    def setUp(self):
        super().setUp()
        self.Completeness = self.env['channel.product.completeness']

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

        # Create channel product
        self.channel_product = self.env['channel.product'].create({
            'name': 'Test Product',
            'channel_id': self.channel.id,
            'product_id': self.env['product.product'].create({
                'name': 'Base Product',
            }).id,
        })

    def test_create_completeness_record(self):
        """Test creating a completeness record."""
        completeness = self.Completeness.create({
            'channel_product_id': self.channel_product.id,
            'field_name': 'name',
            'is_complete': True,
        })
        self.assertTrue(completeness.id)
        self.assertTrue(completeness.is_complete)

    def test_completeness_percentage(self):
        """Test completeness calculation."""
        # Create 5 completeness records
        for i in range(5):
            self.Completeness.create({
                'channel_product_id': self.channel_product.id,
                'field_name': f'field_{i}',
                'is_complete': i < 3,  # 3 out of 5
            })
        # Calculate completeness
        records = self.Completeness.search([
            ('channel_product_id', '=', self.channel_product.id),
        ])
        complete_count = len(records.filtered('is_complete'))
        total_count = len(records)
        pct = (complete_count / total_count * 100) if total_count > 0 else 0
        self.assertEqual(pct, 60.0)


if __name__ == '__main__':
    unittest.main()
