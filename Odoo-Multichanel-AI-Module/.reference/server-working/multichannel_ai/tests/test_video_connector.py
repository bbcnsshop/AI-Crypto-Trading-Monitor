# -*- coding: utf-8 -*-
"""Test Channel Product Video with new _upload_to_connector() method (Phase 11.1)."""
from odoo.tests import TransactionCase, tagged
from unittest.mock import patch, MagicMock


@tagged('post_install', '-at_install', 'multichannel', 'video')
class TestVideoConnector(TransactionCase):
    """Test _upload_to_connector() refactored from 3 separate methods."""

    def setUp(self):
        super(TestVideoConnector, self).setUp()
        self.ChannelConfig = self.env['channel.config']
        self.ChannelProduct = self.env['channel.product']
        self.ChannelProductVideo = self.env['channel.product.video']
        
        # Create test channel
        self.channel_shopee = self.ChannelConfig.create({
            'name': 'Shopee Test',
            'code': 'shopee_test',
            'active': True,
            'use_mock_data': True,
        })

    def test_upload_to_connector_uses_factory(self):
        """Test that _upload_to_connector uses factory pattern."""
        # Create a channel product video
        video = self.ChannelProductVideo.create({
            'name': 'Test Video',
            'channel_id': self.channel_shopee.id,
            'video_url': 'https://example.com/test.mp4',
            'state': 'ready',
        })
        
        # Mock the connector factory
        with patch('odoo.addons.multichannel_ai.models.connectors.get_connector') as mock_factory:
            mock_connector = MagicMock()
            mock_connector.upload_video = MagicMock(return_value={
                'success': True,
                'video_id': 'mock_video_123',
            })
            mock_factory.return_value = mock_connector
            
            # Call _upload_to_connector
            video_data = {
                'name': 'Test Video',
                'url': 'https://example.com/test.mp4',
            }
            result = video._upload_to_connector(video_data)
            
            # Verify factory was called
            self.assertTrue(mock_factory.called)
            self.assertTrue(result.get('success'))

    def test_upload_to_connector_fallback_to_mixin(self):
        """Test that _upload_to_connector falls back to channel mixin get_connector()."""
        # Create channel with get_connector method (from mixin)
        channel = self.ChannelConfig.create({
            'name': 'Channel with Mixin',
            'code': 'channel_mixin',
            'active': True,
        })
        
        # Add get_connector to channel
        if not hasattr(channel, 'get_connector'):
            # Skip if mixin not available
            self.skipTest('Channel mixin get_connector not available')
        
        video = self.ChannelProductVideo.create({
            'name': 'Test Video 2',
            'channel_id': channel.id,
            'video_url': 'https://example.com/test2.mp4',
            'state': 'ready',
        })
        
        video_data = {
            'name': 'Test Video 2',
            'url': 'https://example.com/test2.mp4',
        }
        
        try:
            result = video._upload_to_connector(video_data)
            # Should return some result (success or error)
            self.assertIn('success', result)
        except Exception as e:
            # If connector not available, should return error gracefully
            self.assertIn('error', str(e).lower() or 'success' in str(e).lower())

    def test_upload_to_connector_handles_exception(self):
        """Test that _upload_to_connector handles exceptions gracefully."""
        video = self.ChannelProductVideo.create({
            'name': 'Test Video Error',
            'channel_id': self.channel_shopee.id,
            'video_url': 'https://example.com/test.mp4',
            'state': 'ready',
        })
        
        # Mock factory to raise exception
        with patch('odoo.addons.multichannel_ai.models.connectors.get_connector') as mock_factory:
            mock_factory.side_effect = Exception('Mock error')
            
            video_data = {'name': 'Test', 'url': 'https://example.com/test.mp4'}
            result = video._upload_to_connector(video_data)
            
            # Should catch exception and return error
            self.assertFalse(result.get('success'))
            self.assertIn('error', result)


@tagged('post_install', '-at_install', 'multichannel', 'video')
class TestVideoConnectorSingleSource(TransactionCase):
    """Verify that old _upload_to_shopee/lazada/tiktok methods are removed."""

    def test_old_methods_removed(self):
        """Test that old platform-specific upload methods are gone."""
        video_model = self.env['channel.product.video']
        
        # Old methods should NOT exist
        self.assertFalse(
            hasattr(video_model, '_upload_to_shopee'),
            '_upload_to_shopee should be removed (refactored to _upload_to_connector)'
        )
        self.assertFalse(
            hasattr(video_model, '_upload_to_lazada'),
            '_upload_to_lazada should be removed'
        )
        self.assertFalse(
            hasattr(video_model, '_upload_to_tiktok'),
            '_upload_to_tiktok should be removed'
        )
        
        # New method SHOULD exist
        self.assertTrue(
            hasattr(video_model, '_upload_to_connector'),
            '_upload_to_connector should exist (single source of truth)'
        )
