# -*- coding: utf-8 -*-
"""
Lazada Connector
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


class LazadaConnector(ChannelConnectorBase):
    """Lazada API Connector - Thailand
    
    API Docs: https://open.lazada.com/
    
    Auth: OAuth2
    """
    PLATFORM_CODE = 'lazada'
    PLATFORM_NAME = 'Lazada Thailand'
    
    # Override API URLs
    API_BASE_URLS = {
        'lazada': 'https://api.lazada.com/rest',
    }
    
    def __init__(self, channel_config):
        super().__init__(channel_config)
        self.app_key = self.api_key  # app_key from Lazada dev portal
        self.user_id = getattr(channel_config, 'lazada_user_id', None)

    def _get_config_value(self, key, default=None):
        """Get config value from channel.config extra fields"""
        return getattr(self.channel, key, default)

    def _is_mock_mode(self):
        """Check if running in mock/sandbox mode"""
        return (self.channel.api_url or 'sandbox') == 'sandbox'

    def _generate_lazada_signature(self, params=None):
        """Generate Lazada API signature
        
        Lazada uses MD5 signature: md5(app_secret + sorted_params)
        """
        # Sort and join params
        if params:
            sorted_keys = sorted(params.keys())
            param_str = ''.join([f'{k}{params[k]}' for k in sorted_keys])
        else:
            param_str = ''
        
        message = self.api_secret + param_str
        signature = hashlib.md5(message.encode()).hexdigest()
        return signature

    def _get_lazada_headers(self):
        """Get Lazada-specific headers"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        return headers

    def _build_lazada_params(self, action):
        """Build common Lazada API params with signature"""
        params = {
            'app_key': self.app_key,
            'timestamp': str(int(time.time()) * 1000),  # Lazada uses milliseconds
            'access_token': self.access_token or '',
            'method': action,
        }
        # Generate signature from params
        signature = self._generate_lazada_signature(params)
        params['sign'] = signature.upper()
        return params

    def refresh_access_token(self):
        """Refresh Lazada OAuth token"""
        if self._is_mock_mode():
            result = MOCK.refresh_token(self.PLATFORM_CODE)
        else:
            result = self._lazada_refresh_token()
        
        # Update channel config
        from datetime import timedelta
        from odoo.fields import Datetime
        self.channel.write({
            'access_token': result['access_token'],
            'refresh_token': result.get('refresh_token', ''),
            'token_expire_date': Datetime.now() + timedelta(seconds=result.get('expires_in', 86400 * 30)),
        })
        return result

    def _lazada_refresh_token(self):
        """Real Lazada token refresh API
        
        POST https://api.lazada.com/rest/auth/token/refresh
        """
        params = self._build_lazada_params('auth.token.refresh')
        params['refresh_token'] = self.refresh_token
        
        result = self._request('POST', '', params=params)
        return {
            'access_token': result.get('access_token', ''),
            'refresh_token': result.get('refresh_token', ''),
            'expires_in': result.get('expires_in', 86400 * 30),
        }

    def upload_image(self, image_data, filename='image.jpg', product_id=None):
        """อัปโหลดรูปไป Lazada"""
        if self._is_mock_mode():
            return MOCK.upload_image(self.PLATFORM_CODE, image_data, filename, product_id)
        return self._lazada_upload_image(image_data, filename, product_id)

    def _lazada_upload_image(self, image_data, filename, product_id=None):
        """Real Lazada image upload
        
        POST https://api.lazada.com/rest/product/image
        """
        params = self._build_lazada_params('upload.image')
        
        # Lazada uses multipart upload
        import requests
        files = {
            'image': (filename, image_data, 'image/jpeg'),
        }
        
        url = 'https://api.lazada.com/rest/product/image'
        response = requests.post(
            url,
            params=params,
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
        """สร้างสินค้าใหม่บน Lazada"""
        if self._is_mock_mode():
            return MOCK.create_item(self.PLATFORM_CODE, product_data)
        return self._lazada_create_item(product_data)

    def _lazada_create_item(self, product_data):
        """Real Lazada create product API
        
        POST https://api.lazada.com/rest/product/create
        """
        params = self._build_lazada_params('product.create')
        
        # Transform to Lazada format
        lazada_product = {
            'title': product_data.get('name', ''),
            'description': product_data.get('description', ''),
            'price': str(product_data.get('price', 0)),
            'quantity': str(product_data.get('stock', 0)),
            'category_id': str(product_data.get('category_id', 0)),
            'images': json.dumps([
                {'image_id': img.get('image_id', '')} 
                for img in product_data.get('images', [])
            ]),
        }
        
        params['payload'] = json.dumps(lazada_product)
        
        result = self._request('POST', '', params=params)
        return {
            'success': True,
            'platform_item_id': str(result.get('data', {}).get('item_id', '')),
            'url': f'https://www.lazada.co.th/products/{result.get("data", {}).get("item_id", "")}',
        }

    def update_item(self, platform_item_id, product_data):
        """แก้ไขสินค้าบน Lazada"""
        if self._is_mock_mode():
            return MOCK.update_item(self.PLATFORM_CODE, platform_item_id, product_data)
        return self._lazada_update_item(platform_item_id, product_data)

    def _lazada_update_item(self, platform_item_id, product_data):
        """Real Lazada update product API
        
        POST https://api.lazada.com/rest/product/update
        """
        params = self._build_lazada_params('product.update')
        
        lazada_product = {
            'item_id': str(platform_item_id),
            'title': product_data.get('name', ''),
            'description': product_data.get('description', ''),
            'price': str(product_data.get('price', 0)),
            'quantity': str(product_data.get('stock', 0)),
        }
        
        params['payload'] = json.dumps(lazada_product)
        
        self._request('POST', '', params=params)
        return {'success': True, 'message': f'Item {platform_item_id} updated'}

    def delete_item(self, platform_item_id):
        """ลบสินค้าออกจาก Lazada"""
        if self._is_mock_mode():
            return MOCK.delete_item(self.PLATFORM_CODE, platform_item_id)
        return self._lazada_delete_item(platform_item_id)

    def _lazada_delete_item(self, platform_item_id):
        """Real Lazada delete product API
        
        POST https://api.lazada.com/rest/product/delete
        """
        params = self._build_lazada_params('product.delete')
        params['item_id'] = str(platform_item_id)
        
        self._request('POST', '', params=params)
        return {'success': True, 'message': f'Item {platform_item_id} deleted'}

    def get_item(self, platform_item_id):
        """ดึงสินค้า 1 ตัวจาก Lazada"""
        if self._is_mock_mode():
            return MOCK.get_item(self.PLATFORM_CODE, platform_item_id)
        return self._lazada_get_item(platform_item_id)

    def _lazada_get_item(self, platform_item_id):
        """Real Lazada get product API
        
        POST https://api.lazada.com/rest/product/item/get
        """
        params = self._build_lazada_params('product.item.get')
        params['item_id'] = str(platform_item_id)
        
        result = self._request('POST', '', params=params)
        data = result.get('data', {})
        
        return {
            'item_id': str(data.get('item_id', '')),
            'name': data.get('title', ''),
            'price': float(data.get('price', 0)),
            'stock': int(data.get('quantity', 0)),
        }

    def get_products(self, page=1, limit=50, **kwargs):
        """ดึงรายการสินค้าจาก Lazada"""
        if self._is_mock_mode():
            return MOCK.get_products(self.PLATFORM_CODE, page, limit, **kwargs)
        return self._lazada_get_products(page, limit, **kwargs)

    def _lazada_get_products(self, page, limit, **kwargs):
        """Real Lazada get products API
        
        POST https://api.lazada.com/rest/product/items/get
        """
        params = self._build_lazada_params('product.item.list')
        params['offset'] = str((page - 1) * limit)
        params['limit'] = str(limit)
        
        if kwargs.get('update_time_from'):
            params['update_after'] = str(kwargs['update_time_from'])
        
        result = self._request('POST', '', params=params)
        
        products = []
        for item in result.get('data', {}).get('products', []):
            products.append({
                'item_id': str(item.get('item_id', '')),
                'name': item.get('name', ''),
                'price': float(item.get('price', 0)),
                'status': item.get('status', ''),
            })
        
        return {
            'products': products,
            'total': result.get('data', {}).get('total_products', len(products)),
            'page': page,
            'has_more': len(products) == limit,
        }

    def update_stock(self, platform_item_id, stock):
        """อัปเดตสต็อกสินค้าบน Lazada"""
        if self._is_mock_mode():
            return MOCK.update_stock(self.PLATFORM_CODE, platform_item_id, stock)
        return self._lazada_update_stock(platform_item_id, stock)

    def _lazada_update_stock(self, platform_item_id, stock):
        """Real Lazada update stock API
        
        POST https://api.lazada.com/rest/product/stock/sellable
        """
        params = self._build_lazada_params('product.stock.sellable.update')
        
        stock_data = [{
            'item_id': str(platform_item_id),
            'stock_list': [{'warehouse_id': 0, 'available_stock': int(stock)}]
        }]
        
        params['payload'] = json.dumps({'stock_list': stock_data})
        
        self._request('POST', '', params=params)
        return {'success': True, 'message': f'Stock updated to {stock}'}

    def update_price(self, platform_item_id, price):
        """อัปเดตราคาสินค้าบน Lazada"""
        if self._is_mock_mode():
            return MOCK.update_price(self.PLATFORM_CODE, platform_item_id, price)
        return self._lazada_update_price(platform_item_id, price)

    def _lazada_update_price(self, platform_item_id, price):
        """Real Lazada update price API
        
        POST https://api.lazada.com/rest/product/price.update
        """
        params = self._build_lazada_params('product.price.update')
        
        price_data = [{
            'item_id': str(platform_item_id),
            'price_list': [{'warehouse_id': 0, 'price': float(price)}]
        }]
        
        params['payload'] = json.dumps({'price_list': price_data})
        
        self._request('POST', '', params=params)
        return {'success': True, 'message': f'Price updated to {price}'}

    def get_orders(self, since=None, status=None, page=1, limit=50):
        """ดึงรายการ orders จาก Lazada"""
        if self._is_mock_mode():
            return MOCK.get_orders(self.PLATFORM_CODE, since, status, page, limit)
        return self._lazada_get_orders(since, status, page, limit)

    def _lazada_get_orders(self, since, status, page, limit):
        """Real Lazada get orders API
        
        POST https://api.lazada.com/rest/order/get
        """
        params = self._build_lazada_params('order.get')
        params['sort_by'] = 'created_at'
        params['sort_direction'] = 'DESC'
        params['offset'] = str((page - 1) * limit)
        params['limit'] = str(limit)
        
        if since:
            params['created_after'] = str(since)
        if status:
            params['status'] = status
        
        result = self._request('POST', '', params=params)
        
        orders = []
        for order in result.get('data', {}).get('orders', []):
            orders.append({
                'order_id': str(order.get('order_id', '')),
                'status': order.get('status', ''),
                'total': float(order.get('total_amount', 0)),
                'create_time': order.get('created_at', ''),
            })
        
        return {
            'orders': orders,
            'total': len(orders),
            'page': page,
            'has_more': len(orders) == limit,
        }

    def get_order_detail(self, platform_order_id):
        """ดึงรายละเอียด order จาก Lazada"""
        if self._is_mock_mode():
            return MOCK.get_order_detail(self.PLATFORM_CODE, platform_order_id)
        return self._lazada_get_order_detail(platform_order_id)

    def _lazada_get_order_detail(self, platform_order_id):
        """Real Lazada get order detail API
        
        POST https://api.lazada.com/rest/order/items/get
        """
        params = self._build_lazada_params('order.items.get')
        params['order_id'] = str(platform_order_id)
        
        result = self._request('POST', '', params=params)
        
        items = []
        for item in result.get('data', []):
            items.append({
                'name': item.get('name', ''),
                'qty': item.get('quantity', 0),
                'price': float(item.get('unit_price', 0)),
            })
        
        return {
            'order_id': str(platform_order_id),
            'status': result.get('data', [{}])[0].get('status', ''),
            'total': float(result.get('data', [{}])[0].get('order_items', [{}])[0].get('total_amount', 0)),
            'items': items,
        }

    def get_logistics(self):
        """ดึงรายการ logistics options จาก Lazada"""
        if self._is_mock_mode():
            return MOCK.get_logistics(self.PLATFORM_CODE)
        return self._lazada_get_logistics()

    def _lazada_get_logistics(self):
        """Real Lazada get logistics API
        
        POST https://api.lazada.com/rest/order/logistics/get
        """
        params = self._build_lazada_params('delivery.loadlogistics')
        
        result = self._request('POST', '', params=params)
        
        logistics = []
        for log in result.get('data', {}).get('logistics', []):
            logistics.append({
                'logistics_id': str(log.get('logistics_id', '')),
                'name': log.get('logistics_name', ''),
                'enabled': log.get('enabled', True),
            })
        
        return logistics

    def create_shipment(self, platform_order_id, logistics_id, tracking_number=None):
        """สร้าง shipment บน Lazada"""
        if self._is_mock_mode():
            return MOCK.create_shipment(self.PLATFORM_CODE, platform_order_id, logistics_id, tracking_number)
        return self._lazada_create_shipment(platform_order_id, logistics_id, tracking_number)

    def _lazada_create_shipment(self, platform_order_id, logistics_id, tracking_number=None):
        """Real Lazada set order shipment API
        
        POST https://api.lazada.com/rest/order/setitemshipping
        """
        params = self._build_lazada_params('order.setitemshipping')
        
        shipment_data = [{
            'order_id': str(platform_order_id),
            'logistics_id': str(logistics_id),
            'tracking_number': tracking_number or '',
        }]
        
        params['payload'] = json.dumps({'shipment_provider': shipment_data})
        
        self._request('POST', '', params=params)
        
        return {
            'success': True,
            'shipment_id': f'lazada_{platform_order_id}',
            'tracking_number': tracking_number or '',
        }
