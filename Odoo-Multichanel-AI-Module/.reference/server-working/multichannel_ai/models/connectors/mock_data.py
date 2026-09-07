# -*- coding: utf-8 -*-
"""
Mock Data for Multi-Channel Connector Testing
"""
import time
import logging

_logger = logging.getLogger(__name__)


class MockData:
    """Mock data generator"""

    @staticmethod
    def upload_image(platform, image_data, filename='image.jpg', product_id=None):
        mock_id = f'{platform}_img_{int(time.time())}'
        urls = {'shopee': f'https://cf.shopee.co.th/file/{mock_id}',
                'lazada': f'https://lzd.co.th/i/{mock_id}',
                'tiktok': f'https://shop.tiktok.com/product/{mock_id}'}
        return {'success': True, 'platform_image_id': mock_id, 'url': urls.get(platform)}

    @staticmethod
    def create_item(platform, product_data):
        mock_id = f'{platform}_{int(time.time())}'
        return {'success': True, 'platform_item_id': mock_id, 'url': f'https://{platform}.com/p/{mock_id}'}

    @staticmethod
    def update_item(platform, platform_item_id, product_data):
        return {'success': True, 'message': f'Item {platform_item_id} updated'}

    @staticmethod
    def delete_item(platform, platform_item_id):
        return {'success': True, 'message': f'Item {platform_item_id} deleted'}

    @staticmethod
    def get_item(platform, platform_item_id):
        return {'item_id': platform_item_id, 'name': f'Mock Product', 'price': 199.0, 'stock': 50}

    @staticmethod
    def get_products(platform, page=1, limit=50, **kwargs):
        products = [{'item_id': f'{platform}_{i}', 'name': f'Mock {i}', 'price': 100 + i} for i in range(1, 6)]
        return {'products': products, 'total': 5, 'page': page, 'has_more': False}

    @staticmethod
    def update_stock(platform, platform_item_id, stock):
        return {'success': True, 'message': f'Stock={stock}'}

    @staticmethod
    def update_price(platform, platform_item_id, price):
        return {'success': True, 'message': f'Price={price}'}

    @staticmethod
    def get_orders(platform, since=None, status=None, page=1, limit=50):
        orders = [{'order_id': f'{platform}_o{i}', 'status': 'pending', 'total': 500} for i in range(1, 4)]
        return {'orders': orders, 'total': 3, 'page': page, 'has_more': False}

    @staticmethod
    def get_order_detail(platform, platform_order_id):
        return {'order_id': platform_order_id, 'status': 'pending', 'total': 500.0, 'items': [{'name': 'Mock', 'qty': 1}]}

    @staticmethod
    def get_logistics(platform):
        return [{'logistics_id': f'{platform}_jt', 'name': 'J&T Express', 'enabled': True},
                {'logistics_id': f'{platform}_kerry', 'name': 'Kerry Express', 'enabled': True}]

    @staticmethod
    def create_shipment(platform, platform_order_id, logistics_id, tracking_number=None):
        return {'success': True, 'shipment_id': f'{platform}_ship_{int(time.time())}',
                'tracking_number': tracking_number or f'TRACK{int(time.time())}'}

    @staticmethod
    def refresh_token(platform):
        return {'access_token': f'{platform}_token_{int(time.time())}',
                'refresh_token': f'{platform}_refresh_{int(time.time())}', 'expires_in': 86400 * 30}

    # ===========================
    # Test Data (สำหรับทดสอบ model methods)
    # ===========================
    @staticmethod
    def get_test_products(platform, count=5):
        """Test data: products จำลองสำหรับทดสอบ channel.product"""
        categories = {
            'shopee': ['Fashion Women', 'Electronics', 'Home & Living', 'Beauty', 'Toys'],
            'lazada': ['Apparel', 'Mobiles', 'Home', 'Health', 'Sports'],
            'tiktok': ['Trending', 'Beauty', 'Fashion', 'Gadgets', 'Lifestyle'],
        }
        data = []
        for i in range(1, count + 1):
            data.append({
                'platform_item_id': f'{platform}_test_{i}',
                'name': f'Test Product {i} ({platform})',
                'sku': f'SKU-{platform.upper()}-{i:03d}',
                'price': 99.0 + (i * 50),
                'stock': 10 + i,
                'category': categories.get(platform, ['General'])[(i - 1) % 5],
                'weight': 0.5 + (i * 0.1),
                'description': f'นี่คือสินค้าทดสอบตัวที่ {i} สำหรับ {platform}',
                'images': [
                    f'https://example.com/{platform}/img_{i}_1.jpg',
                    f'https://example.com/{platform}/img_{i}_2.jpg',
                ],
                'status': 'active',
                'created_at': '2026-01-01T00:00:00Z',
            })
        return data

    @staticmethod
    def get_test_orders(platform, count=5):
        """Test data: orders จำลองสำหรับทดสอบ channel.order"""
        statuses = ['pending', 'to_ship', 'shipped', 'completed', 'cancelled']
        data = []
        for i in range(1, count + 1):
            data.append({
                'platform_order_id': f'{platform}_order_test_{i}',
                'order_number': f'#{platform.upper()}{1000 + i}',
                'status': statuses[(i - 1) % 5],
                'total': 250.0 + (i * 100),
                'shipping_fee': 30.0,
                'grand_total': 280.0 + (i * 100),
                'buyer': {
                    'name': f'ลูกค้าทดสอบ {i}',
                    'phone': f'08{i:08d}',
                    'email': f'buyer{i}@test.com',
                },
                'shipping_address': {
                    'full_name': f'ลูกค้าทดสอบ {i}',
                    'phone': f'08{i:08d}',
                    'address': f'123/4 ถนนทดสอบ {i}',
                    'subdistrict': 'แขวงทดสอบ',
                    'district': 'เขตทดสอบ',
                    'province': 'กรุงเทพมหานคร',
                    'postcode': '10110',
                },
                'items': [
                    {
                        'platform_item_id': f'{platform}_test_{i}',
                        'name': f'Test Product {i}',
                        'sku': f'SKU-{platform.upper()}-{i:03d}',
                        'qty': 1 + (i % 3),
                        'price': 99.0 + (i * 50),
                        'subtotal': 99.0 * (1 + (i % 3)),
                    }
                ],
                'created_at': '2026-01-15T10:30:00Z',
                'paid_at': '2026-01-15T10:35:00Z',
            })
        return data

    @staticmethod
    def get_test_categories(platform):
        """Test data: categories จำลอง"""
        return [
            {'category_id': f'{platform}_cat_1', 'name': 'หมวดหมู่หลัก 1', 'parent_id': None},
            {'category_id': f'{platform}_cat_2', 'name': 'หมวดหมู่หลัก 2', 'parent_id': None},
            {'category_id': f'{platform}_cat_3', 'name': 'หมวดหมู่ย่อย 1.1', 'parent_id': f'{platform}_cat_1'},
            {'category_id': f'{platform}_cat_4', 'name': 'หมวดหมู่ย่อย 2.1', 'parent_id': f'{platform}_cat_2'},
        ]

    @staticmethod
    def get_test_logistics(platform):
        """Test data: logistics จำลอง"""
        return [
            {'logistics_id': f'{platform}_jt', 'name': 'J&T Express', 'enabled': True, 'fee': 30.0},
            {'logistics_id': f'{platform}_kerry', 'name': 'Kerry Express', 'enabled': True, 'fee': 35.0},
            {'logistics_id': f'{platform}_flash', 'name': 'Flash Express', 'enabled': True, 'fee': 25.0},
            {'logistics_id': f'{platform}_thaipost', 'name': 'ไปรษณีย์ไทย', 'enabled': True, 'fee': 20.0},
        ]

    @staticmethod
    def get_test_shipment(platform, order_id):
        """Test data: shipment จำลอง"""
        return {
            'shipment_id': f'{platform}_ship_test_{int(time.time())}',
            'order_id': order_id,
            'tracking_number': f'TRACK{platform.upper()}{int(time.time())}',
            'logistics': f'{platform}_jt',
            'status': 'shipped',
            'shipped_at': '2026-01-20T14:00:00Z',
        }


MOCK = MockData()
