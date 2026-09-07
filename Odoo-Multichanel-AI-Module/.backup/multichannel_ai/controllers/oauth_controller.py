# -*- coding: utf-8 -*-
"""
OAuth Controller for Multi-Channel Integration
Handles OAuth flow for Shopee, Lazada, TikTok Shop
"""
from odoo import http, _
from odoo.http import request
from datetime import timedelta
import logging
import time
import hashlib
import hmac
import urllib.parse

_logger = logging.getLogger(__name__)


class OAuthController(http.Controller):

    # ===========================
    # Route 1: Authorize - Redirect to Platform
    # ===========================
    @http.route('/multichannel/oauth/<int:channel_id>/authorize',
                type='http', auth='user', website=True)
    def oauth_authorize(self, channel_id, **kwargs):
        """Redirect user to platform OAuth page"""
        channel = request.env['channel.config'].browse(channel_id)
        if not channel.exists():
            return request.not_found()

        channel_code = channel.channel_code or channel.code
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        callback_url = f"{base_url}/multichannel/oauth/{channel_id}/callback"

        try:
            if channel_code == 'shopee':
                redirect_url = self._shopee_get_auth_url(channel, callback_url)
            elif channel_code == 'lazada':
                redirect_url = self._lazada_get_auth_url(channel, callback_url)
            elif channel_code == 'tiktok':
                redirect_url = self._tiktok_get_auth_url(channel, callback_url)
            else:
                return request.render('multichannel_ai.oauth_error', {
                    'message': f'Unknown channel: {channel_code}'
                })

            _logger.info(f'OAuth redirect for {channel_code}')
            return request.redirect(redirect_url)

        except Exception as e:
            _logger.error(f'OAuth authorize error: {e}')
            return request.render('multichannel_ai.oauth_error', {
                'message': str(e)
            })

    # ===========================
    # Route 2: Callback - Handle OAuth Response
    # ===========================
    @http.route('/multichannel/oauth/<int:channel_id>/callback',
                type='http', auth='public', website=True)
    def oauth_callback(self, channel_id, **kwargs):
        """Handle OAuth callback from platform"""
        channel = request.env['channel.config'].browse(channel_id)
        if not channel.exists():
            return request.not_found()

        code = kwargs.get('code')
        error = kwargs.get('error')
        error_desc = kwargs.get('error_description', '')

        if error:
            return request.redirect(
                f'/web#id={channel.id}&model=channel.config&view_type=form&error={error}'
            )

        if not code:
            return request.redirect(
                f'/web#id={channel.id}&model=channel.config&view_type=form&error=no_code'
            )

        channel_code = channel.channel_code or channel.code

        try:
            if channel_code == 'shopee':
                token_data = self._shopee_exchange_code(channel, code)
            elif channel_code == 'lazada':
                token_data = self._lazada_exchange_code(channel, code)
            elif channel_code == 'tiktok':
                token_data = self._tiktok_exchange_code(channel, code)
            else:
                token_data = None

            if token_data:
                channel.write({
                    'access_token': token_data.get('access_token'),
                    'refresh_token': token_data.get('refresh_token'),
                    'token_expire_date': token_data.get('expire_date'),
                })
                _logger.info(f'OAuth success for {channel.name}')
                # Redirect ไป Form View
                return request.redirect(
                    f'/web#id={channel.id}&model=channel.config&view_type=form'
                )
            else:
                return request.redirect(
                    f'/web#id={channel.id}&model=channel.config&view_type=form&error=oauth_failed'
                )

        except Exception as e:
            _logger.error(f'OAuth callback error: {e}')
            return request.render('multichannel_ai.oauth_error', {
                'message': str(e)
            })
            return request.render('multichannel_ai.oauth_error', {
                'message': str(e)
            })

    # ===========================
    # Shopee OAuth Methods
    # ===========================
    def _shopee_get_auth_url(self, channel, callback_url):
        """Generate Shopee authorization URL"""
        timestamp = str(int(time.time()))
        partner_id = channel.api_key or '0'
        path = '/api/v1/shop/auth_partner'
        sign_string = f"{partner_id}{path}{timestamp}"
        signature = hmac.new(
            (channel.api_secret or '').encode(),
            sign_string.encode(),
            hashlib.sha256
        ).hexdigest()
        params = {
            'partner_id': partner_id,
            'redirect': callback_url,
            'sign': signature,
            'timestamp': timestamp,
        }
        auth_url = 'https://partner.shopeemobile.com/api/v1/shop/auth_partner'
        return f"{auth_url}?{urllib.parse.urlencode(params)}"

    def _shopee_exchange_code(self, channel, code):
        """Exchange Shopee code - MOCK"""
        _logger.warning('Shopee OAuth is MOCK - no real API')
        from odoo.fields import Datetime
        return {
            'access_token': f'shopee_mock_token_{time.time()}',
            'refresh_token': f'shopee_mock_refresh_{time.time()}',
            'expire_date': Datetime.now() + timedelta(days=30),
        }

    # ===========================
    # Lazada OAuth Methods
    # ===========================
    def _lazada_get_auth_url(self, channel, callback_url):
        """Generate Lazada authorization URL"""
        app_key = channel.api_key or ''
        params = {
            'app_key': app_key,
            'redirect_uri': callback_url,
            'response_type': 'code',
            'state': str(channel.id),
        }
        auth_url = 'https://auth.lazada.com/oauth/authorize'
        return f"{auth_url}?{urllib.parse.urlencode(params)}"

    def _lazada_exchange_code(self, channel, code):
        """Exchange Lazada code - MOCK"""
        _logger.warning('Lazada OAuth is MOCK - no real API')
        from odoo.fields import Datetime
        return {
            'access_token': f'lazada_mock_token_{time.time()}',
            'refresh_token': f'lazada_mock_refresh_{time.time()}',
            'expire_date': Datetime.now() + timedelta(days=30),
        }

    # ===========================
    # TikTok OAuth Methods
    # ===========================
    def _tiktok_get_auth_url(self, channel, callback_url):
        """Generate TikTok authorization URL"""
        app_key = channel.api_key or ''
        params = {
            'app_key': app_key,
            'redirect_uri': callback_url,
            'response_type': 'code',
            'state': str(channel.id),
        }
        auth_url = 'https://auth.tiktok-shops.com/oauth/authorize'
        return f"{auth_url}?{urllib.parse.urlencode(params)}"

    def _tiktok_exchange_code(self, channel, code):
        """Exchange TikTok code - MOCK"""
        _logger.warning('TikTok OAuth is MOCK - no real API')
        from odoo.fields import Datetime
        return {
            'access_token': f'tiktok_mock_token_{time.time()}',
            'refresh_token': f'tiktok_mock_refresh_{time.time()}',
            'expire_date': Datetime.now() + timedelta(days=30),
        }