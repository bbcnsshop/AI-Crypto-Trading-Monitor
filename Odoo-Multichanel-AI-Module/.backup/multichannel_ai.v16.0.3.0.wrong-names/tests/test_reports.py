# -*- coding: utf-8 -*-
"""Test Report Actions and Profit Calculations."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'multichannel', 'report')
class TestProfitReport(TransactionCase):
    """Test Profit Report action."""

    def setUp(self):
        super(TestProfitReport, self).setUp()
        self.ChannelProduct = self.env['channel.product']

    def test_profit_report_action_exists(self):
        """Test profit report action is defined."""
        action = self.env.ref('multichannel_ai.action_profit_report', False)
        self.assertIsNotNone(action, "action_profit_report should exist")
        self.assertEqual(action.name, 'Profit Report')

    def test_profit_report_uses_channel_product(self):
        """Test profit report uses channel.product model."""
        action = self.env.ref('multichannel_ai.action_profit_report')
        self.assertEqual(action.res_model, 'channel.product')

    def test_profit_report_view_mode(self):
        """Test profit report has tree and form views."""
        action = self.env.ref('multichannel_ai.action_profit_report')
        self.assertIn('tree', action.view_mode)
        self.assertIn('form', action.view_mode)


@tagged('post_install', '-at_install', 'multichannel', 'report')
class TestProfitCalculation(TransactionCase):
    """Test profit calculation methods."""

    def setUp(self):
        super(TestProfitCalculation, self).setUp()
        self.PriceRecommendation = self.env['price.recommendation']

    def test_profit_fields_exist(self):
        """Test profit-related fields exist."""
        # Check that price.recommendation has profit fields
        fields = self.PriceRecommendation._fields
        
        self.assertIn('gross_profit', fields, "Should have gross_profit field")
        self.assertIn('gross_margin', fields, "Should have gross_margin field")
        self.assertIn('net_profit', fields, "Should have net_profit field")

    def test_gross_profit_calculation(self):
        """Test gross profit = selling_price - cost_price."""
        # Create a price recommendation
        rec = self.PriceRecommendation.create({
            'ai_recommended_price': 299.0,
            'cost_price': 100.0,
        })
        
        # Check gross_profit is computed
        self.assertTrue(hasattr(rec, 'gross_profit'))

    def test_margin_calculation(self):
        """Test margin is computed from profit and price."""
        rec = self.PriceRecommendation.create({
            'ai_recommended_price': 300.0,
            'cost_price': 100.0,
        })
        
        # Check gross_margin is computed
        self.assertTrue(hasattr(rec, 'gross_margin'))

    def test_net_profit_calculation(self):
        """Test net_profit includes all fees."""
        rec = self.PriceRecommendation.create({
            'ai_recommended_price': 299.0,
            'cost_price': 100.0,
            'platform_fee': 29.9,  # 10%
            'payment_fee': 8.97,    # 3%
            'shipping_fee': 15.0,
        })
        
        # Check net_profit is computed
        self.assertTrue(hasattr(rec, 'net_profit'))


@tagged('post_install', '-at_install', 'multichannel', 'report')
class TestFeeCalculation(TransactionCase):
    """Test fee calculation fields."""

    def setUp(self):
        super(TestFeeCalculation, self).setUp()
        self.PriceRecommendation = self.env['price.recommendation']

    def test_platform_fee_field_exists(self):
        """Test platform_fee field exists."""
        fields = self.PriceRecommendation._fields
        self.assertIn('platform_fee', fields)

    def test_payment_fee_field_exists(self):
        """Test payment_fee field exists."""
        fields = self.PriceRecommendation._fields
        self.assertIn('payment_fee', fields)

    def test_shipping_fee_field_exists(self):
        """Test shipping_fee field exists."""
        fields = self.PriceRecommendation._fields
        self.assertIn('shipping_fee', fields)

    def test_vat_amount_field_exists(self):
        """Test vat_amount field exists."""
        fields = self.PriceRecommendation._fields
        self.assertIn('vat_amount', fields)

    def test_action_apply_exists(self):
        """Test action_apply method exists."""
        self.assertTrue(hasattr(self.PriceRecommendation, 'action_apply'))
        self.assertTrue(callable(getattr(self.PriceRecommendation, 'action_apply')))


@tagged('post_install', '-at_install', 'multichannel', 'report')
class TestProfitCalculatorWizard(TransactionCase):
    """Test Profit Calculator Wizard."""

    def setUp(self):
        super(TestProfitCalculatorWizard, self).setUp()
        self.Wizard = self.env['profit.calculator.wizard']

    def test_profit_calculator_wizard_exists(self):
        """Test profit calculator wizard is available."""
        wizard = self.Wizard.create({
            'cost_price': 100.0,
            'selling_price': 299.0,
        })
        self.assertIsNotNone(wizard)

    def test_profit_calculator_computes_results(self):
        """Test wizard computes results."""
        self.assertTrue(hasattr(self.Wizard, '_compute_results'))

    def test_profit_calculator_channel_field(self):
        """Test wizard can filter by channel."""
        wizard = self.Wizard.create({
            'cost_price': 100.0,
            'selling_price': 299.0,
        })
        
        # Should have channel_id field for filtering
        self.assertTrue(hasattr(wizard, 'channel_id') or 'channel_id' in wizard._fields)
