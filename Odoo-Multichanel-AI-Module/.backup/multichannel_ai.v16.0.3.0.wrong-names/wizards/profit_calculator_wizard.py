# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ProfitCalculatorWizard(models.TransientModel):
    """Profit Calculator Wizard"""
    _name = 'profit.calculator.wizard'
    _description = 'Profit Calculator Wizard'
    
    product_id = fields.Many2one('product.product', string='Product')
    channel_id = fields.Many2one('channel.config', string='Channel')
    selling_price = fields.Float(string='Selling Price (incl. VAT)', required=True)
    cost = fields.Float(string='Cost', required=True)
    
    # Computed results
    price_excl_vat = fields.Float(string='Price (excl. VAT)', compute='_compute_results', readonly=True)
    vat_collected = fields.Float(string='VAT Collected', compute='_compute_results', readonly=True)
    platform_fee = fields.Float(string='Platform Fee', compute='_compute_results', readonly=True)
    payment_fee = fields.Float(string='Payment Fee', compute='_compute_results', readonly=True)
    shipping_subsidy = fields.Float(string='Shipping Subsidy', compute='_compute_results', readonly=True)
    total_fees = fields.Float(string='Total Fees', compute='_compute_results', readonly=True)
    gross_profit = fields.Float(string='Gross Profit', compute='_compute_results', readonly=True)
    net_profit = fields.Float(string='Net Profit', compute='_compute_results', readonly=True)
    gross_margin = fields.Float(string='Gross Margin %', compute='_compute_results', readonly=True)
    net_margin = fields.Float(string='Net Margin %', compute='_compute_results', readonly=True)
    break_even_price = fields.Float(string='Break-even Price', compute='_compute_results', readonly=True)
    
    target_margin = fields.Float(string='Target Margin %', default=30.0)
    recommended_price = fields.Float(string='AI Recommended Price', compute='_compute_results', readonly=True)
    ai_available = fields.Boolean(string='AI Available', compute='_compute_ai_available', store=False)
    
    @api.depends()
    def _compute_ai_available(self):
        """Check if AI engine is available."""
        for rec in self:
            try:
                rec.env['multichannel.ai.engine'].search([], limit=1)
                rec.ai_available = True
            except Exception:
                rec.ai_available = False
    
    @api.depends('selling_price', 'cost', 'channel_id.code', 'target_margin')
    def _compute_results(self):
        for rec in self:
            if not rec.channel_id:
                continue
            
            # Check AI availability with fallback
            try:
                ai_engine = rec.env['multichannel.ai.engine'].get_default_engine()
                ai_available = True
            except Exception:
                ai_engine = None
                ai_available = False
            
            if ai_available:
                # Use AI engine
                profit = ai_engine.calculate_profit(
                    rec.selling_price,
                    rec.cost,
                    rec.channel_id.code
                )
                product_data = {
                    'name': rec.product_id.name if rec.product_id else 'Product',
                    'cost': rec.cost,
                    'category': 'IT Equipment'
                }
                ai_rec = ai_engine.recommend_price(
                    product_data,
                    rec.channel_id.code,
                    rec.target_margin
                )
            else:
                # Use formula fallback (same logic as ai_engine)
                profit = self._calculate_profit_formula(
                    rec.selling_price,
                    rec.cost,
                    rec.channel_id.code
                )
                ai_rec = self._recommend_price_formula(
                    rec.cost,
                    rec.channel_id.code,
                    rec.target_margin
                )
            
            # Assign values
            rec.price_excl_vat = profit['price_excl_vat']
            rec.vat_collected = profit['vat_collected']
            rec.platform_fee = profit['platform_fee']
            rec.payment_fee = profit['payment_fee']
            rec.shipping_subsidy = profit['shipping_subsidy']
            rec.total_fees = profit['total_fees']
            rec.gross_profit = profit['gross_profit']
            rec.net_profit = profit['net_profit']
            rec.gross_margin = profit['gross_margin']
            rec.net_margin = profit['net_margin']
            rec.break_even_price = profit['break_even_price']
            rec.recommended_price = ai_rec.get('selling_price', 0)
    
    def _calculate_profit_formula(self, selling_price, cost, channel_code):
        """Formula-based profit calculation (fallback when AI not available)."""
        fee_config = self._get_fee_config(channel_code)
        vat_rate = 7.0
        
        price_excl_vat = selling_price / (1 + vat_rate / 100)
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
    
    def _recommend_price_formula(self, cost, channel_code, target_margin):
        """Formula-based price recommendation (fallback when AI not available)."""
        fee_config = self._get_fee_config(channel_code)
        
        commission = fee_config['commission']
        payment_fee = fee_config['payment_fee']
        shipping_subsidy = fee_config['shipping_subsidy']
        vat = 7.0
        
        total_fee_pct = (commission + payment_fee + shipping_subsidy) / 100.0
        vat_factor = 1 + vat / 100.0
        divisor = (1 - total_fee_pct) * vat_factor
        
        if divisor <= 0:
            divisor = 0.7
        
        selling_price = max(cost, cost * (1 + target_margin / 100.0) / divisor)
        
        return {
            'selling_price': round(selling_price, 2),
            'cost': cost,
            'target_margin': target_margin,
            'channel': channel_code,
            '_source': 'formula',
        }
    
    def _get_fee_config(self, channel_code):
        """Get fee configuration for channel."""
        fee_configs = {
            'shopee': {'commission': 5.0, 'payment_fee': 2.0, 'shipping_subsidy': 2.5, 'name': 'Shopee'},
            'lazada': {'commission': 5.0, 'payment_fee': 2.0, 'shipping_subsidy': 3.0, 'name': 'Lazada'},
            'tiktok': {'commission': 3.5, 'payment_fee': 1.5, 'shipping_subsidy': 2.0, 'name': 'TikTok Shop'},
        }
        return fee_configs.get(channel_code, fee_configs['shopee'])