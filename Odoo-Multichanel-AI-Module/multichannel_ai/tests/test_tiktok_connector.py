# -*- coding: utf-8 -*-
"""Test TikTok Connector methods."""
from odoo.tests import TransactionCase, tagged
from unittest.mock import patch, MagicMock


@tagged('post_install', '-at_install', 'multichannel', 'connector', 'tiktok')
class TestTikTokConnector(TransactionCase):
    """Test TikTok Shop API Connector."""

    def setUp(self):
        super(TestTikTokConnector, self).setUp()
        self.ChannelConfig = self.env['channel.config']
        
        # Create test channel with mock mode
        self.channel_tiktok = self.ChannelConfig.create({
            'name': 'TikTok Test Channel',
            'code': 'tiktok_test',
            'active': True,
            'use_mock_data': True,
            'api_url': 'sandbox',
            'api_key': 'test_client_key',
            'api_secret': 'test_client_secret',
            'access_token': 'test_token',
            'refresh_token': 'test_refresh',
        })

    def test_tiktok_connector_import(self):
        """Test TikTok connector can be imported."""
        from multichannel_ai.models.connectors.tiktok import TikTokConnector
        self.assertTrue(TikTokConnector is not None)
        self.assertEqual(TikTokConnector.PLATFORM_CODE, 'tiktok')

    def test_tiktok_connector_init(self):
        """Test TikTok connector initialization."""
        from multichannel_ai.models.connectors.tiktok import TikTokConnector
        
        connector = TikTokConnector(self.channel_tiktok)
        self.assertIsNotNone(connector)
        self.assertEqual(connector.PLATFORM_CODE, 'tiktok')

    def test_is_mock_mode_true(self):
        """Test mock mode detection when api_url is sandbox."""
        from multichannel_ai.models.connectors.tiktok import TikTokConnector
        
        connector = TikTokConnector(self.channel_tiktok)
        self.assertTrue(connector._is_mock_mode())

    def test_is_mock_mode_false(self):
        """Test mock mode detection when api_url is production."""
        self.channel_tiktok.api_url = 'https://open.tiktokapis.com/v2'
        from multichannel_ai.models.connectors.tiktok import TikTokConnector
        
        connector = TikTokConnector(self.channel_tiktok)
        self.assertFalse(connector._is_mock_mode())

    def test_get_tiktok_headers(self):
        """Test TikTok headers generation."""
        from multichannel_ai.models.connectors.tiktok import TikTokConnector
        
        connector = TikTokConnector(self.channel_tiktok)
        headers = connector._get_tiktok_headers()
        
        self.assertIn('Content-Type', headers)
        self.assertIn('Authorization', headers)

    def test_refresh_access_token_mock(self):
        """Test refresh token in mock mode."""
        from multichannel_ai.models.connectors.tiktok import TikTokConnector
        
        connector = TikTokConnector(self.channel_tiktok)
        result = connector.refresh_access_token()
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_upload_image_mock(self):
        """Test image upload in mock mode."""
        from multichannel_ai.models.connectors.tiktok import TikTokConnector
        
        connector = TikTokConnector(self.channel_tiktok)
        
        # Mock image data
        image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00'
        
        result = connector.upload_image(image_data, 'test.png', product_id=12345)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_create_item_mock(self):
        """Test create item in mock mode."""
        from multichannel_ai.models.connectors.tiktok import TikTokConnector
        
        connector = TikTokConnector(self.channel_tiktok)
        
        product_data = {
            'name': 'Test Product',
            'price': 299.00,
            'stock': 100,
        }
        
        result = connector.create_item(product_data)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_update_item_mock(self):
        """Test update item in mock mode."""
        from multichannel_ai.models.connectors.tiktok import TikTokConnector
        
        connector = TikTokConnector(self.channel_tiktok)
        
        product_data = {
            'name': 'Updated Product',
            'price': 349.00,
        }
        
        result = connector.update_item(12345, product_data)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_get_products_mock(self):
        """Test get products in mock mode."""
        from multichannel_ai.models.connectors.tiktok import TikTokConnector
        
        connector = TikTokConnector(self.channel_tiktok)
        result = connector.get_products(page=1, limit=10)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_update_stock_mock(self):
        """Test update stock in mock mode."""
        from multichannel_ai.models.connectors.tiktok import TikTokConnector
        
        connector = TikTokConnector(self.channel_tiktok)
        result = connector.update_stock(12345, 50)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_update_price_mock(self):
        """Test update price in mock mode."""
        from multichannel_ai.models.connectors.tiktok import TikTokConnector
        
        connector = TikTokConnector(self.channel_tiktok)
        result = connector.update_price(12345, 399.00)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_get_orders_mock(self):
        """Test get orders in mock mode."""
        from multichannel_ai.models.connectors.tiktok import TikTokConnector
        
        connector = TikTokConnector(self.channel_tiktok)
        result = connector.get_orders(page=1, limit=10)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_get_order_detail_mock(self):
        """Test get order detail in mock mode."""
        from multichannel_ai.models.connectors.tiktok import TikTokConnector
        
        connector = TikTokConnector(self.channel_tiktok)
        result = connector.get_order_detail(12345)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_get_logistics_mock(self):
        """Test get logistics in mock mode."""
        from multichannel_ai.models.connectors.tiktok import TikTokConnector
        
        connector = TikTokConnector(self.channel_tiktok)
        result = connector.get_logistics()
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, (dict, list))

    def test_create_shipment_mock(self):
        """Test create shipment in mock mode."""
        from multichannel_ai.models.connectors.tiktok import TikTokConnector
        
        connector = TikTokConnector(self.channel_tiktok)
        result = connector.create_shipment(12345, logistics_id=1, tracking_number='TEST123')
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
