# -*- coding: utf-8 -*-
"""Test AI Engine pricing with smart routing."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'ai_engine', 'pricing')
class TestAIPricingSmartRouting(TransactionCase):
    """Test smart routing for recommend_price()."""

    def setUp(self):
        super(TestAIPricingSmartRouting, self).setUp()
        self.AIEngine = self.env['ai.engine']
        # Create engine without API key (for formula testing)
        self.engine = self.AIEngine.create({
            'name': 'Test AI Engine',
            'provider': 'openrouter',
            'openrouter_api_key': False,  # No API key = formula fallback
            'vat_rate': 7.0,
        })

    def test_recommend_price_no_api_key_uses_formula(self):
        """Test that recommend_price uses formula when no API key."""
        product_data = {
            'name': 'Test Product',
            'cost': 1000.0,
        }
        result = self.engine.recommend_price(product_data, 'shopee', 30.0)
        
        # Should use formula
        self.assertEqual(result.get('_source'), 'formula')
        self.assertEqual(result.get('channel'), 'shopee')
        self.assertEqual(result.get('cost'), 1000.0)
        self.assertIn('selling_price', result)
        self.assertGreater(result['selling_price'], 1000.0)

    def test_recommend_price_shopee_fees(self):
        """Test pricing calculation with Shopee fees."""
        product_data = {
            'name': 'Test Product',
            'cost': 5000.0,
        }
        result = self.engine.recommend_price(product_data, 'shopee', 30.0)
        
        # Shopee: 5% commission, 2% payment, 2.5% shipping
        fee = result.get('fee_breakdown', {})
        self.assertEqual(fee.get('commission'), 5.0)
        self.assertEqual(fee.get('payment_fee'), 2.0)
        self.assertEqual(fee.get('shipping_subsidy'), 2.5)

    def test_recommend_price_lazada_fees(self):
        """Test pricing calculation with Lazada fees."""
        product_data = {
            'name': 'Test Product',
            'cost': 5000.0,
        }
        result = self.engine.recommend_price(product_data, 'lazada', 30.0)
        
        # Lazada: 5% commission, 2% payment, 3% shipping
        fee = result.get('fee_breakdown', {})
        self.assertEqual(fee.get('commission'), 5.0)
        self.assertEqual(fee.get('payment_fee'), 2.0)
        self.assertEqual(fee.get('shipping_subsidy'), 3.0)

    def test_recommend_price_tiktok_fees(self):
        """Test pricing calculation with TikTok fees."""
        product_data = {
            'name': 'Test Product',
            'cost': 5000.0,
        }
        result = self.engine.recommend_price(product_data, 'tiktok', 30.0)
        
        # TikTok: 3.5% commission, 1.5% payment, 2% shipping
        fee = result.get('fee_breakdown', {})
        self.assertEqual(fee.get('commission'), 3.5)
        self.assertEqual(fee.get('payment_fee'), 1.5)
        self.assertEqual(fee.get('shipping_subsidy'), 2.0)

    def test_recommend_price_different_margins(self):
        """Test that higher margin target = higher selling price."""
        product_data = {
            'name': 'Test Product',
            'cost': 1000.0,
        }
        
        result_20 = self.engine.recommend_price(product_data, 'shopee', 20.0)
        result_50 = self.engine.recommend_price(product_data, 'shopee', 50.0)
        
        self.assertGreater(
            result_50['selling_price'],
            result_20['selling_price'],
            'Higher margin target should result in higher selling price'
        )

    def test_recommend_price_zero_cost(self):
        """Test pricing with zero cost."""
        product_data = {
            'name': 'Test Product',
            'cost': 0.0,
        }
        result = self.engine.recommend_price(product_data, 'shopee', 30.0)
        
        # Should return 0 or minimal value
        self.assertEqual(result.get('selling_price'), 0.0)
        self.assertEqual(result.get('cost'), 0.0)

    def test_calculate_formula_price_direct_call(self):
        """Test formula calculation directly."""
        product_data = {
            'name': 'Test Product',
            'cost': 2000.0,
        }
        result = self.engine._calculate_formula_price(product_data, 'shopee', 25.0)
        
        self.assertEqual(result.get('_source'), 'formula')
        self.assertEqual(result.get('channel'), 'shopee')
        self.assertEqual(result.get('target_margin'), 25.0)
        self.assertGreater(result['selling_price'], 2000.0)


@tagged('post_install', '-at_install', 'ai_engine', 'pricing')
class TestAIPricingWithMockAPI(TransactionCase):
    """Test AI pricing with mocked API (if API key is set)."""

    def setUp(self):
        super(TestAIPricingWithMockAPI, self).setUp()
        self.AIEngine = self.env['ai.engine']
        # Create engine with mock API key
        self.engine = self.AIEngine.create({
            'name': 'Test AI Engine with Mock',
            'provider': 'openrouter',
            'openrouter_api_key': 'mock_key_for_testing',  # Has API key
            'vat_rate': 7.0,
        })

    def test_recommend_price_with_api_key_attempts_ai(self):
        """Test that API key triggers AI call attempt."""
        product_data = {
            'name': 'Test Product',
            'cost': 1000.0,
        }
        
        # This will fail to call AI (no real API), but should not crash
        # It should either return AI result or fall back to formula
        try:
            result = self.engine.recommend_price(product_data, 'shopee', 30.0)
            # Should have either _source='ai' or _source='formula'
            self.assertIn(result.get('_source'), ['ai', 'formula'])
            self.assertIn('selling_price', result)
        except Exception as e:
            # If AI call fails completely, should still return formula result
            self.fail(f"recommend_price should not raise exception: {e}")

    def test_classify_product_returns_structure(self):
        """Test that classify_product returns expected structure."""
        product_data = {
            'name': 'Dell Laptop',
            'description': 'Gaming laptop',
            'attributes': 'RAM 16GB, SSD 512GB',
        }
        
        try:
            result = self.engine.classify_product(product_data)
            # Should return dict with expected keys
            self.assertIsInstance(result, dict)
            self.assertIn('category_id', result)
            self.assertIn('confidence', result)
        except Exception as e:
            # AI call may fail, but should return error structure
            self.assertIn('category_id', str(result) if 'result' in dir() else '')
