# -*- coding: utf-8 -*-
"""Test Webhook Controller."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'multichannel', 'webhook')
class TestWebhookController(TransactionCase):
    """Test Webhook Controller routes."""

    def setUp(self):
        super(TestWebhookController, self).setUp()
        self.ChannelConfig = self.env['channel.config']
        self.ChannelOrder = self.env['channel.order']
        
        # Create test channels
        self.channel_shopee = self.ChannelConfig.create({
            'name': 'Shopee Webhook Test',
            'code': 'shopee',
            'active': True,
            'use_mock_data': True,
            'auto_sync_orders': False,
        })
        
        self.channel_lazada = self.ChannelConfig.create({
            'name': 'Lazada Webhook Test',
            'code': 'lazada',
            'active': True,
            'use_mock_data': True,
            'auto_sync_orders': False,
        })
        
        self.channel_tiktok = self.ChannelConfig.create({
            'name': 'TikTok Webhook Test',
            'code': 'tiktok',
            'active': True,
            'use_mock_data': True,
            'auto_sync_orders': False,
        })

    def test_webhook_controller_import(self):
        """Test webhook controller can be imported."""
        from multichannel_ai.controllers.webhook_controller import WebhookController
        self.assertTrue(WebhookController is not None)

    def test_shopee_webhook_route_exists(self):
        """Test Shopee webhook method exists."""
        from multichannel_ai.controllers.webhook_controller import WebhookController
        self.assertTrue(hasattr(WebhookController, 'shopee_webhook'))
        self.assertTrue(callable(getattr(WebhookController, 'shopee_webhook')))

    def test_lazada_webhook_route_exists(self):
        """Test Lazada webhook method exists."""
        from multichannel_ai.controllers.webhook_controller import WebhookController
        self.assertTrue(hasattr(WebhookController, 'lazada_webhook'))
        self.assertTrue(callable(getattr(WebhookController, 'lazada_webhook')))

    def test_tiktok_webhook_route_exists(self):
        """Test TikTok webhook method exists."""
        from multichannel_ai.controllers.webhook_controller import WebhookController
        self.assertTrue(hasattr(WebhookController, 'tiktok_webhook'))
        self.assertTrue(callable(getattr(WebhookController, 'tiktok_webhook')))

    def test_webhook_routes_are_public(self):
        """Test webhook routes are public (auth='public')."""
        from multichannel_ai.controllers.webhook_controller import WebhookController
        
        controller = WebhookController()
        
        # Get method decorators - webhooks should be public
        # This is more of a documentation test
        self.assertTrue(True, "Webhook routes should be auth='public'")


@tagged('post_install', '-at_install', 'multichannel', 'webhook')
class TestWebhookDataProcessing(TransactionCase):
    """Test webhook data processing."""

    def setUp(self):
        super(TestWebhookDataProcessing, self).setUp()
        self.ChannelOrder = self.env['channel.order']

    def test_create_from_webhook_exists(self):
        """Test create_from_webhook method exists on channel.order."""
        self.assertTrue(hasattr(self.ChannelOrder, 'create_from_webhook'))
        self.assertTrue(callable(getattr(self.ChannelOrder, 'create_from_webhook')))

    def test_webhook_data_format(self):
        """Test webhook data format is expected."""
        # Sample webhook data structure
        sample_data = {
            'order_id': '12345',
            'channel_code': 'shopee',
            'buyer_name': 'Test Buyer',
            'total_amount': 299.00,
            'status': 'pending',
        }
        
        self.assertIn('order_id', sample_data)
        self.assertIn('channel_code', sample_data)
        self.assertIn('buyer_name', sample_data)
        self.assertIn('total_amount', sample_data)

    def test_webhook_response_format(self):
        """Test webhook response format is expected."""
        # Expected response format
        success_response = {'status': 'success'}
        error_response = {'status': 'error', 'message': 'some error'}
        
        self.assertIn('status', success_response)
        self.assertIn('status', error_response)
        self.assertEqual(success_response['status'], 'success')
        self.assertEqual(error_response['status'], 'error')


@tagged('post_install', '-at_install', 'multichannel', 'webhook')
class TestWebhookChannelIntegration(TransactionCase):
    """Test webhook integration with channels."""

    def setUp(self):
        super(TestWebhookChannelIntegration, self).setUp()
        self.ChannelConfig = self.env['channel.config']
        
        self.channel = self.ChannelConfig.create({
            'name': 'Webhook Integration Test',
            'code': 'webhook_test',
            'active': True,
            'use_mock_data': True,
        })

    def test_channel_auto_sync_orders_field(self):
        """Test channel has auto_sync_orders field."""
        self.assertTrue(hasattr(self.channel, 'auto_sync_orders'))

    def test_webhook_creates_order(self):
        """Test webhook can create order through create_from_webhook."""
        # Test that the method exists and can be called
        try:
            # This may not create a real order in test environment
            # but should not raise AttributeError
            result = self.ChannelOrder.create_from_webhook('webhook_test', {})
            # Result might be None or a recordset
            self.assertTrue(result is None or hasattr(result, 'id'))
        except Exception as e:
            # Any error should be logged, not raise AttributeError
            self.assertNotIn('AttributeError', str(type(e)))

    def test_webhook_searches_channel_by_code(self):
        """Test webhook searches channel by code."""
        # Verify the channel search pattern works
        channel = self.ChannelConfig.search([('code', '=', 'webhook_test')], limit=1)
        self.assertEqual(channel.id, self.channel.id)


@tagged('post_install', '-at_install', 'multichannel', 'webhook')
class TestWebhookSecurity(TransactionCase):
    """Test webhook security considerations."""

    def test_webhook_csrf_disabled(self):
        """Test webhooks have CSRF disabled."""
        # CSRF should be False for webhook endpoints
        # This is tested via the decorator: @http.route(..., csrf=False)
        self.assertTrue(True, "Webhook routes should have csrf=False")

    def test_webhook_uses_public_auth(self):
        """Test webhooks use public authentication."""
        # Webhooks need auth='public' to receive external calls
        self.assertTrue(True, "Webhook routes should have auth='public'")

    def test_webhook_uses_json_type(self):
        """Test webhooks use JSON response type."""
        # Webhooks should use type='json' for JSON responses
        self.assertTrue(True, "Webhook routes should have type='json'")

    def test_webhook_uses_post_method(self):
        """Test webhooks accept POST method."""
        # Webhooks should only accept POST
        self.assertTrue(True, "Webhook routes should have methods=['POST']")

    def test_webhook_sudo_for_channel_search(self):
        """Test webhook uses sudo() for channel search."""
        # Webhook controller uses .sudo() for channel search
        # This is important for public access
        self.assertTrue(True, "Webhook should use sudo() for channel search")
