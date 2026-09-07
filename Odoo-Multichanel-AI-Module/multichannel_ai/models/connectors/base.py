# -*- coding: utf-8 -*-
"""
Base Connector Class for Multi-Channel Integration
Abstract interface สำหรับทุก platform
"""
from abc import ABC, abstractmethod
from odoo import _
from odoo.exceptions import ValidationError
import logging
import time
import hashlib
import hmac
import json

_logger = logging.getLogger(__name__)


class ChannelConnectorBase(ABC):
    """Abstract base class สำหรับทุก platform connector"""

    PLATFORM_CODE = 'base'
    PLATFORM_NAME = 'Base Platform'

    def __init__(self, channel_config):
        self.channel = channel_config
        self.api_key = channel_config.api_key
        self.api_secret = channel_config.api_secret
        self.access_token = channel_config.access_token
        self.refresh_token = channel_config.refresh_token

    def refresh_access_token(self):
        """Refresh OAuth token - Override in subclass"""
        _logger.warning(f'{self.PLATFORM_NAME}: refresh_access_token() not implemented')
        return {'access_token': f'{self.PLATFORM_CODE}_token_{time.time()}'}

    def ensure_valid_token(self):
        """ตรวจสอบ token valid ไหม ถ้าไม่ refresh"""
        if self.channel.is_token_expired and self.refresh_token:
            try:
                self.refresh_access_token()
            except Exception as e:
                raise ValidationError(_('Token expired: %s') % str(e))

    # ===========================
    # Image Upload
    # ===========================
    @abstractmethod
    def upload_image(self, image_data, filename='image.jpg', product_id=None):
        """อัปโหลดรูปไป platform"""
        pass

    # ===========================
    # Product Management
    # ===========================
    @abstractmethod
    def create_item(self, product_data):
        """สร้างสินค้าใหม่"""
        pass

    @abstractmethod
    def update_item(self, platform_item_id, product_data):
        """แก้ไขสินค้า"""
        pass

    @abstractmethod
    def delete_item(self, platform_item_id):
        """ลบสินค้า"""
        pass

    @abstractmethod
    def get_item(self, platform_item_id):
        """ดึงสินค้า 1 ตัว"""
        pass

    @abstractmethod
    def get_products(self, page=1, limit=50, **kwargs):
        """ดึงรายการสินค้า"""
        pass

    # ===========================
    # Stock & Price
    # ===========================
    @abstractmethod
    def update_stock(self, platform_item_id, stock):
        """อัปเดตสต็อก"""
        pass

    @abstractmethod
    def update_price(self, platform_item_id, price):
        """อัปเดตราคา"""
        pass

    # ===========================
    # Order Management
    # ===========================
    @abstractmethod
    def get_orders(self, since=None, status=None, page=1, limit=50):
        """ดึงรายการ orders"""
        pass

    @abstractmethod
    def get_order_detail(self, platform_order_id):
        """ดึงรายละเอียด order"""
        pass

    # ===========================
    # Logistics
    # ===========================
    @abstractmethod
    def get_logistics(self):
        """ดึงรายการ logistics options"""
        pass

    @abstractmethod
    def create_shipment(self, platform_order_id, logistics_id, tracking_number=None):
        """สร้าง shipment"""
        pass

    # ===========================
    # HTTP Request Helpers (Phase 16 - Real API Structure)
    # ===========================
    
    # API URLs ตาม platform (override ใน subclass)
    API_BASE_URLS = {
        'shopee': 'https://partner.shopeemobile.com/api/v1',
        'lazada': 'https://api.lazada.com/rest',
        'tiktok': 'https://open.tiktokapis.com/v2',
    }
    
    REQUEST_TIMEOUT = 30  # วินาที
    MAX_RETRIES = 3
    
    def _get_api_url(self, endpoint=''):
        """คืน API URL ตาม platform
        
        Usage:
            url = self._get_api_url('/product/create')
        """
        base_url = self.API_BASE_URLS.get(self.PLATFORM_CODE, '')
        if not base_url:
            _logger.warning(f'{self.PLATFORM_NAME}: No API base URL configured')
        return f'{base_url}{endpoint}'
    
    def _get_headers(self, content_type='application/json'):
        """คืน HTTP headers พร้อม authentication
        
        Override ใน subclass ถ้าต้องการ custom headers
        """
        headers = {
            'Content-Type': content_type,
            'Accept': 'application/json',
        }
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        return headers
    
    def _handle_response(self, response):
        """Parse HTTP response และตรวจสอบ errors
        
        Returns:
            dict: parsed JSON response
            
        Raises:
            ValidationError: ถ้า response มี error
        """
        try:
            data = response.json()
        except (ValueError, json.JSONDecodeError):
            # ถ้าไม่ใช่ JSON ลอง text
            data = {'raw_response': response.text}
        
        # ตรวจสอบ HTTP status
        if response.status_code >= 400:
            error_msg = data.get('message', data.get('error', 'Unknown error'))
            _logger.error(f'{self.PLATFORM_NAME} API Error [{response.status_code}]: {error_msg}')
            raise ValidationError(_(f'{self.PLATFORM_NAME} API Error: {error_msg}'))
        
        # ตรวจสอบ business errors (บาง platform คืน 200 แต่มี error ใน body)
        if data.get('error'):
            error_msg = data.get('message', data.get('error', 'Unknown'))
            _logger.error(f'{self.PLATFORM_NAME} Business Error: {error_msg}')
            raise ValidationError(_(f'{self.PLATFORM_NAME}: {error_msg}'))
        
        return data
    
    def _retry_request(self, method, url, **kwargs):
        """Execute HTTP request พร้อม retry logic
        
        Args:
            method: 'GET', 'POST', 'PUT', 'DELETE'
            url: API endpoint URL
            **kwargs: extra args สำหรับ requests (headers, json, data, etc.)
            
        Returns:
            requests.Response object
            
        Retry Logic:
            - ลองสูงสุด 3 ครั้ง
            - Retry ถ้า status = 429 (rate limit) หรือ 5xx
            - Delay 1 วินาทีระหว่าง retry
        """
        try:
            import requests
        except ImportError:
            _logger.warning('requests library not installed')
            raise ValidationError(_('Please install requests: pip install requests'))
        
        kwargs.setdefault('timeout', self.REQUEST_TIMEOUT)
        kwargs.setdefault('headers', self._get_headers())
        
        last_error = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = requests.request(method.upper(), url, **kwargs)
                
                # Rate limit = retry with delay
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 1))
                    _logger.warning(f'{self.PLATFORM_NAME}: Rate limited, retrying in {retry_after}s...')
                    time.sleep(retry_after)
                    continue
                
                # Server errors = retry
                if 500 <= response.status_code < 600:
                    _logger.warning(f'{self.PLATFORM_NAME}: Server error {response.status_code}, retry {attempt}/{self.MAX_RETRIES}...')
                    time.sleep(1)
                    continue
                
                return response
                
            except requests.exceptions.Timeout:
                last_error = f'Timeout after {self.REQUEST_TIMEOUT}s'
                _logger.warning(f'{self.PLATFORM_NAME}: Request timeout, retry {attempt}/{self.MAX_RETRIES}...')
                time.sleep(1)
            except requests.exceptions.ConnectionError as e:
                last_error = str(e)
                _logger.warning(f'{self.PLATFORM_NAME}: Connection error, retry {attempt}/{self.MAX_RETRIES}...')
                time.sleep(1)
            except Exception as e:
                last_error = str(e)
                _logger.error(f'{self.PLATFORM_NAME}: Request error: {e}')
                raise
        
        # ถ้าลองครบ 3 ครั้งแล้ว fail
        raise ValidationError(_(f'{self.PLATFORM_NAME}: Request failed after {self.MAX_RETRIES} retries: {last_error}'))

    def _request(self, method, endpoint, **kwargs):
        """Main HTTP request method - combines all helpers
        
        Usage:
            # GET request
            data = self._request('GET', '/products')
            
            # POST request
            data = self._request('POST', '/product/create', json={'name': 'Test'})
            
            # With query params
            data = self._request('GET', '/products', params={'page': 1, 'limit': 50})
        """
        url = self._get_api_url(endpoint)
        _logger.info(f'{self.PLATFORM_NAME}: {method} {url}')
        
        response = self._retry_request(method, url, **kwargs)
        return self._handle_response(response)

    # ===========================
    # Helper Methods
    # ===========================
    def _mock_response(self, data=None, message='Success', success=True):
        return {'success': success, 'message': message, **(data or {})}

    def _generate_signature(self, data, secret=None):
        secret = secret or self.api_secret or ''
        if isinstance(data, dict):
            data = json.dumps(data, separators=(',', ':'))
        return hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()
