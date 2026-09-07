# -*- coding: utf-8 -*-
from odoo import models, api, _
import logging

_logger = logging.getLogger(__name__)


class SyncActionsMixin(models.AbstractModel):
    """Mixin: sync products/orders from channel."""
    _name = 'channel.sync.actions'
    _description = 'Channel Sync Actions'

    def action_sync_products(self):
        self.ensure_one()
        try:
            connector = self.get_connector()
            result = connector.get_products(page=1, limit=50)
            return self._notification('success',
                _('Synced %d products (MOCK)' % len(result.get('items', []))))
        except Exception as e:
            _logger.error('Sync products failed: %s', e)
            return self._notification('danger', _('Sync failed: %s' % str(e)))

    def action_sync_orders(self):
        self.ensure_one()
        try:
            connector = self.get_connector()
            result = connector.get_orders()
            return self._notification('success',
                _('Synced %d orders (MOCK)' % len(result.get('orders', []))))
        except Exception as e:
            _logger.error('Sync orders failed: %s', e)
            return self._notification('danger', _('Sync failed: %s' % str(e)))
