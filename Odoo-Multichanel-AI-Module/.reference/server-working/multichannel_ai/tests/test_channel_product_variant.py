# -*- coding: utf-8 -*-
# Test for channel.product.variant model
import unittest
from unittest.mock import patch, MagicMock

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'multichannel')
class TestChannelProductVariant(TransactionCase):
    """Test channel.product.variant model."""

    def setUp(self):
        super().setUp()
        self.Variant = self.env['channel.product.variant']

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
            'name': 'Test Channel Product',
            'channel_id': self.channel.id,
            'product_id': self.env['product.product'].create({
                'name': 'Test Product',
            }).id,
            'channel_state': 'active',
        })

    def test_create_variant(self):
        """Test creating a channel product variant."""
        variant = self.Variant.create({
            'channel_product_id': self.channel_product.id,
            'odoo_variant_id': self.env['product.product'].create({
                'name': 'Variant 1',
            }).id,
            'channel_price': 100.0,
            'channel_qty': 50,
        })
        self.assertTrue(variant.id)
        self.assertEqual(variant.channel_price, 100.0)
        self.assertEqual(variant.channel_qty, 50)

    def test_variant_name_get(self):
        """Test variant name_get returns proper display name."""
        variant = self.Variant.create({
            'channel_product_id': self.channel_product.id,
            'odoo_variant_id': self.env['product.product'].create({
                'name': 'Size: L',
            }).id,
        })
        name = variant.name_get()
        self.assertTrue(len(name) > 0)

    def test_check_variant_values(self):
        """Test constraints on variant price and quantity."""
        variant = self.Variant.create({
            'channel_product_id': self.channel_product.id,
            'odoo_variant_id': self.env['product.product'].create({
                'name': 'Test',
            }).id,
        })
        # Should allow positive values
        variant.write({'channel_price': 50.0, 'channel_qty': 10})
        # Should raise on negative price
        with self.assertRaises(Exception):
            variant.write({'channel_price': -10.0})
        # Should raise on negative qty
        with self.assertRaises(Exception):
            variant.write({'channel_qty': -5})

    @patch('odoo.addons.multichannel_ai.models.connectors.get_connector')
    def test_action_sync_to_platform(self, mock_get_connector):
        """Test sync_to_platform calls connector."""
        mock_connector = MagicMock()
        mock_connector.update_item.return_value = {'success': True}
        mock_get_connector.return_value = mock_connector

        variant = self.Variant.create({
            'channel_product_id': self.channel_product.id,
            'odoo_variant_id': self.env['product.product'].create({
                'name': 'Sync Test',
            }).id,
            'channel_price': 99.0,
            'channel_qty': 25,
        })
        result = variant.action_sync_to_platform()
        # Should return action to close wizard or True
        self.assertTrue(result)
        mock_connector.update_item.assert_called()

    def test_action_retry_sync(self):
        """Test retry sync updates error fields."""
        variant = self.Variant.create({
            'channel_product_id': self.channel_product.id,
            'odoo_variant_id': self.env['product.product'].create({
                'name': 'Retry Test',
            }).id,
            'sync_state': 'error',
            'last_error': 'Previous error',
        })
        variant.action_retry_sync()
        # Error should be cleared
        self.assertEqual(variant.last_error, False)

    def test_ensure_can_create_on_platform(self):
        """Test validation before creating on platform."""
        variant = self.Variant.create({
            'channel_product_id': self.channel_product.id,
            'odoo_variant_id': self.env['product.product'].create({
                'name': 'Ready Test',
            }).id,
        })
        # Should not raise when valid
        variant.ensure_can_create_on_platform()

    def test_ensure_can_create_requires_price(self):
        """Test create validation requires channel_price."""
        variant = self.Variant.create({
            'channel_product_id': self.channel_product.id,
            'odoo_variant_id': self.env['product.product'].create({
                'name': 'No Price Test',
            }).id,
            'channel_price': 0.0,  # No price
        })
        # Should raise ValidationError
        with self.assertRaises(Exception):
            variant.ensure_can_create_on_platform()

    def test_get_platform_payload(self):
        """Test payload generation for API calls."""
        variant = self.Variant.create({
            'channel_product_id': self.channel_product.id,
            'odoo_variant_id': self.env['product.product'].create({
                'name': 'Payload Test',
            }).id,
            'channel_price': 150.0,
            'channel_qty': 30,
        })
        payload = variant.get_platform_payload()
        self.assertIn('price', payload or {})
        self.assertIn('stock', payload or {})


if __name__ == '__main__':
    unittest.main()
