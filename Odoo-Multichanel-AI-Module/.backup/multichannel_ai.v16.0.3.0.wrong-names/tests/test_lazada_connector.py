# -*- coding: utf-8 -*-
"""Test Lazada Connector methods."""
from odoo.tests import TransactionCase, tagged
from unittest.mock import patch, MagicMock


@tagged('post_install', '-at_install', 'multichannel', 'connector', 'lazada')
class TestLazadaConnector(TransactionCase):
    """Test Lazada API Connector."""

    def setUp(self):
        super(TestLazadaConnector, self).setUp()
        self.ChannelConfig = self.env['channel.config']
        
        # Create test channel with mock mode
        self.channel_lazada = self.ChannelConfig.create({
            'name': 'Lazada Test Channel',
            'code': 'lazada_test',
            'active': True,
            'use_mock_data': True,
            'api_url': 'sandbox',
            'api_key': 'test_app_key',
            'api_secret': 'test_app_secret',
            'access_token': 'test_token',
            'refresh_token': 'test_refresh',
        })

    def test_lazada_connector_import(self):
        """Test Lazada connector can be imported."""
        from multichannel_ai.models.connectors.lazada import LazadaConnector
        self.assertTrue(LazadaConnector is not None)
        self.assertEqual(LazadaConnector.PLATFORM_CODE, 'lazada')

    def test_lazada_connector_init(self):
        """Test Lazada connector initialization."""
        from multichannel_ai.models.connectors.lazada import LazadaConnector
        
        connector = LazadaConnector(self.channel_lazada)
        self.assertIsNotNone(connector)
        self.assertEqual(connector.PLATFORM_CODE, 'lazada')

    def test_is_mock_mode_true(self):
        """Test mock mode detection when api_url is sandbox."""
        from multichannel_ai.models.connectors.lazada import LazadaConnector
        
        connector = LazadaConnector(self.channel_lazada)
        self.assertTrue(connector._is_mock_mode())

    def test_is_mock_mode_false(self):
        """Test mock mode detection when api_url is production."""
        self.channel_lazada.api_url = 'https://api.lazada.co.th/rest'
        from multichannel_ai.models.connectors.lazada import LazadaConnector
        
        connector = LazadaConnector(self.channel_lazada)
        self.assertFalse(connector._is_mock_mode())

    def test_generate_lazada_signature(self):
        """Test Lazada signature generation."""
        from multichannel_ai.models.connectors.lazada import LazadaConnector
        
        connector = LazadaConnector(self.channel_lazada)
        
        # Test signature generation
        params = {'api_name': 'product.create', 'test_param': 'value'}
        signature = connector._generate_lazada_signature(params)
        
        # Signature should be string
        self.assertIsInstance(signature, str)

    def test_get_lazada_headers(self):
        """Test Lazada headers generation."""
        from multichannel_ai.models.connectors.lazada import LazadaConnector
        
        connector = LazadaConnector(self.channel_lazada)
        headers = connector._get_lazada_headers()
        
        self.assertIn('Content-Type', headers)
        self.assertIn('Accept', headers)

    def test_refresh_access_token_mock(self):
        """Test refresh token in mock mode."""
        from multichannel_ai.models.connectors.lazada import LazadaConnector
        
        connector = LazadaConnector(self.channel_lazada)
        result = connector.refresh_access_token()
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_upload_image_mock(self):
        """Test image upload in mock mode."""
        from multichannel_ai.models.connectors.lazada import LazadaConnector
        
        connector = LazadaConnector(self.channel_lazada)
        
        # Mock image data
        image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00'
        
        result = connector.upload_image(image_data, 'test.png', product_id=12345)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_create_item_mock(self):
        """Test create item in mock mode."""
        from multichannel_ai.models.connectors.lazada import LazadaConnector
        
        connector = LazadaConnector(self.channel_lazada)
        
        product_data = {
            'name': 'Test Product',
            'price': 299.00,
            'quantity': 100,
        }
        
        result = connector.create_item(product_data)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_update_item_mock(self):
        """Test update item in mock mode."""
        from multichannel_ai.models.connectors.lazada import LazadaConnector
        
        connector = LazadaConnector(self.channel_lazada)
        
        product_data = {
            'name': 'Updated Product',
            'price': 349.00,
        }
        
        result = connector.update_item(12345, product_data)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_get_products_mock(self):
        """Test get products in mock mode."""
        from multichannel_ai.models.connectors.lazada import LazadaConnector
        
        connector = LazadaConnector(self.channel_lazada)
        result = connector.get_products(page=1, limit=10)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_update_stock_mock(self):
        """Test update stock in mock mode."""
        from multichannel_ai.models.connectors.lazada import LazadaConnector
        
        connector = LazadaConnector(self.channel_lazada)
        result = connector.update_stock(12345, 50)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_update_price_mock(self):
        """Test update price in mock mode."""
        from multichannel_ai.models.connectors.lazada import LazadaConnector
        
        connector = LazadaConnector(self.channel_lazada)
        result = connector.update_price(12345, 399.00)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_get_orders_mock(self):
        """Test get orders in mock mode."""
        from multichannel_ai.models.connectors.lazada import LazadaConnector
        
        connector = LazadaConnector(self.channel_lazada)
        result = connector.get_orders(page=1, limit=10)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_get_order_detail_mock(self):
        """Test get order detail in mock mode."""
        from multichannel_ai.models.connectors.lazada import LazadaConnector
        
        connector = LazadaConnector(self.channel_lazada)
        result = connector.get_order_detail(12345)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_get_logistics_mock(self):
        """Test get logistics in mock mode."""
        from multichannel_ai.models.connectors.lazada import LazadaConnector
        
        connector = LazadaConnector(self.channel_lazada)
        result = connector.get_logistics()
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, (dict, list))

    def test_create_shipment_mock(self):
        """Test create shipment in mock mode."""
        from multichannel_ai.models.connectors.lazada import LazadaConnector
        
        connector = LazadaConnector(self.channel_lazada)
        result = connector.create_shipment(12345, logistics_id=1, tracking_number='TEST123')
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
