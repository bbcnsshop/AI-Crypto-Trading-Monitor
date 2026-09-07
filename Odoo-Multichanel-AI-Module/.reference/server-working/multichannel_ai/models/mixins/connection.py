# -*- coding: utf-8 -*-
from odoo import models, api, _
import logging

_logger = logging.getLogger(__name__)


class ConnectionMixin(models.AbstractModel):
    """Mixin: connector factory + test connection."""
    _name = 'channel.connection'
    _description = 'Channel Connection'

    def get_connector(self):
        """Return appropriate connector instance based on platform."""
        self.ensure_one()
        if self.api_url == 'sandbox':
            from odoo.addons.multichannel_ai.models.connectors.mock_data import MockConnector
            return MockConnector(self)
        platform = self.platform
        if platform == 'shopee':
            from odoo.addons.multichannel_ai.models.connectors.shopee import ShopeeConnector
            return ShopeeConnector(self)
        if platform == 'lazada':
            from odoo.addons.multichannel_ai.models.connectors.lazada import LazadaConnector
            return LazadaConnector(self)
        if platform == 'tiktok':
            from odoo.addons.multichannel_ai.models.connectors.tiktok import TikTokConnector
            return TikTokConnector(self)
        from odoo.addons.multichannel_ai.models.connectors.base import BaseConnector
        return BaseConnector(self)

    def action_test_connection(self):
        """Test API connection using connector."""
        self.ensure_one()
        try:
            connector = self.get_connector()
            if hasattr(connector, 'get_products'):
                connector.get_products(page=1, limit=1)
            else:
                connector.test_connection()
            mode = 'MOCK (Sandbox)' if (self.api_url == 'sandbox') else 'Production (Real API)'
            return self._notification('success', _('Connection OK! (%s)' % mode))
        except NotImplementedError:
            return self._notification('warning',
                _('Production API not implemented. Use Sandbox mode.'))
        except Exception as e:
            _logger.error('Test connection failed: %s', e)
            return self._notification('danger', _('Connection failed: %s' % str(e)))

    def _notification(self, type_, message):
        """Helper: display notification action."""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Channel'),
                'message': message,
                'type': type_,
            }
        }
