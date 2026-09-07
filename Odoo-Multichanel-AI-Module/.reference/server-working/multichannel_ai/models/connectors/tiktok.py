# -*- coding: utf-8 -*-
"""
TikTok Shop Connector
เรียก MOCK หรือ API จริงตาม api_url mode
"""
from .base import ChannelConnectorBase
from .mock_data import MOCK
import logging
import time
import hashlib
import hmac
import json

_logger = logging.getLogger(__name__)


class TikTokConnector(ChannelConnectorBase):
    """TikTok Shop API Connector - Thailand
    
    API Docs: https://partner.tiktok-shop.com/
    
    Auth: OAuth2
    """
    PLATFORM_CODE = 'tiktok'
    PLATFORM_NAME = 'TikTok Shop Thailand'
    
    # Override API URLs
    API_BASE_URLS = {
        'tiktok': 'https://open.tiktokapis.com/v2',
    }
    
    def __init__(self, channel_config):
        super().__init__(channel_config)
        self.app_id = self.api_key  # app_id from TikTok dev portal
        self.shop_id = getattr(channel_config, 'tiktok_shop_id', None)

    def _get_config_value(self, key, default=None):
        """Get config value from channel.config extra fields"""
        return getattr(self.channel, key, default)

    def _is_mock_mode(self):
        """Check if running in mock/sandbox mode"""
        return (self.channel.api_url or 'sandbox') == 'sandbox'

    def _get_tiktok_headers(self):
        """Get TikTok-specific headers with access token"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        return headers

    def refresh_access_token(self):
        """Refresh TikTok OAuth token"""
        if self._is_mock_mode():
            result = MOCK.refresh_token(self.PLATFORM_CODE)
        else:
            result = self._tiktok_refresh_token()
        
        # Update channel config
        from datetime import timedelta
        from odoo.fields import Datetime
        self.channel.write({
            'access_token': result['access_token'],
            'refresh_token': result.get('refresh_token', ''),
            'token_expire_date': Datetime.now() + timedelta(seconds=result.get('expires_in', 86400 * 30)),
        })
        return result

    def _tiktok_refresh_token(self):
        """Real TikTok token refresh API
        
        POST https://open.tiktokapis.com/v2/oauth/token/refresh/
        """
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.app_id,
            'client_secret': self.api_secret,
        }
        
        result = self._request('POST', '/oauth/token/refresh/', json=data)
        return {
            'access_token': result.get('access_token', ''),
            'refresh_token': result.get('refresh_token', ''),
            'expires_in': result.get('expires_in', 86400 * 30),
        }

    def upload_image(self, image_data, filename='image.jpg', product_id=None):
        """อัปโหลดรูปไป TikTok"""
        if self._is_mock_mode():
            return MOCK.upload_image(self.PLATFORM_CODE, image_data, filename, product_id)
        return self._tiktok_upload_image(image_data, filename, product_id)

    def _tiktok_upload_image(self, image_data, filename, product_id=None):
        """Real TikTok image upload
        
        POST https://open.tiktokapis.com/v2/product/image/upload/
        """
        # TikTok uses multipart upload
        import requests
        url = self._get_api_url('/v2/product/image/upload/')
        
        files = {
            'image': (filename, image_data, 'image/jpeg'),
        }
        
        response = requests.post(
            url,
            headers={'Authorization': f'Bearer {self.access_token}'},
            files=files,
            timeout=60
        )
        
        result = self._handle_response(response)
        return {
            'success': True,
            'platform_image_id': result.get('data', {}).get('image_id', ''),
            'url': result.get('data', {}).get('image_url', ''),
        }

    def create_item(self, product_data):
        """สร้างสินค้าใหม่บน TikTok"""
        if self._is_mock_mode():
            return MOCK.create_item(self.PLATFORM_CODE, product_data)
        return self._tiktok_create_item(product_data)

    def _tiktok_create_item(self, product_data):
        """Real TikTok create product API
        
        POST https://open.tiktokapis.com/v2/product/202309/products/
        """
        tiktok_product = {
            'product_type': 'NORMAL',
            'category_id': str(product_data.get('category_id', '')),
            'product_name': product_data.get('name', ''),
            'description': product_data.get('description', ''),
            'images': [{
                'image_id': img.get('image_id', '')
            } for img in product_data.get('images', [])],
            'sku_info': [{
                'sku_id': '',
                'price': {
                    'currency': 'THB',
                    'amount': str(product_data.get('price', 0)),
                },
                'stock_infos': [{
                    'warehouse_id': '10001',
                    'available_stock': int(product_data.get('stock', 0)),
                }],
            }],
        }
        
        result = self._request('POST', '/v2/product/202309/products/', json=tiktok_product)
        return {
            'success': True,
            'platform_item_id': str(result.get('data', {}).get('product_id', '')),
            'url': f'https://shop.tiktok.com/product/{result.get("data", {}).get("product_id", "")}',
        }

    def update_item(self, platform_item_id, product_data):
        """แก้ไขสินค้าบน TikTok"""
        if self._is_mock_mode():
            return MOCK.update_item(self.PLATFORM_CODE, platform_item_id, product_data)
        return self._tiktok_update_item(platform_item_id, product_data)

    def _tiktok_update_item(self, platform_item_id, product_data):
        """Real TikTok update product API
        
        PUT https://open.tiktokapis.com/v2/product/202309/products/
        """
        tiktok_product = {
            'product_id': str(platform_item_id),
            'product_name': product_data.get('name', ''),
            'description': product_data.get('description', ''),
        }
        
        self._request('PUT', '/v2/product/202309/products/', json=tiktok_product)
        return {'success': True, 'message': f'Item {platform_item_id} updated'}

    def delete_item(self, platform_item_id):
        """ลบสินค้าออกจาก TikTok"""
        if self._is_mock_mode():
            return MOCK.delete_item(self.PLATFORM_CODE, platform_item_id)
        return self._tiktok_delete_item(platform_item_id)

    def _tiktok_delete_item(self, platform_item_id):
        """Real TikTok delete product API
        
        DELETE https://open.tiktokapis.com/v2/product/202309/products/
        """
        params = {'product_id': str(platform_item_id)}
        self._request('DELETE', '/v2/product/202309/products/', params=params)
        return {'success': True, 'message': f'Item {platform_item_id} deleted'}

    def get_item(self, platform_item_id):
        """ดึงสินค้า 1 ตัวจาก TikTok"""
        if self._is_mock_mode():
            return MOCK.get_item(self.PLATFORM_CODE, platform_item_id)
        return self._tiktok_get_item(platform_item_id)

    def _tiktok_get_item(self, platform_item_id):
        """Real TikTok get product API
        
        GET https://open.tiktokapis.com/v2/product/202309/products/get/
        """
        params = {'product_id': str(platform_item_id)}
        result = self._request('GET', '/v2/product/202309/products/get/', params=params)
        
        product = result.get('data', {}).get('products', [{}])[0]
        return {
            'item_id': str(product.get('product_id', '')),
            'name': product.get('product_name', ''),
            'price': float(product.get('skus', [{}])[0].get('price', {}).get('amount', 0)),
            'stock': int(product.get('skus', [{}])[0].get('stock_infos', [{}])[0].get('available_stock', 0)),
        }

    def get_products(self, page=1, limit=50, **kwargs):
        """ดึงรายการสินค้าจาก TikTok"""
        if self._is_mock_mode():
            return MOCK.get_products(self.PLATFORM_CODE, page, limit, **kwargs)
        return self._tiktok_get_products(page, limit, **kwargs)

    def _tiktok_get_products(self, page, limit, **kwargs):
        """Real TikTok get products list API
        
        GET https://open.tiktokapis.com/v2/product/202309/products/search/
        """
        data = {
            'page_size': limit,
            'cursor': (page - 1) * limit,
        }
        
        result = self._request('POST', '/v2/product/202309/products/search/', json=data)
        
        products = []
        for product in result.get('data', {}).get('products', []):
            products.append({
                'item_id': str(product.get('product_id', '')),
                'name': product.get('product_name', ''),
                'price': float(product.get('skus', [{}])[0].get('price', {}).get('amount', 0)),
                'status': product.get('status', ''),
            })
        
        return {
            'products': products,
            'total': result.get('data', {}).get('total_count', len(products)),
            'page': page,
            'has_more': result.get('data', {}).get('has_more', False),
        }

    def update_stock(self, platform_item_id, stock):
        """อัปเดตสต็อกสินค้าบน TikTok"""
        if self._is_mock_mode():
            return MOCK.update_stock(self.PLATFORM_CODE, platform_item_id, stock)
        return self._tiktok_update_stock(platform_item_id, stock)

    def _tiktok_update_stock(self, platform_item_id, stock):
        """Real TikTok update stock API
        
        POST https://open.tiktokapis.com/v2/product/202309/stock/update/
        """
        data = {
            'product_id': str(platform_item_id),
            'sku_stocks': [{
                'sku_id': '',  # Main SKU
                'stock_infos': [{
                    'warehouse_id': '10001',
                    'available_stock': int(stock),
                }],
            }],
        }
        
        self._request('POST', '/v2/product/202309/stock/update/', json=data)
        return {'success': True, 'message': f'Stock updated to {stock}'}

    def update_price(self, platform_item_id, price):
        """อัปเดตราคาสินค้าบน TikTok"""
        if self._is_mock_mode():
            return MOCK.update_price(self.PLATFORM_CODE, platform_item_id, price)
        return self._tiktok_update_price(platform_item_id, price)

    def _tiktok_update_price(self, platform_item_id, price):
        """Real TikTok update price API
        
        POST https://open.tiktokapis.com/v2/product/202309/price/update/
        """
        data = {
            'product_id': str(platform_item_id),
            'sku_prices': [{
                'sku_id': '',  # Main SKU
                'price': {
                    'currency': 'THB',
                    'amount': str(price),
                },
            }],
        }
        
        self._request('POST', '/v2/product/202309/price/update/', json=data)
        return {'success': True, 'message': f'Price updated to {price}'}

    def get_orders(self, since=None, status=None, page=1, limit=50):
        """ดึงรายการ orders จาก TikTok"""
        if self._is_mock_mode():
            return MOCK.get_orders(self.PLATFORM_CODE, since, status, page, limit)
        return self._tiktok_get_orders(since, status, page, limit)

    def _tiktok_get_orders(self, since, status, page, limit):
        """Real TikTok get orders API
        
        POST https://open.tiktokapis.com/v2/order/202309/orders/search/
        """
        data = {
            'page_size': limit,
            'cursor': (page - 1) * limit,
        }
        
        if since:
            data['create_time_from'] = int(since)
            data['create_time_to'] = int(time.time())
        
        if status:
            data['order_status'] = status
        
        result = self._request('POST', '/v2/order/202309/orders/search/', json=data)
        
        orders = []
        for order in result.get('data', {}).get('orders', []):
            orders.append({
                'order_id': str(order.get('order_id', '')),
                'status': order.get('order_status', ''),
                'total': float(order.get('total_amount', {}).get('amount', 0)),
                'create_time': order.get('create_time', 0),
            })
        
        return {
            'orders': orders,
            'total': len(orders),
            'page': page,
            'has_more': result.get('data', {}).get('has_more', False),
        }

    def get_order_detail(self, platform_order_id):
        """ดึงรายละเอียด order จาก TikTok"""
        if self._is_mock_mode():
            return MOCK.get_order_detail(self.PLATFORM_CODE, platform_order_id)
        return self._tiktok_get_order_detail(platform_order_id)

    def _tiktok_get_order_detail(self, platform_order_id):
        """Real TikTok get order detail API
        
        GET https://open.tiktokapis.com/v2/order/202309/orders/get/
        """
        params = {'order_id': str(platform_order_id)}
        result = self._request('GET', '/v2/order/202309/orders/get/', params=params)
        
        order = result.get('data', {})
        items = []
        for item in order.get('line_items', []):
            items.append({
                'name': item.get('product_name', ''),
                'qty': item.get('quantity', 0),
                'price': float(item.get('unit_price', {}).get('amount', 0)),
            })
        
        return {
            'order_id': str(order.get('order_id', '')),
            'status': order.get('order_status', ''),
            'total': float(order.get('total_amount', {}).get('amount', 0)),
            'items': items,
        }

    def get_logistics(self):
        """ดึงรายการ logistics options จาก TikTok"""
        if self._is_mock_mode():
            return MOCK.get_logistics(self.PLATFORM_CODE)
        return self._tiktok_get_logistics()

    def _tiktok_get_logistics(self):
        """Real TikTok get logistics API
        
        GET https://open.tiktokapis.com/v2/logistics/warehouse/search/
        """
        result = self._request('GET', '/v2/logistics/warehouse/search/')
        
        logistics = []
        for log in result.get('data', {}).get('warehouse_list', []):
            logistics.append({
                'logistics_id': str(log.get('warehouse_id', '')),
                'name': log.get('warehouse_name', ''),
                'enabled': True,
            })
        
        return logistics

    def create_shipment(self, platform_order_id, logistics_id, tracking_number=None):
        """สร้าง shipment บน TikTok"""
        if self._is_mock_mode():
            return MOCK.create_shipment(self.PLATFORM_CODE, platform_order_id, logistics_id, tracking_number)
        return self._tiktok_create_shipment(platform_order_id, logistics_id, tracking_number)

    def _tiktok_create_shipment(self, platform_order_id, logistics_id, tracking_number=None):
        """Real TikTok create shipment API
        
        POST https://open.tiktokapis.com/v2/logistics/shipping_document/upload/
        """
        data = {
            'order_id': str(platform_order_id),
            'shipping_provider_id': str(logistics_id),
        }
        
        if tracking_number:
            # Upload tracking number separately
            pass
        
        self._request('POST', '/v2/logistics/shipping_document/upload/', json=data)
        
        return {
            'success': True,
            'shipment_id': f'tiktok_{platform_order_id}',
            'tracking_number': tracking_number or '',
        }
