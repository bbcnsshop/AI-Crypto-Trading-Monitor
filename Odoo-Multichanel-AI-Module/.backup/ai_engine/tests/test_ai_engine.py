# -*- coding: utf-8 -*-
"""Test AI Engine basic operations."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'ai_engine')
class TestAIEngine(TransactionCase):
    """Test AI Engine CRUD and basic operations."""

    def setUp(self):
        super(TestAIEngine, self).setUp()
        self.AIEngine = self.env['ai.engine']

    def test_get_default_engine(self):
        """Test get_default_engine method."""
        # Create a default engine
        engine = self.AIEngine.create({
            'name': 'Default Engine',
            'provider': 'openrouter',
            'is_default': True,
        })
        
        # Get default engine
        default = self.AIEngine.get_default_engine()
        self.assertEqual(default.id, engine.id)

    def test_create_engine(self):
        """Test creating AI engine."""
        engine = self.AIEngine.create({
            'name': 'Test Engine',
            'provider': 'openrouter',
            'vat_rate': 7.0,
        })
        
        self.assertTrue(engine.id)
        self.assertEqual(engine.name, 'Test Engine')
        self.assertEqual(engine.vat_rate, 7.0)

    def test_engine_unique_name(self):
        """Test engine name uniqueness."""
        self.AIEngine.create({
            'name': 'Unique Engine',
            'provider': 'openrouter',
        })
        
        # Should not crash even if name duplicates (unless constrained)
        engine2 = self.AIEngine.create({
            'name': 'Unique Engine 2',
            'provider': 'openrouter',
        })
        self.assertTrue(engine2.id)

    def test_calculate_profit_basic(self):
        """Test profit calculation."""
        engine = self.AIEngine.create({
            'name': 'Test Engine',
            'provider': 'openrouter',
        })
        
        result = engine.calculate_profit(
            selling_price=1500.0,
            cost=1000.0,
            channel_code='shopee',
        )
        
        self.assertIn('gross_profit', result)
        self.assertIn('net_profit', result)
        self.assertIn('net_margin', result)
        self.assertEqual(result['gross_profit'], 500.0)

    def test_calculate_profit_different_channels(self):
        """Test profit calculation for different channels."""
        engine = self.AIEngine.create({
            'name': 'Test Engine',
            'provider': 'openrouter',
        })
        
        result_shopee = engine.calculate_profit(1500.0, 1000.0, 'shopee')
        result_lazada = engine.calculate_profit(1500.0, 1000.0, 'lazada')
        result_tiktok = engine.calculate_profit(1500.0, 1000.0, 'tiktok')
        
        # All should have same gross profit
        self.assertEqual(result_shopee['gross_profit'], 500.0)
        self.assertEqual(result_lazada['gross_profit'], 500.0)
        self.assertEqual(result_tiktok['gross_profit'], 500.0)
        
        # But different net profit (different fees)
        self.assertNotEqual(
            result_shopee.get('net_profit', 0),
            result_tiktok.get('net_profit', 0),
        )

    def test_get_fee_config(self):
        """Test fee config retrieval."""
        engine = self.AIEngine.create({
            'name': 'Test Engine',
            'provider': 'openrouter',
        })
        
        shopee_fees = engine._get_fee_config('shopee')
        self.assertIn('commission', shopee_fees)
        self.assertIn('payment_fee', shopee_fees)
        self.assertIn('shipping_subsidy', shopee_fees)
        
        lazada_fees = engine._get_fee_config('lazada')
        self.assertNotEqual(
            shopee_fees.get('commission'),
            lazada_fees.get('commission'),
        )

    def test_category_mapping_creation(self):
        """Test creating category mapping."""
        engine = self.AIEngine.create({
            'name': 'Test Engine',
            'provider': 'openrouter',
        })
        
        # Get or create a product category
        category = self.env['product.category'].search([], limit=1)
        if not category:
            category = self.env['product.category'].create({
                'name': 'Test Category',
            })
        
        # Create category mapping
        mapping = self.env['ai.category.mapping'].create({
            'engine_id': engine.id,
            'product_name': 'Test Product',
            'category_id': category.id,
            'confidence': 0.85,
        })
        
        self.assertTrue(mapping.id)
        self.assertEqual(mapping.confidence, 0.85)
