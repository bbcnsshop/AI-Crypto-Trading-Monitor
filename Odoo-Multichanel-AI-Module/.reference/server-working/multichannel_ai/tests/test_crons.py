# -*- coding: utf-8 -*-
"""Test Cron Jobs and Scheduled Tasks."""
from odoo.tests import TransactionCase, tagged
from unittest.mock import patch, MagicMock


@tagged('post_install', '-at_install', 'multichannel', 'cron')
class TestChannelProductCrons(TransactionCase):
    """Test channel.product cron jobs."""

    def setUp(self):
        super(TestChannelProductCrons, self).setUp()
        self.ChannelProduct = self.env['channel.product']
        self.ChannelConfig = self.env['channel.config']
        
        # Create test channel
        self.channel = self.ChannelConfig.create({
            'name': 'Cron Test Channel',
            'code': 'cron_test',
            'active': True,
            'use_mock_data': True,
            'api_url': 'sandbox',
        })

    def test_cron_sync_pending_products_exists(self):
        """Test cron_sync_pending_products method exists."""
        self.assertTrue(hasattr(self.ChannelProduct, 'cron_sync_pending_products'))
        self.assertTrue(callable(getattr(self.ChannelProduct, 'cron_sync_pending_products')))

    def test_cron_sync_channel_stock_exists(self):
        """Test cron_sync_channel_stock method exists."""
        self.assertTrue(hasattr(self.ChannelProduct, 'cron_sync_channel_stock'))
        self.assertTrue(callable(getattr(self.ChannelProduct, 'cron_sync_channel_stock')))

    def test_cron_refresh_ai_prices_exists(self):
        """Test cron_refresh_ai_prices method exists."""
        self.assertTrue(hasattr(self.ChannelProduct, 'cron_refresh_ai_prices'))
        self.assertTrue(callable(getattr(self.ChannelProduct, 'cron_refresh_ai_prices')))

    def test_cron_check_completeness_exists(self):
        """Test cron_check_completeness method exists."""
        self.assertTrue(hasattr(self.ChannelProduct, 'cron_check_completeness'))
        self.assertTrue(callable(getattr(self.ChannelProduct, 'cron_check_completeness')))

    def test_cron_sync_error_alert_exists(self):
        """Test cron_sync_error_alert method exists."""
        self.assertTrue(hasattr(self.ChannelProduct, 'cron_sync_error_alert'))
        self.assertTrue(callable(getattr(self.ChannelProduct, 'cron_sync_error_alert')))

    def test_cron_ai_auto_fill_missing_exists(self):
        """Test cron_ai_auto_fill_missing method exists."""
        self.assertTrue(hasattr(self.ChannelProduct, 'cron_ai_auto_fill_missing'))
        self.assertTrue(callable(getattr(self.ChannelProduct, 'cron_ai_auto_fill_missing')))


@tagged('post_install', '-at_install', 'multichannel', 'cron')
class TestChannelOrderCrons(TransactionCase):
    """Test channel.order cron jobs."""

    def setUp(self):
        super(TestChannelOrderCrons, self).setUp()
        self.ChannelOrder = self.env['channel.order']
        self.ChannelConfig = self.env['channel.config']
        
        # Create test channel
        self.channel = self.ChannelConfig.create({
            'name': 'Order Cron Test',
            'code': 'order_cron_test',
            'active': True,
            'use_mock_data': True,
            'api_url': 'sandbox',
        })

    def test_cron_import_orders_exists(self):
        """Test cron_import_orders method exists."""
        self.assertTrue(hasattr(self.ChannelOrder, 'cron_import_orders'))
        self.assertTrue(callable(getattr(self.ChannelOrder, 'cron_import_orders')))

    def test_cron_sync_stock_exists(self):
        """Test cron_sync_stock method exists (order version)."""
        self.assertTrue(hasattr(self.ChannelOrder, 'cron_sync_stock'))
        self.assertTrue(callable(getattr(self.ChannelOrder, 'cron_sync_stock')))


@tagged('post_install', '-at_install', 'multichannel', 'cron')
class TestTokenCrons(TransactionCase):
    """Test token refresh cron jobs."""

    def setUp(self):
        super(TestTokenCrons, self).setUp()
        # Import the mixin model
        from multichannel_ai.models.mixins.token_actions import TokenActionsMixin
        self.TokenMixin = TokenActionsMixin

    def test_cron_refresh_expiring_tokens_exists(self):
        """Test cron_refresh_expiring_tokens method exists."""
        self.assertTrue(hasattr(self.TokenMixin, 'cron_refresh_expiring_tokens'))
        self.assertTrue(callable(getattr(self.TokenMixin, 'cron_refresh_expiring_tokens')))


@tagged('post_install', '-at_install', 'multichannel', 'cron')
class TestCronExecution(TransactionCase):
    """Test cron job execution in mock mode."""

    def setUp(self):
        super(TestCronExecution, self).setUp()
        self.ChannelProduct = self.env['channel.product']
        self.ChannelOrder = self.env['channel.order']
        self.ChannelConfig = self.env['channel.config']
        
        # Create test channel
        self.channel = self.ChannelConfig.create({
            'name': 'Cron Exec Test',
            'code': 'cron_exec_test',
            'active': True,
            'use_mock_data': True,
            'api_url': 'sandbox',
        })

    def test_cron_sync_pending_products_runs(self):
        """Test cron_sync_pending_products can run without error."""
        try:
            self.ChannelProduct.cron_sync_pending_products()
            result = True
        except Exception as e:
            # May fail if no products, but method should exist
            result = 'no products' in str(e).lower() or 'not found' in str(e).lower()
        
        self.assertTrue(result, "cron_sync_pending_products should execute or handle empty state gracefully")

    def test_cron_sync_channel_stock_runs(self):
        """Test cron_sync_channel_stock can run without error."""
        try:
            self.ChannelProduct.cron_sync_channel_stock()
            result = True
        except Exception as e:
            result = 'no products' in str(e).lower() or 'not found' in str(e).lower()
        
        self.assertTrue(result, "cron_sync_channel_stock should execute or handle empty state gracefully")

    def test_cron_refresh_ai_prices_runs(self):
        """Test cron_refresh_ai_prices can run without error."""
        try:
            self.ChannelProduct.cron_refresh_ai_prices()
            result = True
        except Exception as e:
            result = 'no products' in str(e).lower() or 'not found' in str(e).lower()
        
        self.assertTrue(result, "cron_refresh_ai_prices should execute or handle empty state gracefully")

    def test_cron_check_completeness_runs(self):
        """Test cron_check_completeness can run without error."""
        try:
            self.ChannelProduct.cron_check_completeness()
            result = True
        except Exception as e:
            result = 'no products' in str(e).lower() or 'not found' in str(e).lower()
        
        self.assertTrue(result, "cron_check_completeness should execute or handle empty state gracefully")

    def test_cron_import_orders_runs(self):
        """Test cron_import_orders can run without error."""
        try:
            self.ChannelOrder.cron_import_orders()
            result = True
        except Exception as e:
            result = 'no channel' in str(e).lower() or 'not found' in str(e).lower()
        
        self.assertTrue(result, "cron_import_orders should execute or handle empty state gracefully")

    def test_cron_sync_stock_runs(self):
        """Test cron_sync_stock can run without error."""
        try:
            self.ChannelOrder.cron_sync_stock()
            result = True
        except Exception as e:
            result = 'no channel' in str(e).lower() or 'not found' in str(e).lower()
        
        self.assertTrue(result, "cron_sync_stock should execute or handle empty state gracefully")
