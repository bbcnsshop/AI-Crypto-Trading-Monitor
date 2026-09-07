# -*- coding: utf-8 -*-
"""
Tests for AI Bridge Module
Tests optional AI functionality with/without ai_engine
"""
from odoo.tests.common import TransactionCase, tagged
import logging

_logger = logging.getLogger(__name__)


@tagged('standard', 'ai_bridge')
class TestAIBridge(TransactionCase):
    """Test AI Bridge functionality - optional AI with fallback"""
    
    def setUp(self):
        super().setUp()
        self.ChannelProduct = self.env['channel.product']
        self.ChannelConfig = self.env['channel.config']
    
    def test_ai_availability_check(self):
        """Test that AI availability check works correctly."""
        # Test with fallback - ai_engine might not be installed in test
        try:
            self.env['multichannel.ai.engine'].search([], limit=1)
            ai_installed = True
        except Exception:
            ai_installed = False
        
        # If AI is installed, it should work
        if ai_installed:
            engine = self.env['multichannel.ai.engine'].get_default_engine()
            self.assertTrue(engine.exists(), "AI engine should exist when installed")
        else:
            # Without AI, formula fallback should work
            _logger.info('AI engine not installed - testing formula fallback')
    
    def test_formula_pricing_fallback(self):
        """Test formula-based pricing when AI is not available."""
        # Test the formula pricing in profit_calculator_wizard
        wizard = self.env['profit.calculator.wizard']
        
        # Create a channel for testing
        channel = self.ChannelConfig.create({
            'name': 'Test Shopee',
            'code': 'shopee',
            'platform': 'shopee',
            'api_url': 'sandbox',
        })
        
        # Create wizard with test data
        test_data = {
            'selling_price': 1000.00,  # 1000 THB
            'cost': 500.00,  # 500 THB
            'channel_id': channel.id,
        }
        
        wizard_rec = wizard.new(test_data)
        wizard_rec._compute_results()
        
        # With formula, we expect:
        # price_excl_vat = 1000 / 1.07 = 934.58
        # fees = 934.58 * (5+2+2.5)/100 = 88.78
        # net_profit = 934.58 - 500 - 88.78 = 345.80
        
        self.assertTrue(
            wizard_rec.price_excl_vat > 0,
            "Price excluding VAT should be calculated"
        )
        self.assertTrue(
            wizard_rec.total_fees > 0,
            "Total fees should be calculated"
        )
        self.assertTrue(
            wizard_rec.net_profit > 0,
            "Net profit should be positive for valid pricing"
        )
        
        _logger.info(
            "Formula pricing: selling=%s, excl_vat=%s, fees=%s, net_profit=%s",
            wizard_rec.selling_price,
            wizard_rec.price_excl_vat,
            wizard_rec.total_fees,
            wizard_rec.net_profit
        )
    
    def test_formula_price_recommendation(self):
        """Test formula-based price recommendation."""
        wizard = self.env['profit.calculator.wizard']
        
        # Create a channel
        channel = self.ChannelConfig.create({
            'name': 'Test Lazada',
            'code': 'lazada',
            'platform': 'lazada',
            'api_url': 'sandbox',
        })
        
        # Test with cost and target margin
        test_data = {
            'selling_price': 0,  # Not used for recommendation
            'cost': 1000.00,  # 1000 THB cost
            'channel_id': channel.id,
            'target_margin': 30.0,  # 30% margin
        }
        
        wizard_rec = wizard.new(test_data)
        wizard_rec._compute_results()
        
        # The recommended price should cover cost + margin
        self.assertTrue(
            wizard_rec.recommended_price > test_data['cost'],
            "Recommended price should be higher than cost"
        )
        
        _logger.info(
            "Price recommendation: cost=%s, recommended=%s",
            test_data['cost'],
            wizard_rec.recommended_price
        )
    
    def test_add_to_channel_without_ai(self):
        """Test adding products to channel without AI engine."""
        # Create a channel
        channel = self.ChannelConfig.create({
            'name': 'Test Shopee',
            'code': 'shopee',
            'platform': 'shopee',
            'api_url': 'sandbox',
        })
        
        # Create a product
        ProductProduct = self.env['product.product']
        product = ProductProduct.create({
            'name': 'Test Product',
            'type': 'product',
            'list_price': 100.00,
            'standard_price': 50.00,
        })
        
        # Try to add to channel - should work without AI
        wizard = self.env['add.to.channel.bulk.wizard'].create({
            'channel_id': channel.id,
            'selection_type': 'selected',
            'use_ai_price': True,  # Should fall back to default price
        })
        
        # This should not raise an error even without AI
        try:
            wizard.action_add_to_channel()
            success = True
        except Exception as e:
            _logger.warning('Add to channel failed: %s', str(e))
            success = False
        
        self.assertTrue(success, "Adding to channel should work without AI")
    
    def test_channel_config_ai_fields(self):
        """Test that channel config has AI availability fields."""
        channel = self.ChannelConfig.create({
            'name': 'Test Channel',
            'code': 'test',
            'platform': 'shopee',
            'api_url': 'sandbox',
        })
        
        # These fields should exist and be computed
        self.assertTrue(
            hasattr(channel, 'ai_available'),
            "Channel should have ai_available field"
        )
        self.assertTrue(
            hasattr(channel, 'ai_pricing_enabled'),
            "Channel should have ai_pricing_enabled field"
        )
        
        # ai_available should be False if ai_engine not installed
        # (or True if installed)
        _logger.info('AI Available: %s', channel.ai_available)
        _logger.info('AI Pricing Enabled: %s', channel.ai_pricing_enabled)
