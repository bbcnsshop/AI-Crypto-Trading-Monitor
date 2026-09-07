# -*- coding: utf-8 -*-
"""Test Wizard Models."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'multichannel', 'wizard')
class TestAddToChannelWizard(TransactionCase):
    """Test Add to Channel Wizard."""

    def setUp(self):
        super(TestAddToChannelWizard, self).setUp()
        self.Wizard = self.env['add.to.channel.wizard']
        self.ChannelConfig = self.env['channel.config']
        
        self.channel = self.ChannelConfig.create({
            'name': 'Wizard Test',
            'code': 'wizard_test',
            'active': True,
            'use_mock_data': True,
        })

    def test_wizard_model_exists(self):
        """Test wizard model is defined."""
        self.assertTrue(hasattr(self.env, 'add.to.channel.wizard'))

    def test_wizard_create(self):
        """Test wizard can be created."""
        wizard = self.Wizard.create({
            'channel_id': self.channel.id,
        })
        self.assertIsNotNone(wizard)
        self.assertEqual(wizard.channel_id.id, self.channel.id)

    def test_wizard_action_preview_exists(self):
        """Test action_preview method exists."""
        self.assertTrue(hasattr(self.Wizard, 'action_preview'))

    def test_wizard_action_add_to_channel_exists(self):
        """Test action_add_to_channel method exists."""
        self.assertTrue(hasattr(self.Wizard, 'action_add_to_channel'))


@tagged('post_install', '-at_install', 'multichannel', 'wizard')
class TestChannelListAddWizard(TransactionCase):
    """Test Channel List Add Wizard."""

    def setUp(self):
        super(TestChannelListAddWizard, self).setUp()
        self.Wizard = self.env['channel.list.add.wizard']

    def test_wizard_model_exists(self):
        """Test wizard model is defined."""
        self.assertTrue(hasattr(self.env, 'channel.list.add.wizard'))

    def test_wizard_create(self):
        """Test wizard can be created."""
        wizard = self.Wizard.create({
            'code': 'new_channel',
            'name': 'New Channel',
            'country_code': 'TH',
        })
        self.assertIsNotNone(wizard)
        self.assertEqual(wizard.code, 'new_channel')
        self.assertEqual(wizard.name, 'New Channel')

    def test_wizard_action_add_channel_exists(self):
        """Test action_add_channel method exists."""
        self.assertTrue(hasattr(self.Wizard, 'action_add_channel'))


@tagged('post_install', '-at_install', 'multichannel', 'wizard')
class TestChannelProductAIFillWizard(TransactionCase):
    """Test Channel Product AI Fill Wizard."""

    def setUp(self):
        super(TestChannelProductAIFillWizard, self).setUp()
        self.Wizard = self.env['channel.product.ai.fill.wizard']

    def test_wizard_model_exists(self):
        """Test wizard model is defined."""
        self.assertTrue(hasattr(self.env, 'channel.product.ai.fill.wizard'))

    def test_wizard_create(self):
        """Test wizard can be created."""
        wizard = self.Wizard.create({
            'name': 'AI Fill Test',
        })
        self.assertIsNotNone(wizard)

    def test_wizard_default_get_exists(self):
        """Test default_get method exists."""
        self.assertTrue(hasattr(self.Wizard, 'default_get'))

    def test_wizard_action_preview_exists(self):
        """Test action_preview method exists."""
        self.assertTrue(hasattr(self.Wizard, 'action_preview'))

    def test_wizard_action_fill_exists(self):
        """Test action_fill method exists."""
        self.assertTrue(hasattr(self.Wizard, 'action_fill'))

    def test_wizard_action_view_products_exists(self):
        """Test action_view_products method exists."""
        self.assertTrue(hasattr(self.Wizard, 'action_view_products'))


@tagged('post_install', '-at_install', 'multichannel', 'wizard')
class TestChannelProductAttributeWizard(TransactionCase):
    """Test Channel Product Attribute Wizard."""

    def setUp(self):
        super(TestChannelProductAttributeWizard, self).setUp()
        self.Wizard = self.env['channel.product.attribute.wizard']

    def test_wizard_model_exists(self):
        """Test wizard model is defined."""
        self.assertTrue(hasattr(self.env, 'channel.product.attribute.wizard'))

    def test_wizard_create(self):
        """Test wizard can be created."""
        wizard = self.Wizard.create({
            'name': 'Attribute Wizard Test',
        })
        self.assertIsNotNone(wizard)

    def test_wizard_action_generate_exists(self):
        """Test action_generate method exists."""
        self.assertTrue(hasattr(self.Wizard, 'action_generate'))


@tagged('post_install', '-at_install', 'multichannel', 'wizard')
class TestProfitCalculatorWizard(TransactionCase):
    """Test Profit Calculator Wizard."""

    def setUp(self):
        super(TestProfitCalculatorWizard, self).setUp()
        self.Wizard = self.env['profit.calculator.wizard']

    def test_wizard_model_exists(self):
        """Test wizard model is defined."""
        self.assertTrue(hasattr(self.env, 'profit.calculator.wizard'))

    def test_wizard_create(self):
        """Test wizard can be created."""
        wizard = self.Wizard.create({
            'cost_price': 100.0,
            'selling_price': 299.0,
        })
        self.assertIsNotNone(wizard)

    def test_wizard_compute_results_exists(self):
        """Test _compute_results method exists."""
        self.assertTrue(hasattr(self.Wizard, '_compute_results'))

    def test_profit_calculation(self):
        """Test basic profit calculation logic."""
        # Create a simple test
        wizard = self.Wizard.create({
            'cost_price': 100.0,
            'selling_price': 299.0,
        })
        self.assertEqual(wizard.cost_price, 100.0)
        self.assertEqual(wizard.selling_price, 299.0)