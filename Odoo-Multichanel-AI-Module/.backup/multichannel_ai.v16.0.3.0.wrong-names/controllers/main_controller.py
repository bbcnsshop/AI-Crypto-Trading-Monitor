# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessDenied
import json
import logging

_logger = logging.getLogger(__name__)


def _ensure_multichannel_user():
    """Ensure user has at least 'multichannel_ai.group_multichannel_user' group."""
    if not request.env.user.has_group('multichannel_ai.group_multichannel_user'):
        raise AccessDenied(_("You don't have access to Multi-Channel. Please contact your administrator."))


def _ensure_multichannel_manager():
    """Ensure user has 'multichannel_ai.group_multichannel_manager' group (admin actions)."""
    if not request.env.user.has_group('multichannel_ai.group_multichannel_manager'):
        raise AccessDenied(_("This action requires Multi-Channel Manager role."))


class MainController(http.Controller):
    """Main Controller for Multi-Channel E-Commerce (Frontend for Staff/Manager)."""
    
    @http.route('/multichannel/dashboard', type='http', auth='user', website=False)
    def dashboard(self, **kwargs):
        """Dashboard showing all channel summaries"""
        _ensure_multichannel_user()
        channels = request.env['channel.config'].search([])
        
        # Get summary data for each channel
        summary_data = []
        for channel in channels:
            product_count = request.env['channel.product'].search_count([
                ('channel_id', '=', channel.id),
                ('state', '=', 'active')
            ])
            order_count = request.env['channel.order'].search_count([
                ('channel_id', '=', channel.id)
            ])
            pending_order = request.env['channel.order'].search_count([
                ('channel_id', '=', channel.id),
                ('state', '=', 'pending')
            ])
            
            summary_data.append({
                'channel': channel,
                'product_count': product_count,
                'order_count': order_count,
                'pending_order': pending_order,
            })
        
        return request.render('multichannel_ai.dashboard_template', {
            'summary_data': summary_data,
        })
    
    @http.route('/multichannel', type='http', auth='user', website=False)
    def index(self, **kwargs):
        """Redirect to dashboard"""
        _ensure_multichannel_user()
        return request.redirect('/multichannel/dashboard')

    @http.route('/multichannel/channels', type='http', auth='user', website=False)
    def channels_page(self, **kwargs):
        """Channels management page"""
        _ensure_multichannel_user()
        channels = request.env['channel.config'].search([])
        return request.render('multichannel_ai.channels_template', {
            'channels': channels,
        })

    @http.route('/multichannel/products', type='http', auth='user', website=False,
                methods=['GET', 'POST'])
    def products_page(self, channel=None, state=None, search=None, page=1, **kwargs):
        """Channel products list page with filters and pagination"""
        _ensure_multichannel_user()
        page = int(page) if page else 1
        per_page = 25

        domain = []
        if channel:
            domain.append(('channel_id', '=', int(channel)))
        if state:
            domain.append(('state', '=', state))
        if search:
            domain.append(('product_id.name', 'ilike', search))

        total = request.env['channel.product'].search_count(domain)
        total_pages = max(1, (total + per_page - 1) // per_page)
        offset = (page - 1) * per_page

        products = request.env['channel.product'].search(
            domain, limit=per_page, offset=offset, order='id desc'
        )
        channels = request.env['channel.config'].search([])

        return request.render('multichannel_ai.channel_products_template', {
            'products': products,
            'channels': channels,
            'channel_id': channel,
            'state': state,
            'search': search,
            'page': page,
            'total_pages': total_pages,
        })

    @http.route('/multichannel/sync', type='http', auth='user', website=False)
    def sync_page(self, **kwargs):
        """Manual sync page (Manager only for full sync)"""
        _ensure_multichannel_user()
        channels = request.env['channel.config'].search([])
        ch_stats = {}
        for ch in channels:
            ch_stats[ch.id] = {
                'total': request.env['channel.product'].search_count(
                    [('channel_id', '=', ch.id)]
                ),
                'synced': request.env['channel.product'].search_count([
                    ('channel_id', '=', ch.id),
                    ('sync_status', '=', 'synced'),
                ]),
                'pending': request.env['channel.product'].search_count([
                    ('channel_id', '=', ch.id),
                    ('sync_status', '=', 'pending'),
                ]),
                'error': request.env['channel.product'].search_count([
                    ('channel_id', '=', ch.id),
                    ('sync_status', '=', 'error'),
                ]),
            }
        return request.render('multichannel_ai.sync_template', {
            'channels': channels,
            'ch_stats': ch_stats,
        })

    @http.route('/multichannel/orders', type='http', auth='user', website=False)
    def orders_page(self, **kwargs):
        """Orders list page"""
        _ensure_multichannel_user()
        orders = request.env['channel.order'].search(
            [], limit=50, order='create_date desc'
        )
        return request.render('multichannel_ai.dashboard_template', {
            'summary_data': [],
            'orders': orders,
        })

    @http.route('/multichannel/api/sync_product', type='json', auth='user')
    def api_sync_product(self, product_id=None, **kwargs):
        """API: Sync single channel product (Manager only)"""
        _ensure_multichannel_manager()
        if not product_id:
            return {'success': False, 'error': 'Missing product_id'}
        try:
            cp = request.env['channel.product'].browse(int(product_id))
            if not cp.exists():
                return {'success': False, 'error': 'Product not found'}
            cp.sync_to_channel()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/multichannel/api/sync_channel', type='json', auth='user')
    def api_sync_channel(self, channel_id=None, **kwargs):
        """API: Sync all products in a channel (Manager only)"""
        _ensure_multichannel_manager()
        if not channel_id:
            return {'success': False, 'error': 'Missing channel_id'}
        try:
            products = request.env['channel.product'].search([
                ('channel_id', '=', int(channel_id)),
                ('state', 'in', ('active', 'draft')),
            ])
            synced = 0
            errors = 0
            for cp in products:
                try:
                    cp.sync_to_channel()
                    synced += 1
                except Exception:
                    errors += 1
            return {
                'success': True,
                'count': synced,
                'errors': errors,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route('/multichannel/api/products', type='json', auth='user', methods=['GET'])
    def get_products(self, channel_id=None, **kwargs):
        """API to get products for a channel (User can read)"""
        _ensure_multichannel_user()
        domain = [('state', '=', 'active')]
        if channel_id:
            domain.append(('channel_id', '=', int(channel_id)))
        
        products = request.env['channel.product'].search_read(domain, [
            'name', 'channel_id', 'channel_price', 'qty_available', 'state'
        ])
        
        return products
    
    @http.route('/multichannel/api/pricing', type='json', auth='user', methods=['POST'])
    def calculate_pricing(self, **kwargs):
        """API to calculate pricing with AI (optional).
        
        Uses ai_engine if available, falls back to formula-based pricing.
        """
        product_id = kwargs.get('product_id')
        channel_code = kwargs.get('channel_code')
        
        if not product_id or not channel_code:
            return {'error': 'Missing product_id or channel_code'}
        
        product = request.env['product.product'].browse(int(product_id))
        
        product_data = {
            'name': product.display_name,
            'cost': product.standard_price,
            'category': product.categ_id.name if product.categ_id else 'IT Equipment'
        }
        
        # Try AI, fallback to formula
        try:
            ai_engine = request.env['multichannel.ai.engine'].get_default_engine()
            result = ai_engine.recommend_price(product_data, channel_code)
        except Exception as e:
            _logger.info('AI pricing not available, using formula: %s', str(e))
            # Formula fallback
            result = self._formula_price_recommendation(product_data, channel_code)
        
        return result
    
    def _formula_price_recommendation(self, product_data, channel_code='shopee', target_margin=30.0):
        """Formula-based price recommendation (fallback when AI not available)."""
        cost = product_data.get('cost', 0) or 0
        vat_rate = 7.0
        
        # Fee config for channel
        fee_configs = {
            'shopee': {'commission': 5.0, 'payment_fee': 2.0, 'shipping_subsidy': 2.5},
            'lazada': {'commission': 5.0, 'payment_fee': 2.0, 'shipping_subsidy': 3.0},
            'tiktok': {'commission': 3.5, 'payment_fee': 1.5, 'shipping_subsidy': 2.0},
        }
        fee = fee_configs.get(channel_code, fee_configs['shopee'])
        
        commission = fee['commission']
        payment_fee = fee['payment_fee']
        shipping_subsidy = fee['shipping_subsidy']
        
        total_fee_pct = (commission + payment_fee + shipping_subsidy) / 100.0
        vat_factor = 1 + vat_rate / 100.0
        divisor = (1 - total_fee_pct) * vat_factor
        
        if divisor <= 0:
            divisor = 0.7
        
        selling_price = max(cost, cost * (1 + target_margin / 100.0) / divisor)
        
        return {
            'selling_price': round(selling_price, 2),
            'cost': cost,
            'target_margin': target_margin,
            'channel': channel_code,
            'fee_breakdown': fee,
            '_source': 'formula',
        }

    @http.route('/multichannel/field_mappings', type='http', auth='user', website=False)
    def field_mappings_page(self, channel_id=None, **kwargs):
        """Field Mappings management page"""
        _ensure_multichannel_user()
        channels = request.env['channel.config'].search([('active', '=', True)])
        domain = []
        if channel_id:
            domain.append(('channel_id', '=', int(channel_id)))
        mappings = request.env['channel.product.field.mapping'].search(
            domain, order='channel_id, sequence, id'
        )
        return request.render('multichannel_ai.field_mappings_template', {
            'channels': channels,
            'mappings': mappings,
            'selected_channel_id': int(channel_id) if channel_id else None,
        })

    @http.route('/multichannel/api/field_mappings', type='json', auth='user', methods=['GET'])
    def get_field_mappings(self, channel_id=None, **kwargs):
        """API to get field mappings (User can read)"""
        _ensure_multichannel_user()
        domain = [('active', '=', True)]
        if channel_id:
            domain.append(('channel_id', '=', int(channel_id)))
        mappings = request.env['channel.product.field.mapping'].search_read(
            domain, ['id', 'channel_id', 'odoo_field', 'platform_field',
                    'transform_type', 'default_value', 'is_required',
                    'transform_value', 'description', 'sequence']
        )
        return {'success': True, 'mappings': mappings}

    @http.route('/multichannel/api/field_mappings', type='json', auth='user', methods=['POST'])
    def create_field_mapping(self, **kwargs):
        """API to create field mapping (Manager only)"""
        _ensure_multichannel_manager()
        try:
            mapping = request.env['channel.product.field.mapping'].create(kwargs)
            return {'success': True, 'id': mapping.id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/multichannel/api/field_mappings/<int:mapping_id>', type='json', auth='user', methods=['PUT'])
    def update_field_mapping(self, mapping_id, **kwargs):
        """API to update field mapping (Manager only)"""
        _ensure_multichannel_manager()
        try:
            mapping = request.env['channel.product.field.mapping'].browse(mapping_id)
            if not mapping.exists():
                return {'success': False, 'error': 'Mapping not found'}
            mapping.write(kwargs)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/multichannel/api/field_mappings/<int:mapping_id>', type='json', auth='user', methods=['DELETE'])
    def delete_field_mapping(self, mapping_id, **kwargs):
        """API to delete field mapping (Manager only)"""
        _ensure_multichannel_manager()
        try:
            mapping = request.env['channel.product.field.mapping'].browse(mapping_id)
            if not mapping.exists():
                return {'success': False, 'error': 'Mapping not found'}
            mapping.unlink()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}