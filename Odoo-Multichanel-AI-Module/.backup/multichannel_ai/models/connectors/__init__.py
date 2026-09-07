# -*- coding: utf-8 -*-
"""
Channel Connectors Package
Base class + Platform-specific connectors (MOCK mode by default)
"""
from .base import ChannelConnectorBase
from .mock_data import MOCK, MockData
from .shopee import ShopeeConnector
from .lazada import LazadaConnector
from .tiktok import TikTokConnector

# Factory function to get connector
def get_connector(channel_config):
    """Get connector instance based on channel code"""
    code = (channel_config.channel_code or channel_config.code or '').lower()
    if code == 'shopee':
        return ShopeeConnector(channel_config)
    elif code == 'lazada':
        return LazadaConnector(channel_config)
    elif code == 'tiktok':
        return TikTokConnector(channel_config)
    else:
        return ChannelConnectorBase(channel_config)

__all__ = [
    'ChannelConnectorBase',
    'MockData',
    'MOCK',
    'ShopeeConnector',
    'LazadaConnector',
    'TikTokConnector',
    'get_connector',
]
