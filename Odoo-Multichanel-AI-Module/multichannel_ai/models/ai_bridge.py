# -*- coding: utf-8 -*-
"""
AI Bridge Module
Wraps ai_engine calls with fallback to formula-based calculations

This module provides optional AI functionality:
- When ai_engine is installed: Full AI-powered features
- When ai_engine is NOT installed: Formula-based fallbacks

Usage:
    class MyModel(models.Model, AIAvailabilityMixin):
        _inherit = 'my.model'
        
        def my_method(self):
            if self.is_ai_available():
                # Use AI
                engine = self.get_ai_engine()
                result = engine.recommend_price(...)
            else:
                # Use formula fallback
                result = self.formula_price_recommendation(...)
"""
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class AIAvailabilityMixin(models.AbstractModel):
    """Mixin to check and access AI engine availability"""
    _name = 'ai.availability.mixin'
    _description = 'AI Availability Mixin'

    @api.model
    def is_ai_available(self):
        """Check if multichannel AI engine is configured.
        
        Returns:
            bool: True if AI engine is available, False otherwise
        """
        try:
            # Try to access ai.engine model
            self.env['ai.engine'].search([], limit=1)
            return True
        except Exception as e:
            _logger.debug('AI engine not available: %s', str(e))
            return False

    @api.model
    def get_ai_engine(self):
        """Get AI engine record if available, None otherwise.
        
        Returns:
            ai.engine recordset or None
        """
        try:
            return self.env['ai.engine'].get_default_engine()
        except Exception as e:
            _logger.debug('Could not get AI engine: %s', str(e))
            return None


class FormulaPricingMixin(models.AbstractModel):
    """Formula-based pricing when AI is not available.
    
    Provides the same interface as ai_engine but uses mathematical
    formulas instead of AI calls.
    """
    _name = 'formula.pricing.mixin'
    _description = 'Formula Pricing Mixin'

    # Default fee rates (Thai e-commerce platforms)
    _default_platform_fee = 5.0  # Shopee
    _default_payment_fee = 2.0
    _default_shipping_fee = 2.5
    _vat_rate = 7.0  # Thai VAT

    def calculate_profit(self, selling_price, cost, channel_code='shopee'):
        """Calculate profit breakdown using formula.
        
        Args:
            selling_price: Selling price (THB, inclusive VAT)
            cost: Product cost (THB)
            channel_code: Channel identifier ('shopee', 'lazada', 'tiktok')
            
        Returns:
            dict: Profit breakdown with keys:
                - selling_price, price_excl_vat, vat_collected
                - cost, gross_profit, gross_margin
                - platform_fee, payment_fee, shipping_subsidy, total_fees
                - net_profit, net_margin, break_even_price
        """
        fee_config = self._get_fee_config(channel_code)
        
        price_excl_vat = selling_price / (1 + self._vat_rate / 100)
        vat_collected = selling_price - price_excl_vat
        platform_fee = price_excl_vat * (fee_config['commission'] / 100)
        payment_fee = price_excl_vat * (fee_config['payment_fee'] / 100)
        shipping_subsidy = price_excl_vat * (fee_config['shipping_subsidy'] / 100)
        total_fees = platform_fee + payment_fee + shipping_subsidy
        gross_profit = price_excl_vat - cost
        net_profit = gross_profit - total_fees
        gross_margin = (gross_profit / price_excl_vat * 100) if price_excl_vat else 0
        net_margin = (net_profit / price_excl_vat * 100) if price_excl_vat else 0

        return {
            'selling_price': selling_price,
            'price_excl_vat': round(price_excl_vat, 2),
            'vat_collected': round(vat_collected, 2),
            'cost': cost,
            'gross_profit': round(gross_profit, 2),
            'gross_margin': round(gross_margin, 1),
            'platform_fee': round(platform_fee, 2),
            'payment_fee': round(payment_fee, 2),
            'shipping_subsidy': round(shipping_subsidy, 2),
            'total_fees': round(total_fees, 2),
            'net_profit': round(net_profit, 2),
            'net_margin': round(net_margin, 1),
            'break_even_price': round(cost + total_fees, 2),
        }

    def recommend_price(self, product_data, channel_code='shopee', target_margin=30.0):
        """Recommend selling price using formula.
        
        Args:
            product_data: dict with keys:
                - name: Product name (optional)
                - cost: Product cost (required)
                - margin: Target margin override (optional)
            channel_code: Channel identifier ('shopee', 'lazada', 'tiktok')
            target_margin: Target margin percentage (default: 30%)
            
        Returns:
            dict: Price recommendation with keys:
                - selling_price, cost, target_margin
                - channel, fee_breakdown
                - _source: 'formula'
        """
        cost = product_data.get('cost', 0) or 0
        margin_target = product_data.get('margin', target_margin) or target_margin
        fee_config = self._get_fee_config(channel_code)

        commission = fee_config['commission']
        payment_fee = fee_config['payment_fee']
        shipping_subsidy = fee_config['shipping_subsidy']
        
        total_fee_pct = (commission + payment_fee + shipping_subsidy) / 100.0
        vat_factor = 1 + self._vat_rate / 100.0
        divisor = (1 - total_fee_pct) * vat_factor
        
        if divisor <= 0:
            divisor = 0.7

        selling_price = max(cost, cost * (1 + margin_target / 100.0) / divisor)

        return {
            'selling_price': round(selling_price, 2),
            'cost': cost,
            'target_margin': margin_target,
            'channel': channel_code,
            'fee_breakdown': fee_config,
            '_source': 'formula',
        }

    def _get_fee_config(self, channel_code):
        """Get fee configuration for channel.
        
        Args:
            channel_code: Channel identifier
            
        Returns:
            dict: Fee config with commission, payment_fee, shipping_subsidy, name
        """
        fee_configs = {
            'shopee': {
                'commission': 5.0,
                'payment_fee': 2.0,
                'shipping_subsidy': 2.5,
                'name': 'Shopee'
            },
            'lazada': {
                'commission': 5.0,
                'payment_fee': 2.0,
                'shipping_subsidy': 3.0,
                'name': 'Lazada'
            },
            'tiktok': {
                'commission': 3.5,
                'payment_fee': 1.5,
                'shipping_subsidy': 2.0,
                'name': 'TikTok Shop'
            },
        }
        return fee_configs.get(
            channel_code,
            {
                'commission': self._default_platform_fee,
                'payment_fee': self._default_payment_fee,
                'shipping_subsidy': self._default_shipping_fee,
                'name': channel_code
            }
        )


class AIAwareMixin(models.AbstractModel):
    """Combined mixin for AI-aware operations.
    
    Use this mixin in models that need both AI availability check
    and formula-based fallbacks.
    """
    _name = 'ai.aware.mixin'
    _description = 'AI Aware Mixin'

    @api.model
    def get_pricing_engine(self):
        """Get pricing calculator (AI or formula).

        Returns:
            object: Either ai.engine or FormulaPricingMixin
        """
        # Try AI engine first
        try:
            return self.env['ai.engine'].get_default_engine()
        except Exception:
            # Fallback to formula
            return self

    @api.model
    def calculate_profit(self, selling_price, cost, channel_code='shopee'):
        """Calculate profit (AI if available, formula otherwise)."""
        try:
            engine = self.env['ai.engine'].get_default_engine()
            return engine.calculate_profit(selling_price, cost, channel_code)
        except Exception:
            # Use formula fallback
            return FormulaPricingMixin.calculate_profit(self, selling_price, cost, channel_code)

    @api.model
    def recommend_price(self, product_data, channel_code='shopee', target_margin=30.0):
        """Recommend price (AI if available, formula otherwise)."""
        try:
            engine = self.env['ai.engine'].get_default_engine()
            return engine.recommend_price(product_data, channel_code, target_margin)
        except Exception:
            # Use formula fallback
            return FormulaPricingMixin.recommend_price(self, product_data, channel_code, target_margin)
