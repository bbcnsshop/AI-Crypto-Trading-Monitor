# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class TokenActionsMixin(models.AbstractModel):
    """Mixin: token refresh + cron job."""
    _name = 'channel.token.actions'
    _description = 'Channel Token Actions'

    def action_refresh_token(self):
        self.ensure_one()
        try:
            data = self._do_refresh_token()
            self.write({
                'access_token': data.get('access_token'),
                'refresh_token': data.get('refresh_token'),
                'token_expire_date': data.get('expire_date'),
            })
            return self._notification('success', _('Token refreshed (MOCK)'))
        except Exception as e:
            _logger.error('Refresh token failed: %s', e)
            return self._notification('danger', _('Refresh failed: %s' % str(e)))

    def _do_refresh_token(self):
        """Helper: refresh token API call (currently MOCK)."""
        self.ensure_one()
        return {
            'access_token': 'mock_token_%s' % fields.Datetime.now(),
            'refresh_token': self.refresh_token,
            'expire_date': fields.Datetime.now() + timedelta(days=30),
        }

    @api.model
    def cron_refresh_expiring_tokens(self):
        """Cron: refresh tokens expiring within 7 days."""
        threshold = fields.Datetime.now() + timedelta(days=7)
        configs = self.search([
            ('active', '=', True),
            ('refresh_token', '!=', False),
            ('token_expire_date', '<=', threshold),
        ])
        for config in configs:
            try:
                config.action_refresh_token()
            except Exception as e:
                _logger.error('Auto refresh failed for %s: %s', config.name, e)
        return True
