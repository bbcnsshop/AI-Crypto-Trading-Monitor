# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class WebhookController(http.Controller):
    """Webhook Controller for receiving order notifications"""
    
    @http.route('/multichannel/shopee/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def shopee_webhook(self, **kwargs):
        """Shopee webhook endpoint"""
        try:
            data = json.loads(request.httprequest.data)
            _logger.info(f"Shopee webhook received: {data}")
            
            # Process the order data
            channel = request.env['channel.config'].sudo().search([('code', '=', 'shopee')], limit=1)
            if channel:
                order = request.env['channel.order'].sudo().create_from_webhook(data)
                if order and channel.auto_sync_orders:
                    order.action_create_sale_order()
            
            return {'status': 'success'}
        except Exception as e:
            _logger.error(f"Shopee webhook error: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @http.route('/multichannel/lazada/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def lazada_webhook(self, **kwargs):
        """Lazada webhook endpoint"""
        try:
            data = json.loads(request.httprequest.data)
            _logger.info(f"Lazada webhook received: {data}")
            
            channel = request.env['channel.config'].sudo().search([('code', '=', 'lazada')], limit=1)
            if channel:
                order = request.env['channel.order'].sudo().create_from_webhook(data)
                if order and channel.auto_sync_orders:
                    order.action_create_sale_order()
            
            return {'status': 'success'}
        except Exception as e:
            _logger.error(f"Lazada webhook error: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @http.route('/multichannel/tiktok/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def tiktok_webhook(self, **kwargs):
        """TikTok Shop webhook endpoint"""
        try:
            data = json.loads(request.httprequest.data)
            _logger.info(f"TikTok webhook received: {data}")
            
            channel = request.env['channel.config'].sudo().search([('code', '=', 'tiktok')], limit=1)
            if channel:
                order = request.env['channel.order'].sudo().create_from_webhook(data)
                if order and channel.auto_sync_orders:
                    order.action_create_sale_order()
            
            return {'status': 'success'}
        except Exception as e:
            _logger.error(f"TikTok webhook error: {str(e)}")
            return {'status': 'error', 'message': str(e)}