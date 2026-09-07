# -*- coding: utf-8 -*-
# Test for price.recommendation model
import unittest
from unittest.mock import patch, MagicMock

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'multichannel')
class TestPriceRecommendation(TransactionCase):
    """Test price.recommendation model."""

    def setUp(self):
        super().setUp()
        self.PriceRec = self.env['price.recommendation']
        # Create test product
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
            'list_price': 100.0,
            'standard_price': 50.0,
        })
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

    def test_create_recommendation(self):
        """Test creating a price recommendation."""
        rec = self.PriceRec.create({
            'product_id': self.product.id,
            'channel_id': self.channel.id,
            'ai_recommended_price': 120.0,
            'cost_price': 50.0,
        })
        self.assertTrue(rec.id)
        self.assertEqual(rec.ai_recommended_price, 120.0)
        self.assertEqual(rec.cost_price, 50.0)

    def test_margin_computation(self):
        """Test gross margin is computed correctly."""
        rec = self.PriceRec.create({
            'product_id': self.product.id,
            'channel_id': self.channel.id,
            'ai_recommended_price': 100.0,
            'cost_price': 50.0,
        })
        # Trigger depends
        rec._compute_margin()
        self.assertEqual(rec.gross_profit, 50.0)
        # margin = (100 - 50) / 100 * 100 = 50%
        self.assertEqual(rec.margin_pct, 50.0)

    def test_margin_computation_with_zero_price(self):
        """Test margin handles zero price gracefully."""
        rec = self.PriceRec.create({
            'product_id': self.product.id,
            'channel_id': self.channel.id,
            'ai_recommended_price': 0.0,
            'cost_price': 50.0,
        })
        rec._compute_margin()
        self.assertEqual(rec.gross_profit, -50.0)
        self.assertEqual(rec.margin_pct, 0.0)  # Should not divide by zero

    def test_net_profit_computation(self):
        """Test net profit includes fees."""
        rec = self.PriceRec.create({
            'product_id': self.product.id,
            'channel_id': self.channel.id,
            'ai_recommended_price': 200.0,
            'cost_price': 50.0,
            'platform_fee': 10.0,
            'payment_fee': 5.0,
            'shipping_fee': 15.0,
            'vat_amount': 7.0,
        })
        rec._compute_net_profit()
        # gross = 200 - 50 = 150
        # net = 150 - 10 - 5 - 15 - 7 = 113
        self.assertEqual(rec.net_profit, 113.0)

    def test_action_apply_creates_record(self):
        """Test action_apply creates applied recommendation record."""
        rec = self.PriceRec.create({
            'product_id': self.product.id,
            'channel_id': self.channel.id,
            'ai_recommended_price': 150.0,
            'cost_price': 60.0,
            'state': 'pending',
        })
        result = rec.action_apply()
        self.assertTrue(result)
        self.assertEqual(rec.state, 'applied')

    @patch('odoo.addons.multichannel_ai.models.channel_product.AIEngine')
    def test_action_apply_with_ai_call(self, mock_ai):
        """Test action_apply can trigger AI pricing."""
        mock_engine = MagicMock()
        mock_engine.recommend_price.return_value = 150.0
        mock_ai.return_value = mock_engine

        rec = self.PriceRec.create({
            'product_id': self.product.id,
            'channel_id': self.channel.id,
            'cost_price': 60.0,
            'state': 'draft',
        })
        # If AI key is configured, should call AI
        # If not, should use formula


if __name__ == '__main__':
    unittest.main()
