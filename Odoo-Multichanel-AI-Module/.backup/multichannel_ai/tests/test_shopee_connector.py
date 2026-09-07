# -*- coding: utf-8 -*-
"""Test Shopee Connector methods."""
from odoo.tests import TransactionCase, tagged
from unittest.mock import patch, MagicMock


@tagged('post_install', '-at_install', 'multichannel', 'connector', 'shopee')
class TestShopeeConnector(TransactionCase):
    """Test Shopee API Connector."""

    def setUp(self):
        super(TestShopeeConnector, self).setUp()
        self.ChannelConfig = self.env['channel.config']
        
        # Create test channel with mock mode
        self.channel_shopee = self.ChannelConfig.create({
            'name': 'Shopee Test Channel',
            'code': 'shopee_test',
            'active': True,
            'use_mock_data': True,
            'api_url': 'sandbox',
            'api_key': 'test_partner_id',
            'api_secret': 'test_secret',
            'access_token': 'test_token',
            'refresh_token': 'test_refresh',
        })

    def test_shopee_connector_import(self):
        """Test Shopee connector can be imported."""
        from multichannel_ai.models.connectors.shopee import ShopeeConnector
        self.assertTrue(ShopeeConnector is not None)
        self.assertEqual(ShopeeConnector.PLATFORM_CODE, 'shopee')

    def test_shopee_connector_init(self):
        """Test Shopee connector initialization."""
        from multichannel_ai.models.connectors.shopee import ShopeeConnector
        
        connector = ShopeeConnector(self.channel_shopee)
        self.assertIsNotNone(connector)
        self.assertEqual(connector.PLATFORM_CODE, 'shopee')

    def test_is_mock_mode_true(self):
        """Test mock mode detection when api_url is sandbox."""
        from multichannel_ai.models.connectors.shopee import ShopeeConnector
        
        connector = ShopeeConnector(self.channel_shopee)
        self.assertTrue(connector._is_mock_mode())

    def test_is_mock_mode_false(self):
        """Test mock mode detection when api_url is production."""
        self.channel_shopee.api_url = 'https://partner.shopeemobile.com/api/v1'
        from multichannel_ai.models.connectors.shopee import ShopeeConnector
        
        connector = ShopeeConnector(self.channel_shopee)
        self.assertFalse(connector._is_mock_mode())

    def test_generate_shopee_signature(self):
        """Test Shopee signature generation."""
        from multichannel_ai.models.connectors.shopee import ShopeeConnector
        
        connector = ShopeeConnector(self.channel_shopee)
        
        # Test signature generation
        path = '/api/v1/product/add_item'
        signature = connector._generate_shopee_signature(path)
        
        # Signature should be hex string
        self.assertIsInstance(signature, str)
        self.assertEqual(len(signature), 64)  # SHA256 hex = 64 chars

    def test_get_shopee_headers(self):
        """Test Shopee headers generation."""
        from multichannel_ai.models.connectors.shopee import ShopeeConnector
        
        connector = ShopeeConnector(self.channel_shopee)
        headers = connector._get_shopee_headers()
        
        self.assertIn('Content-Type', headers)
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertIn('Accept', headers)
        self.assertIn('Authorization', headers)

    def test_refresh_access_token_mock(self):
        """Test refresh token in mock mode."""
        from multichannel_ai.models.connectors.shopee import ShopeeConnector
        
        connector = ShopeeConnector(self.channel_shopee)
        result = connector.refresh_access_token()
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_upload_image_mock(self):
        """Test image upload in mock mode."""
        from multichannel_ai.models.connectors.shopee import ShopeeConnector
        
        connector = ShopeeConnector(self.channel_shopee)
        
        # Mock image data
        image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00'
        
        result = connector.upload_image(image_data, 'test.png', product_id=12345)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_create_item_mock(self):
        """Test create item in mock mode."""
        from multichannel_ai.models.connectors.shopee import ShopeeConnector
        
        connector = ShopeeConnector(self.channel_shopee)
        
        product_data = {
            'name': 'Test Product',
            'price': 299.00,
            'stock': 100,
            'category_id': 1,
        }
        
        result = connector.create_item(product_data)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_update_item_mock(self):
        """Test update item in mock mode."""
        from multichannel_ai.models.connectors.shopee import ShopeeConnector
        
        connector = ShopeeConnector(self.channel_shopee)
        
        product_data = {
            'name': 'Updated Product',
            'price': 349.00,
        }
        
        result = connector.update_item(12345, product_data)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_get_products_mock(self):
        """Test get products in mock mode."""
        from multichannel_ai.models.connectors.shopee import ShopeeConnector
        
        connector = ShopeeConnector(self.channel_shopee)
        result = connector.get_products(page=1, limit=10)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn('products', result)

    def test_update_stock_mock(self):
        """Test update stock in mock mode."""
        from multichannel_ai.models.connectors.shopee import ShopeeConnector
        
        connector = ShopeeConnector(self.channel_shopee)
        result = connector.update_stock(12345, 50)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_update_price_mock(self):
        """Test update price in mock mode."""
        from multichannel_ai.models.connectors.shopee import ShopeeConnector
        
        connector = ShopeeConnector(self.channel_shopee)
        result = connector.update_price(12345, 399.00)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_get_orders_mock(self):
        """Test get orders in mock mode."""
        from multichannel_ai.models.connectors.shopee import ShopeeConnector
        
        connector = ShopeeConnector(self.channel_shopee)
        result = connector.get_orders(page=1, limit=10)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_get_order_detail_mock(self):
        """Test get order detail in mock mode."""
        from multichannel_ai.models.connectors.shopee import ShopeeConnector
        
        connector = ShopeeConnector(self.channel_shopee)
        result = connector.get_order_detail(12345)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_get_logistics_mock(self):
        """Test get logistics in mock mode."""
        from multichannel_ai.models.connectors.shopee import ShopeeConnector
        
        connector = ShopeeConnector(self.channel_shopee)
        result = connector.get_logistics()
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, (dict, list))

    def test_create_shipment_mock(self):
        """Test create shipment in mock mode."""
        from multichannel_ai.models.connectors.shopee import ShopeeConnector
        
        connector = ShopeeConnector(self.channel_shopee)
        result = connector.create_shipment(12345, logistics_id=1, tracking_number='TEST123')
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
