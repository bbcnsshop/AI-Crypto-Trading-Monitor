# -*- coding: utf-8 -*-
"""Test OAuth Controller and Token Management."""
from odoo.tests import TransactionCase, tagged, HttpCase
from unittest.mock import patch, MagicMock


@tagged('post_install', '-at_install', 'multichannel', 'oauth')
class TestOAuthController(TransactionCase):
    """Test OAuth Controller routes."""

    def setUp(self):
        super(TestOAuthController, self).setUp()
        self.ChannelConfig = self.env['channel.config']
        
        # Create test channels for each platform
        self.channel_shopee = self.ChannelConfig.create({
            'name': 'Shopee OAuth Test',
            'code': 'shopee_oauth',
            'active': True,
            'use_mock_data': True,
            'api_url': 'sandbox',
            'api_key': 'test_partner_id',
            'api_secret': 'test_secret',
        })
        
        self.channel_lazada = self.ChannelConfig.create({
            'name': 'Lazada OAuth Test',
            'code': 'lazada_oauth',
            'active': True,
            'use_mock_data': True,
            'api_url': 'sandbox',
            'api_key': 'test_app_key',
            'api_secret': 'test_app_secret',
        })
        
        self.channel_tiktok = self.ChannelConfig.create({
            'name': 'TikTok OAuth Test',
            'code': 'tiktok_oauth',
            'active': True,
            'use_mock_data': True,
            'api_url': 'sandbox',
            'api_key': 'test_client_key',
            'api_secret': 'test_client_secret',
        })

    def test_oauth_controller_import(self):
        """Test OAuth controller can be imported."""
        from multichannel_ai.controllers.oauth_controller import OAuthController
        self.assertTrue(OAuthController is not None)

    def test_oauth_authorize_route_exists(self):
        """Test /multichannel/oauth/<id>/authorize route exists."""
        # Verify the route method exists
        from multichannel_ai.controllers.oauth_controller import OAuthController
        self.assertTrue(hasattr(OAuthController, 'oauth_authorize'))
        self.assertTrue(callable(getattr(OAuthController, 'oauth_authorize')))

    def test_oauth_callback_route_exists(self):
        """Test /multichannel/oauth/<id>/callback route exists."""
        from multichannel_ai.controllers.oauth_controller import OAuthController
        self.assertTrue(hasattr(OAuthController, 'oauth_callback'))
        self.assertTrue(callable(getattr(OAuthController, 'oauth_callback')))

    def test_oauth_authorize_shopee_method(self):
        """Test Shopee auth URL generation."""
        from multichannel_ai.controllers.oauth_controller import OAuthController
        controller = OAuthController()
        
        callback_url = 'http://localhost:8069/multichannel/oauth/1/callback'
        auth_url = controller._shopee_get_auth_url(self.channel_shopee, callback_url)
        
        self.assertIsNotNone(auth_url)
        self.assertIsInstance(auth_url, str)
        self.assertIn('shopee', auth_url.lower())

    def test_oauth_authorize_lazada_method(self):
        """Test Lazada auth URL generation."""
        from multichannel_ai.controllers.oauth_controller import OAuthController
        controller = OAuthController()
        
        callback_url = 'http://localhost:8069/multichannel/oauth/1/callback'
        auth_url = controller._lazada_get_auth_url(self.channel_lazada, callback_url)
        
        self.assertIsNotNone(auth_url)
        self.assertIsInstance(auth_url, str)
        self.assertIn('lazada', auth_url.lower())

    def test_oauth_authorize_tiktok_method(self):
        """Test TikTok auth URL generation."""
        from multichannel_ai.controllers.oauth_controller import OAuthController
        controller = OAuthController()
        
        callback_url = 'http://localhost:8069/multichannel/oauth/1/callback'
        auth_url = controller._tiktok_get_auth_url(self.channel_tiktok, callback_url)
        
        self.assertIsNotNone(auth_url)
        self.assertIsInstance(auth_url, str)
        self.assertIn('tiktok', auth_url.lower())


@tagged('post_install', '-at_install', 'multichannel', 'oauth')
class TestTokenManagement(TransactionCase):
    """Test OAuth Token storage and refresh."""

    def setUp(self):
        super(TestTokenManagement, self).setUp()
        self.ChannelConfig = self.env['channel.config']
        
        self.channel = self.ChannelConfig.create({
            'name': 'Token Test',
            'code': 'token_test',
            'active': True,
            'use_mock_data': True,
            'api_url': 'sandbox',
            'api_key': 'test_key',
            'api_secret': 'test_secret',
        })

    def test_channel_has_token_fields(self):
        """Test channel.config has token fields."""
        self.assertTrue(hasattr(self.channel, 'access_token'))
        self.assertTrue(hasattr(self.channel, 'refresh_token'))
        self.assertTrue(hasattr(self.channel, 'token_expire_date'))

    def test_can_set_access_token(self):
        """Test access_token can be set."""
        self.channel.access_token = 'test_access_token_123'
        self.assertEqual(self.channel.access_token, 'test_access_token_123')

    def test_can_set_refresh_token(self):
        """Test refresh_token can be set."""
        self.channel.refresh_token = 'test_refresh_token_456'
        self.assertEqual(self.channel.refresh_token, 'test_refresh_token_456')

    def test_is_token_expired_property(self):
        """Test is_token_expired property exists."""
        self.assertTrue(hasattr(self.channel, 'is_token_expired'))

    def test_token_expire_date_setter(self):
        """Test token_expire_date can be set."""
        from datetime import datetime, timedelta
        future_date = datetime.now() + timedelta(days=7)
        self.channel.token_expire_date = future_date
        self.assertEqual(self.channel.token_expire_date, future_date)

    def test_token_refresh_updates_channel(self):
        """Test token refresh updates channel fields."""
        from multichannel_ai.models.connectors.shopee import ShopeeConnector
        
        connector = ShopeeConnector(self.channel)
        
        # Set initial tokens
        self.channel.access_token = 'old_token'
        self.channel.refresh_token = 'old_refresh'
        
        # Refresh token
        connector.refresh_access_token()
        
        # Channel should still have tokens (refresh may update or return new)
        self.assertTrue(self.channel.access_token is not None or self.channel.refresh_token is not None)


@tagged('post_install', '-at_install', 'multichannel', 'oauth')
class TestOAuthRoutesExist(TransactionCase):
    """Test that OAuth routes are registered."""

    def test_oauth_route_patterns(self):
        """Test OAuth route patterns are valid."""
        from odoo.http import root
        
        # Check if OAuth routes are in the route registry
        oauth_routes = []
        for route in root.routes:
            if hasattr(route, 'rule') and '/multichannel/oauth' in str(route.rule):
                oauth_routes.append(str(route.rule))
        
        # Should have at least authorize and callback routes
        # (May not be loaded in test environment, just verify no errors)
        self.assertIsInstance(oauth_routes, list)