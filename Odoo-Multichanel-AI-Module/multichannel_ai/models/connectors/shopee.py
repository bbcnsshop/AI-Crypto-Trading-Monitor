# -*- coding: utf-8 -*-
"""
Shopee Connector
เรียก MOCK หรือ API จริงตาม api_url mode
"""
from .base import ChannelConnectorBase
from .mock_data import MOCK
import logging
import time
import hashlib
import hmac
import base64

_logger = logging.getLogger(__name__)


class ShopeeConnector(ChannelConnectorBase):
    """Shopee API Connector - Thailand
    
    API Docs: https://open.shopee.com/
    
    Auth: OAuth2 + Signature-based authentication
    """
    PLATFORM_CODE = 'shopee'
    PLATFORM_NAME = 'Shopee Thailand'
    
    # Override API URLs
    API_BASE_URLS = {
        'shopee': 'https://partner.shopeemobile.com/api/v1',
    }
    
    def __init__(self, channel_config):
        super().__init__(channel_config)
        self.partner_id = self.api_key  # partner_id from Shopee dev portal
        self.shop_id = getattr(channel_config, 'shop_id', None) or self._get_config_value('shopee_shop_id')

    def _get_config_value(self, key, default=None):
        """Get config value from channel.config extra fields"""
        return getattr(self.channel, key, default)

    def _is_mock_mode(self):
        """Check if running in mock/sandbox mode"""
        return (self.channel.api_url or 'sandbox') == 'sandbox'

    def _generate_shopee_signature(self, path, params=None):
        """Generate Shopee API signature
        
        Shopee uses HMAC-SHA256 with path + params as message
        """
        import urllib.parse
        message = path
        if params:
            # Sort params by key and encode
            sorted_params = sorted(params.items())
            param_str = '&'.join([f'{k}={v}' for k, v in sorted_params])
            message = path + param_str
        
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature.upper()

    def _get_shopee_headers(self):
        """Get Shopee-specific headers with signature"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}' if self.access_token else '',
        }
        return headers

    def refresh_access_token(self):
        """Refresh Shopee OAuth token"""
        if self._is_mock_mode():
            result = MOCK.refresh_token(self.PLATFORM_CODE)
        else:
            # Real Shopee API call
            result = self._shopee_refresh_token()
        
        # Update channel config
        from datetime import timedelta
        from odoo.fields import Datetime
        self.channel.write({
            'access_token': result['access_token'],
            'refresh_token': result.get('refresh_token', ''),
            'token_expire_date': Datetime.now() + timedelta(seconds=result.get('expires_in', 86400 * 30)),
        })
        return result

    def _shopee_refresh_token(self):
        """Real Shopee token refresh API
        
        POST https://partner.shopeemobile.com/api/v1/auth/token/refresh
        """
        path = '/api/v1/auth/token/refresh'
        data = {
            'partner_id': int(self.partner_id),
            'refresh_token': self.refresh_token,
        }
        
        response = self._retry_request('POST', self._get_api_url(path), json=data)
        return self._handle_response(response)

    def upload_image(self, image_data, filename='image.jpg', product_id=None):
        """อัปโหลดรูปไป Shopee"""
        if self._is_mock_mode():
            return MOCK.upload_image(self.PLATFORM_CODE, image_data, filename, product_id)
        
        # Real Shopee API
        return self._shopee_upload_image(image_data, filename, product_id)

    def _shopee_upload_image(self, image_data, filename, product_id=None):
        """Real Shopee image upload
        
        POST https://partner.shopeemobile.com/api/v1/media/upload
        """
        path = '/api/v1/media/upload'
        
        # Prepare multipart form data
        files = {
            'image': (filename, image_data, 'image/jpeg'),
        }
        data = {
            'partner_id': int(self.partner_id),
            'shopid': int(self.shop_id) if self.shop_id else 0,
            'timestamp': int(time.time()),
        }
        
        # Shopee uses multipart upload for images
        import requests
        url = self._get_api_url(path)
        response = requests.post(
            url,
            data=data,
            files=files,
            headers={'Authorization': f'Bearer {self.access_token}'},
            timeout=60
        )
        
        result = self._handle_response(response)
        return {
            'success': True,
            'platform_image_id': result.get('image_id', ''),
            'url': result.get('image_url', ''),
        }

    def create_item(self, product_data):
        """สร้างสินค้าใหม่บน Shopee"""
        if self._is_mock_mode():
            return MOCK.create_item(self.PLATFORM_CODE, product_data)
        return self._shopee_create_item(product_data)

    def _shopee_create_item(self, product_data):
        """Real Shopee create item API
        
        POST https://partner.shopeemobile.com/api/v1/product/add
        """
        path = '/api/v1/product/add'
        
        # Transform to Shopee format
        shopee_data = {
            'partner_id': int(self.partner_id),
            'shopid': int(self.shop_id) if self.shop_id else 0,
            'timestamp': int(time.time()),
            'item': {
                'item_name': product_data.get('name', ''),
                'description': product_data.get('description', ''),
                'price': float(product_data.get('price', 0)),
                'stock': int(product_data.get('stock', 0)),
                'category_id': product_data.get('category_id', 0),
                'attributes': product_data.get('attributes', []),
                'images': [{'image_id': img.get('image_id', '')} for img in product_data.get('images', [])],
            },
        }
        
        result = self._request('POST', path, json=shopee_data)
        return {
            'success': True,
            'platform_item_id': str(result.get('item_id', '')),
            'url': f'https://shopee.co.th/product/{self.shop_id}/{result.get("item_id", "")}',
        }

    def update_item(self, platform_item_id, product_data):
        """แก้ไขสินค้าบน Shopee"""
        if self._is_mock_mode():
            return MOCK.update_item(self.PLATFORM_CODE, platform_item_id, product_data)
        return self._shopee_update_item(platform_item_id, product_data)

    def _shopee_update_item(self, platform_item_id, product_data):
        """Real Shopee update item API
        
        POST https://partner.shopeemobile.com/api/v1/product/update
        """
        path = '/api/v1/product/update'
        
        shopee_data = {
            'partner_id': int(self.partner_id),
            'shopid': int(self.shop_id) if self.shop_id else 0,
            'timestamp': int(time.time()),
            'item_id': int(platform_item_id),
            'item': {
                'item_name': product_data.get('name', ''),
                'description': product_data.get('description', ''),
                'price': float(product_data.get('price', 0)),
                'stock': int(product_data.get('stock', 0)),
            },
        }
        
        result = self._request('POST', path, json=shopee_data)
        return {'success': True, 'message': f'Item {platform_item_id} updated'}

    def delete_item(self, platform_item_id):
        """ลบสินค้าออกจาก Shopee"""
        if self._is_mock_mode():
            return MOCK.delete_item(self.PLATFORM_CODE, platform_item_id)
        return self._shopee_delete_item(platform_item_id)

    def _shopee_delete_item(self, platform_item_id):
        """Real Shopee delete item API
        
        POST https://partner.shopeemobile.com/api/v1/product/delete
        """
        path = '/api/v1/product/delete'
        
        data = {
            'partner_id': int(self.partner_id),
            'shopid': int(self.shop_id) if self.shop_id else 0,
            'timestamp': int(time.time()),
            'item_id': int(platform_item_id),
        }
        
        self._request('POST', path, json=data)
        return {'success': True, 'message': f'Item {platform_item_id} deleted'}

    def get_item(self, platform_item_id):
        """ดึงสินค้า 1 ตัวจาก Shopee"""
        if self._is_mock_mode():
            return MOCK.get_item(self.PLATFORM_CODE, platform_item_id)
        return self._shopee_get_item(platform_item_id)

    def _shopee_get_item(self, platform_item_id):
        """Real Shopee get item detail API
        
        POST https://partner.shopeemobile.com/api/v1/product/get_item_base_info
        """
        path = '/api/v1/product/get_item_base_info'
        
        data = {
            'partner_id': int(self.partner_id),
            'shopid': int(self.shop_id) if self.shop_id else 0,
            'timestamp': int(time.time()),
            'item_id_list': [int(platform_item_id)],
        }
        
        result = self._request('POST', path, json=data)
        items = result.get('item_list', [])
        if items:
            item = items[0]
            return {
                'item_id': str(item.get('item_id', '')),
                'name': item.get('item_name', ''),
                'price': float(item.get('price', 0)),
                'stock': int(item.get('stock_info', [{}])[0].get('stock', 0)),
            }
        return {'error': 'Item not found'}

    def get_products(self, page=1, limit=50, **kwargs):
        """ดึงรายการสินค้าจาก Shopee"""
        if self._is_mock_mode():
            return MOCK.get_products(self.PLATFORM_CODE, page, limit, **kwargs)
        return self._shopee_get_products(page, limit, **kwargs)

    def _shopee_get_products(self, page, limit, **kwargs):
        """Real Shopee get products list API
        
        POST https://partner.shopeemobile.com/api/v1/product/get_item_list
        """
        path = '/api/v1/product/get_item_list'
        offset = (page - 1) * limit
        
        data = {
            'partner_id': int(self.partner_id),
            'shopid': int(self.shop_id) if self.shop_id else 0,
            'timestamp': int(time.time()),
            'pagination_offset': offset,
            'pagination_entries_per_page': limit,
            'update_time_from': kwargs.get('update_time_from', 0),
            'update_time_to': kwargs.get('update_time_to', int(time.time())),
        }
        
        result = self._request('POST', path, json=data)
        
        products = []
        for item in result.get('item', []):
            products.append({
                'item_id': str(item.get('item_id', '')),
                'name': item.get('item_name', ''),
                'price': float(item.get('price', 0)),
                'status': item.get('status', ''),
            })
        
        return {
            'products': products,
            'total': result.get('total_count', len(products)),
            'page': page,
            'has_more': result.get('has_more', False),
        }

    def update_stock(self, platform_item_id, stock):
        """อัปเดตสต็อกสินค้าบน Shopee"""
        if self._is_mock_mode():
            return MOCK.update_stock(self.PLATFORM_CODE, platform_item_id, stock)
        return self._shopee_update_stock(platform_item_id, stock)

    def _shopee_update_stock(self, platform_item_id, stock):
        """Real Shopee update stock API
        
        POST https://partner.shopeemobile.com/api/v1/product/update_stock
        """
        path = '/api/v1/product/update_stock'
        
        data = {
            'partner_id': int(self.partner_id),
            'shopid': int(self.shop_id) if self.shop_id else 0,
            'timestamp': int(time.time()),
            'item_id': int(platform_item_id),
            'stock_list': [
                {'stock_infos': [{'available_stock': int(stock)}]}
            ],
        }
        
        self._request('POST', path, json=data)
        return {'success': True, 'message': f'Stock updated to {stock}'}

    def update_price(self, platform_item_id, price):
        """อัปเดตราคาสินค้าบน Shopee"""
        if self._is_mock_mode():
            return MOCK.update_price(self.PLATFORM_CODE, platform_item_id, price)
        return self._shopee_update_price(platform_item_id, price)

    def _shopee_update_price(self, platform_item_id, price):
        """Real Shopee update price API
        
        POST https://partner.shopeemobile.com/api/v1/product/update_price
        """
        path = '/api/v1/product/update_price'
        
        data = {
            'partner_id': int(self.partner_id),
            'shopid': int(self.shop_id) if self.shop_id else 0,
            'timestamp': int(time.time()),
            'item_id': int(platform_item_id),
            'price_list': [{'price': float(price)}],
        }
        
        self._request('POST', path, json=data)
        return {'success': True, 'message': f'Price updated to {price}'}

    def get_orders(self, since=None, status=None, page=1, limit=50):
        """ดึงรายการ orders จาก Shopee"""
        if self._is_mock_mode():
            return MOCK.get_orders(self.PLATFORM_CODE, since, status, page, limit)
        return self._shopee_get_orders(since, status, page, limit)

    def _shopee_get_orders(self, since, status, page, limit):
        """Real Shopee get orders API
        
        POST https://partner.shopeemobile.com/api/v1/orders/get
        """
        path = '/api/v1/orders/get'
        
        data = {
            'partner_id': int(self.partner_id),
            'shopid': int(self.shop_id) if self.shop_id else 0,
            'timestamp': int(time.time()),
            'create_time_from': int(since) if since else int(time.time()) - 86400 * 7,
            'create_time_to': int(time.time()),
            'pagination_offset': (page - 1) * limit,
            'pagination_entries_per_page': limit,
        }
        
        if status:
            data['order_status'] = status
        
        result = self._request('POST', path, json=data)
        
        orders = []
        for order in result.get('orders', []):
            orders.append({
                'order_id': str(order.get('order_id', '')),
                'status': order.get('order_status', ''),
                'total': float(order.get('total_amount', 0)),
                'create_time': order.get('create_time', 0),
            })
        
        return {
            'orders': orders,
            'total': len(orders),
            'page': page,
            'has_more': result.get('has_more', False),
        }

    def get_order_detail(self, platform_order_id):
        """ดึงรายละเอียด order จาก Shopee"""
        if self._is_mock_mode():
            return MOCK.get_order_detail(self.PLATFORM_CODE, platform_order_id)
        return self._shopee_get_order_detail(platform_order_id)

    def _shopee_get_order_detail(self, platform_order_id):
        """Real Shopee get order detail API
        
        POST https://partner.shopeemobile.com/api/v1/orders/order_detail/get
        """
        path = '/api/v1/orders/order_detail/get'
        
        data = {
            'partner_id': int(self.partner_id),
            'shopid': int(self.shop_id) if self.shop_id else 0,
            'timestamp': int(time.time()),
            'order_id_list': [int(platform_order_id)],
        }
        
        result = self._request('POST', path, json=data)
        order_details = result.get('orders', [])
        
        if order_details:
            order = order_details[0]
            items = []
            for item in order.get('items', []):
                items.append({
                    'name': item.get('item_name', ''),
                    'qty': item.get('quantity', 0),
                    'price': float(item.get('price', 0)),
                })
            
            return {
                'order_id': str(order.get('order_id', '')),
                'status': order.get('status', ''),
                'total': float(order.get('total_amount', 0)),
                'items': items,
            }
        return {'error': 'Order not found'}

    def get_logistics(self):
        """ดึงรายการ logistics options จาก Shopee"""
        if self._is_mock_mode():
            return MOCK.get_logistics(self.PLATFORM_CODE)
        return self._shopee_get_logistics()

    def _shopee_get_logistics(self):
        """Real Shopee get logistics API
        
        POST https://partner.shopeemobile.com/api/v1/logistics/get_logistics
        """
        path = '/api/v1/logistics/get_logistics'
        
        data = {
            'partner_id': int(self.partner_id),
            'shopid': int(self.shop_id) if self.shop_id else 0,
            'timestamp': int(time.time()),
        }
        
        result = self._request('POST', path, json=data)
        
        logistics = []
        for log in result.get('logistics', []):
            logistics.append({
                'logistics_id': str(log.get('logistics_id', '')),
                'name': log.get('logistics_name', ''),
                'enabled': log.get('enabled', True),
            })
        
        return logistics

    def create_shipment(self, platform_order_id, logistics_id, tracking_number=None):
        """สร้าง shipment บน Shopee"""
        if self._is_mock_mode():
            return MOCK.create_shipment(self.PLATFORM_CODE, platform_order_id, logistics_id, tracking_number)
        return self._shopee_create_shipment(platform_order_id, logistics_id, tracking_number)

    def _shopee_create_shipment(self, platform_order_id, logistics_id, tracking_number=None):
        """Real Shopee create shipment API
        
        POST https://partner.shopeemobile.com/api/v1/logistics/set_logistics
        """
        path = '/api/v1/logistics/set_logistics'
        
        data = {
            'partner_id': int(self.partner_id),
            'shopid': int(self.shop_id) if self.shop_id else 0,
            'timestamp': int(time.time()),
            'order_id': int(platform_order_id),
            'logistics_id': int(logistics_id),
        }
        
        if tracking_number:
            # Need to use different endpoint for air waybill
            pass
        
        self._request('POST', path, json=data)
        
        return {
            'success': True,
            'shipment_id': f'shopee_{platform_order_id}',
            'tracking_number': tracking_number or '',
        }
