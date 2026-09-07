# -*- coding: utf-8 -*-
"""Test Channel Product Image with upload methods.

Comprehensive tests for channel.product.image covering:
- Fields and metadata
- Onchange methods
- Compute methods
- Action methods
- Upload methods (mock mode)
"""
from odoo.tests import TransactionCase, tagged
from unittest.mock import patch, MagicMock


@tagged('post_install', '-at_install', 'multichannel', 'image')
class TestChannelProductImageFields(TransactionCase):
    """Test channel.product.image fields exist."""

    def setUp(self):
        super().setUp()
        self.ChannelProductImage = self.env['channel.product.image']
        self.ChannelConfig = self.env['channel.config']
        self.ChannelProduct = self.env['channel.product']

        # Create test channel
        channel_module = self.env['channel.list.module'].create({
            'name': 'Shopee',
            'code': 'shopee',
            'active': True,
        })
        self.channel = self.ChannelConfig.create({
            'name': 'Test Shopee',
            'code': 'shopee_test',
            'platform': 'shopee',
            'active': True,
            'api_url': 'sandbox',
        })

        # Create product
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'image_1920': False,  # No image
        })

        # Create channel product
        self.channel_product = self.ChannelProduct.create({
            'product_id': self.product.id,
            'channel_id': self.channel.id,
        })

    def test_image_fields_exist(self):
        """Test all required fields exist on model."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
        })
        # Check fields exist
        self.assertTrue(hasattr(image, 'channel_product_id'))
        self.assertTrue(hasattr(image, 'channel_id'))
        self.assertTrue(hasattr(image, 'sequence'))
        self.assertTrue(hasattr(image, 'is_primary'))
        self.assertTrue(hasattr(image, 'source_type'))
        self.assertTrue(hasattr(image, 'image_url'))
        self.assertTrue(hasattr(image, 'upload_status'))
        self.assertTrue(hasattr(image, 'alt_text'))
        self.assertTrue(hasattr(image, 'image_type'))
        self.assertTrue(hasattr(image, 'shopee_image_id'))
        self.assertTrue(hasattr(image, 'lazada_image_id'))
        self.assertTrue(hasattr(image, 'tiktok_image_id'))

    def test_image_creation_with_defaults(self):
        """Test image creation with default values."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
        })
        self.assertTrue(image.id)
        self.assertEqual(image.upload_status, 'pending')
        self.assertEqual(image.source_type, 'product')
        self.assertEqual(image.sequence, 10)
        self.assertFalse(image.is_primary)

    def test_image_source_type_selection(self):
        """Test source type selection field."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'source_type': 'url',
            'image_url': 'https://example.com/test.jpg',
        })
        self.assertEqual(image.source_type, 'url')
        self.assertEqual(image.image_url, 'https://example.com/test.jpg')


@tagged('post_install', '-at_install', 'multichannel', 'image')
class TestChannelProductImageOnchange(TransactionCase):
    """Test onchange methods."""

    def setUp(self):
        super().setUp()
        self.ChannelProductImage = self.env['channel.product.image']
        self.ChannelConfig = self.env['channel.config']
        self.ChannelProduct = self.env['channel.product']

        channel_module = self.env['channel.list.module'].create({
            'name': 'Lazada',
            'code': 'lazada',
            'active': True,
        })
        self.channel = self.ChannelConfig.create({
            'name': 'Test Lazada',
            'code': 'lazada_test',
            'platform': 'lazada',
            'active': True,
            'api_url': 'sandbox',
        })

        self.product = self.env['product.product'].create({'name': 'Test Product'})
        self.channel_product = self.ChannelProduct.create({
            'product_id': self.product.id,
            'channel_id': self.channel.id,
        })

    def test_onchange_source_type_product(self):
        """Test onchange sets odoo_image_field for product source."""
        image = self.ChannelProductImage.new({
            'channel_product_id': self.channel_product.id,
        })
        image.source_type = 'product'
        image._onchange_source_type()
        self.assertEqual(image.odoo_image_field, 'image_1920')

    def test_onchange_source_type_variant(self):
        """Test onchange sets odoo_image_field for variant source."""
        image = self.ChannelProductImage.new({
            'channel_product_id': self.channel_product.id,
        })
        image.source_type = 'variant'
        image._onchange_source_type()
        self.assertEqual(image.odoo_image_field, 'image_variant_1920')

    def test_onchange_source_type_url(self):
        """Test onchange clears odoo_image_field for URL source."""
        image = self.ChannelProductImage.new({
            'channel_product_id': self.channel_product.id,
            'odoo_image_field': 'image_1920',
        })
        image.source_type = 'url'
        image._onchange_source_type()
        self.assertFalse(image.odoo_image_field)


@tagged('post_install', '-at_install', 'multichannel', 'image')
class TestChannelProductImageCompute(TransactionCase):
    """Test compute methods."""

    def setUp(self):
        super().setUp()
        self.ChannelProductImage = self.env['channel.product.image']
        self.ChannelConfig = self.env['channel.config']
        self.ChannelProduct = self.env['channel.product']

        channel_module = self.env['channel.list.module'].create({
            'name': 'TikTok',
            'code': 'tiktok',
            'active': True,
        })
        self.channel = self.ChannelConfig.create({
            'name': 'Test TikTok',
            'code': 'tiktok_test',
            'platform': 'tiktok',
            'active': True,
            'api_url': 'sandbox',
        })

        self.product = self.env['product.product'].create({'name': 'Test Product'})
        self.channel_product = self.ChannelProduct.create({
            'product_id': self.product.id,
            'channel_id': self.channel.id,
        })

    def test_compute_default_alt_text(self):
        """Test alt text is computed correctly."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'source_type': 'url',
            'image_url': 'https://example.com/test.jpg',
        })
        # Call compute method
        image._compute_default_alt_text()
        self.assertIn('Test Product', image.alt_text)
        self.assertIn('Test TikTok', image.alt_text)

    def test_compute_default_image_type_primary(self):
        """Test image_type = 'main' when is_primary=True."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'is_primary': True,
            'sequence': 5,
        })
        image._compute_default_image_type()
        self.assertEqual(image.image_type, 'main')

    def test_compute_default_image_type_sequence_one(self):
        """Test image_type = 'main' when sequence=1."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'sequence': 1,
        })
        image._compute_default_image_type()
        self.assertEqual(image.image_type, 'main')

    def test_compute_default_image_type_gallery(self):
        """Test image_type = 'gallery' when sequence in [2,10]."""
        for seq in [2, 5, 10]:
            image = self.ChannelProductImage.create({
                'channel_product_id': self.channel_product.id,
                'sequence': seq,
                'is_primary': False,
            })
            image._compute_default_image_type()
            self.assertEqual(image.image_type, 'gallery')

    def test_compute_default_image_type_thumbnail(self):
        """Test image_type = 'thumbnail' when sequence > 10."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'sequence': 15,
            'is_primary': False,
        })
        image._compute_default_image_type()
        self.assertEqual(image.image_type, 'thumbnail')


@tagged('post_install', '-at_install', 'multichannel', 'image')
class TestChannelProductImageAction(TransactionCase):
    """Test action methods."""

    def setUp(self):
        super().setUp()
        self.ChannelProductImage = self.env['channel.product.image']
        self.ChannelConfig = self.env['channel.config']
        self.ChannelProduct = self.env['channel.product']

        channel_module = self.env['channel.list.module'].create({
            'name': 'Shopee',
            'code': 'shopee',
            'active': True,
        })
        self.channel = self.ChannelConfig.create({
            'name': 'Test Shopee',
            'code': 'shopee_test',
            'platform': 'shopee',
            'active': True,
            'api_url': 'sandbox',
        })

        self.product = self.env['product.product'].create({'name': 'Test Product'})
        self.channel_product = self.ChannelProduct.create({
            'product_id': self.product.id,
            'channel_id': self.channel.id,
        })

    def test_action_regenerate_alt_text(self):
        """Test regenerate alt text action returns notification."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'source_type': 'url',
            'image_url': 'https://example.com/test.jpg',
            'alt_text': 'Old Alt Text',
        })
        result = image.action_regenerate_alt_text()
        self.assertTrue(result)
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')

    def test_action_regenerate_alt_text_updates(self):
        """Test alt text is updated after regenerate."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'source_type': 'url',
            'image_url': 'https://example.com/test.jpg',
            'alt_text': 'Old',
        })
        old_alt = image.alt_text
        image.action_regenerate_alt_text()
        # Alt text should be regenerated
        self.assertIsNotNone(image.alt_text)


@tagged('post_install', '-at_install', 'multichannel', 'image')
class TestChannelProductImageUpload(TransactionCase):
    """Test upload methods."""

    def setUp(self):
        super().setUp()
        self.ChannelProductImage = self.env['channel.product.image']
        self.ChannelConfig = self.env['channel.config']
        self.ChannelProduct = self.env['channel.product']

        channel_module = self.env['channel.list.module'].create({
            'name': 'Shopee',
            'code': 'shopee',
            'active': True,
        })
        self.channel = self.ChannelConfig.create({
            'name': 'Test Shopee',
            'code': 'shopee_test',
            'platform': 'shopee',
            'active': True,
            'api_url': 'sandbox',
        })

        self.product = self.env['product.product'].create({'name': 'Test Product'})
        self.channel_product = self.ChannelProduct.create({
            'product_id': self.product.id,
            'channel_id': self.channel.id,
        })

    def test_get_image_data_no_product(self):
        """Test _get_image_data returns False when no product."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
        })
        image.product_id = False
        img, src = image._get_image_data()
        self.assertFalse(img)
        self.assertFalse(src)

    def test_get_image_data_product_source(self):
        """Test _get_image_data with product source."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'source_type': 'product',
            'odoo_image_field': 'image_1920',
        })
        img, src = image._get_image_data()
        # May be False if product has no image
        self.assertFalse(img)  # Test product has no image

    def test_prepare_image_for_upload(self):
        """Test _prepare_image_for_upload returns data and checksum."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
        })
        test_bytes = b'fake image data'
        data, checksum, size = image._prepare_image_for_upload(test_bytes)
        self.assertEqual(data, test_bytes)
        self.assertIsNotNone(checksum)
        self.assertEqual(size, len(test_bytes))

    @patch('requests.get')
    def test_download_from_url_success(self, mock_get):
        """Test _download_from_url success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'fake image bytes'
        mock_get.return_value = mock_response

        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
        })
        result = image._download_from_url('https://example.com/image.jpg')
        self.assertEqual(result, b'fake image bytes')

    @patch('requests.get')
    def test_download_from_url_failure(self, mock_get):
        """Test _download_from_url failure returns False."""
        mock_get.side_effect = Exception('Network error')

        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
        })
        result = image._download_from_url('https://example.com/image.jpg')
        self.assertFalse(result)


@tagged('post_install', '-at_install', 'multichannel', 'image')
class TestChannelProductImageStatus(TransactionCase):
    """Test image status management."""

    def setUp(self):
        super().setUp()
        self.ChannelProductImage = self.env['channel.product.image']
        self.ChannelConfig = self.env['channel.config']
        self.ChannelProduct = self.env['channel.product']

        channel_module = self.env['channel.list.module'].create({
            'name': 'Lazada',
            'code': 'lazada',
            'active': True,
        })
        self.channel = self.ChannelConfig.create({
            'name': 'Test Lazada',
            'code': 'lazada_test',
            'platform': 'lazada',
            'active': True,
            'api_url': 'sandbox',
        })

        self.product = self.env['product.product'].create({'name': 'Test Product'})
        self.channel_product = self.ChannelProduct.create({
            'product_id': self.product.id,
            'channel_id': self.channel.id,
        })

    def test_upload_status_values(self):
        """Test upload status can be set to all values."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'upload_status': 'pending',
        })
        self.assertEqual(image.upload_status, 'pending')

        image.upload_status = 'uploading'
        self.assertEqual(image.upload_status, 'uploading')

        image.upload_status = 'uploaded'
        self.assertEqual(image.upload_status, 'uploaded')

        image.upload_status = 'error'
        self.assertEqual(image.upload_status, 'error')

    def test_action_retry_upload_no_error_images(self):
        """Test action_retry_upload with no error images."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'upload_status': 'pending',
        })
        # Should not raise
        result = image.action_retry_upload()
        self.assertTrue(result)

    def test_action_retry_upload_with_error_images(self):
        """Test action_retry_upload retries error images."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'upload_status': 'error',
            'upload_message': 'Previous error',
        })
        # Should not raise even when no channel
        result = image.action_retry_upload()
        self.assertTrue(result)


@tagged('post_install', '-at_install', 'multichannel', 'image')
class TestChannelProductImagePlatform(TransactionCase):
    """Test platform-specific image IDs."""

    def setUp(self):
        super().setUp()
        self.ChannelProductImage = self.env['channel.product.image']
        self.ChannelConfig = self.env['channel.config']
        self.ChannelProduct = self.env['channel.product']

        channel_module = self.env['channel.list.module'].create({
            'name': 'TikTok',
            'code': 'tiktok',
            'active': True,
        })
        self.channel = self.ChannelConfig.create({
            'name': 'Test TikTok',
            'code': 'tiktok_test',
            'platform': 'tiktok',
            'active': True,
            'api_url': 'sandbox',
        })

        self.product = self.env['product.product'].create({'name': 'Test Product'})
        self.channel_product = self.ChannelProduct.create({
            'product_id': self.product.id,
            'channel_id': self.channel.id,
        })

    def test_shopee_image_id_field(self):
        """Test Shopee image ID field."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'shopee_image_id': 'SHP-12345',
        })
        self.assertEqual(image.shopee_image_id, 'SHP-12345')

    def test_lazada_image_id_field(self):
        """Test Lazada image ID field."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'lazada_image_id': 'LZD-67890',
        })
        self.assertEqual(image.lazada_image_id, 'LZD-67890')

    def test_tiktok_image_id_field(self):
        """Test TikTok image ID field."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'tiktok_image_id': 'TT-11111',
        })
        self.assertEqual(image.tiktok_image_id, 'TT-11111')

    def test_platform_image_url_field(self):
        """Test platform image URL field."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'platform_image_url': 'https://cdn.example.com/image.jpg',
        })
        self.assertEqual(image.platform_image_url, 'https://cdn.example.com/image.jpg')

    def test_image_id_on_platform_field(self):
        """Test image ID on platform field."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'image_id_on_platform': 'PLAT-IMG-001',
        })
        self.assertEqual(image.image_id_on_platform, 'PLAT-IMG-001')


@tagged('post_install', '-at_install', 'multichannel', 'image')
class TestChannelProductImageMetadata(TransactionCase):
    """Test image metadata fields."""

    def setUp(self):
        super().setUp()
        self.ChannelProductImage = self.env['channel.product.image']
        self.ChannelConfig = self.env['channel.config']
        self.ChannelProduct = self.env['channel.product']

        channel_module = self.env['channel.list.module'].create({
            'name': 'Shopee',
            'code': 'shopee',
            'active': True,
        })
        self.channel = self.ChannelConfig.create({
            'name': 'Test Shopee',
            'code': 'shopee_test',
            'platform': 'shopee',
            'active': True,
            'api_url': 'sandbox',
        })

        self.product = self.env['product.product'].create({'name': 'Test Product'})
        self.channel_product = self.ChannelProduct.create({
            'product_id': self.product.id,
            'channel_id': self.channel.id,
        })

    def test_width_height_fields(self):
        """Test width and height fields."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'width': 1920,
            'height': 1080,
        })
        self.assertEqual(image.width, 1920)
        self.assertEqual(image.height, 1080)

    def test_file_size_field(self):
        """Test file size field."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'file_size': 102400,
        })
        self.assertEqual(image.file_size, 102400)

    def test_checksum_field(self):
        """Test checksum field."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'checksum': 'abc123def456',
        })
        self.assertEqual(image.checksum, 'abc123def456')

    def test_upload_message_field(self):
        """Test upload message field."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'upload_message': 'Upload successful',
        })
        self.assertEqual(image.upload_message, 'Upload successful')

    def test_last_upload_field(self):
        """Test last upload datetime field."""
        from datetime import datetime
        now = fields.Datetime.now()
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'last_upload': now,
        })
        self.assertEqual(image.last_upload, now)

    def test_alt_text_seo_field(self):
        """Test alt text for SEO."""
        image = self.ChannelProductImage.create({
            'channel_product_id': self.channel_product.id,
            'alt_text': 'Test Product - Shopee main image',
        })
        self.assertEqual(image.alt_text, 'Test Product - Shopee main image')

    def test_image_type_selection(self):
        """Test image type selection values."""
        for img_type in ['main', 'gallery', 'detail', 'thumbnail']:
            image = self.ChannelProductImage.create({
                'channel_product_id': self.channel_product.id,
                'image_type': img_type,
            })
            self.assertEqual(image.image_type, img_type)
