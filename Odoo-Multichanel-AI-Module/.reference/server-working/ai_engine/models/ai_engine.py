# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class AIEngine(models.Model):
    """AI Engine for Product Classification and Pricing using OpenRouter"""
    _name = 'ai.engine'
    _description = 'AI Engine for Product Classification and Pricing'
    
    @api.model
    def get_default_engine(self):
        engine = self.search([], limit=1)
        if not engine:
            engine = self.create({'name': 'Default AI Engine'})
        return engine
    
    name = fields.Char(string='Engine Name', default='AI Engine')
    provider = fields.Selection([
        ('openrouter', 'OpenRouter (Multiple Models)'),
        ('local', 'Local LLM (Ollama)'),
    ], string='AI Provider', default='openrouter')
    
    # OpenRouter Settings
    openrouter_api_key = fields.Char(
        string='OpenRouter API Key', 
        groups='base.group_system',
        help='sk-or-v1-... from openrouter.ai/keys'
    )
    openrouter_base_url = fields.Char(
        string='Base URL',
        default='https://openrouter.ai/api/v1',
        help='OpenRouter API base URL'
    )
    openrouter_model = fields.Char(
        string='Model',
        default='google/gemini-2.0-flash-exp:free',
        help='OpenRouter model name. Free models use ":free" suffix (e.g. "openrouter/free", "google/gemini-2.0-flash-exp:free"). Premium models: "openai/gpt-4o", "anthropic/claude-3.5-sonnet", "deepseek/deepseek-chat" etc.'
    )
    
    # Local LLM Settings
    local_endpoint = fields.Char(string='Local Endpoint', default='http://localhost:11434/api/generate')
    local_model = fields.Char(string='Local Model', default='llama3')
    
    # Default Fee Rates
    default_platform_fee = fields.Float(string='Platform Fee (%)', default=5.0)
    default_payment_fee = fields.Float(string='Payment Fee (%)', default=2.0)
    default_shipping_fee = fields.Float(string='Shipping Subsidy (%)', default=2.5)
    
    # Thai VAT
    vat_rate = fields.Float(string='VAT Rate (%)', default=7.0)
    
    # Relation fields
    category_mapping_ids = fields.One2many('ai.category.mapping', 'engine_id', string='Category Mappings')
    
    def classify_product(self, product_data):
        self.ensure_one()
        categories = self.env['product.category'].search_read([], ['id', 'name', 'complete_name', 'parent_path'])
        category_list = chr(10).join([f'- {c["id"]}: {c["complete_name"]}' for c in categories])
        prompt = f'You are an expert product classifier for IT equipment in Thailand. Categories: {category_list} Product: {product_data.get("name", "")} Description: {product_data.get("description", "N/A")} Attributes: {product_data.get("attributes", "N/A")} Return JSON: {{"category_id": ID, "confidence": 0.0-1.0, "reasoning": "...", "suggested_tags": []}}'
        try:
            import json
            response = self._call_ai(prompt)
            result = json.loads(response)
            if result.get('category_id'):
                self._create_category_mapping(product_data.get('name', ''), result['category_id'], result.get('confidence', 0))
                category = self.env['product.category'].browse(result['category_id'])
                result['category_name'] = category.complete_name
            return result
        except Exception as e:
            _logger.error(f'AI classification failed: {str(e)}')
            return {'category_id': False, 'category_name': 'Error', 'confidence': 0, 'reasoning': str(e), 'suggested_tags': []}
    
    def recommend_price(self, product_data, channel_code='shopee', target_margin=30.0):
        """Recommend selling price for a product on a specific channel.

        Smart routing:
        - ถ้ามี OpenRouter API key → ใช้ AI แนะนำราคา
        - ถ้าไม่มี → ใช้ formula calculation fallback
        """
        self.ensure_one()
        # Try AI-based recommendation if API key is configured
        if self.provider == 'openrouter' and self.openrouter_api_key:
            try:
                prompt = (
                    f'You are a pricing expert for IT equipment in Thailand. '
                    f'Product: {product_data.get("name", "")}, '
                    f'Cost: {product_data.get("cost", 0):,.0f} THB, '
                    f'Target Margin: {target_margin}%. '
                    f'Platform Fees: Shopee 5/2/2.5%, Lazada 5/2/3%, TikTok 3.5/1.5/2%. VAT 7%. '
                    f'Return JSON: selling_price, gross_profit, net_profit, net_margin, recommendation.'
                )
                import json
                response = self._call_ai(prompt)
                result = json.loads(response)
                result.setdefault('channel', channel_code)
                result['_source'] = 'ai'
                return result
            except Exception as e:
                _logger.warning('AI pricing failed, fallback to formula: %s', str(e))

        # Fallback: formula-based calculation
        return self._calculate_formula_price(product_data, channel_code, target_margin)

    def _calculate_formula_price(self, product_data, channel_code='shopee', margin_target=30.0):
        """Formula-based price recommendation (no AI required)."""
        cost = product_data.get('cost', 0) or 0
        margin_target = product_data.get('margin', margin_target) or margin_target
        fee_config = self._get_fee_config(channel_code)
        commission = fee_config['commission']
        payment_fee = fee_config['payment_fee']
        shipping_subsidy = fee_config['shipping_subsidy']
        vat = self.vat_rate or 7.0
        total_fee_pct = (commission + payment_fee + shipping_subsidy) / 100.0
        vat_factor = 1 + vat / 100.0
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

    def calculate_profit(self, selling_price, cost, channel_code):
        self.ensure_one()
        fee_config = self._get_fee_config(channel_code)
        price_excl_vat = selling_price / (1 + self.vat_rate / 100)
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
            'selling_price': selling_price, 'price_excl_vat': round(price_excl_vat, 2), 'vat_collected': round(vat_collected, 2),
            'cost': cost, 'gross_profit': round(gross_profit, 2), 'gross_margin': round(gross_margin, 1),
            'platform_fee': round(platform_fee, 2), 'payment_fee': round(payment_fee, 2), 'shipping_subsidy': round(shipping_subsidy, 2),
            'total_fees': round(total_fees, 2), 'net_profit': round(net_profit, 2), 'net_margin': round(net_margin, 1),
            'break_even_price': round(cost + total_fees, 2),
        }

    def _get_fee_config(self, channel_code):
        fee_configs = {
            'shopee': {'commission': 5.0, 'payment_fee': 2.0, 'shipping_subsidy': 2.5, 'name': 'Shopee'},
            'lazada': {'commission': 5.0, 'payment_fee': 2.0, 'shipping_subsidy': 3.0, 'name': 'Lazada'},
            'tiktok': {'commission': 3.5, 'payment_fee': 1.5, 'shipping_subsidy': 2.0, 'name': 'TikTok Shop'},
        }
        return fee_configs.get(channel_code, {'commission': self.default_platform_fee, 'payment_fee': self.default_payment_fee, 'shipping_subsidy': self.default_shipping_fee, 'name': channel_code})

    def _call_ai(self, prompt):
        if self.provider == 'openrouter': return self._call_openrouter(prompt)
        elif self.provider == 'local': return self._call_local(prompt)
        else: raise ValidationError(_('AI provider not configured'))

    def _call_openrouter(self, prompt):
        if not self.openrouter_api_key: raise ValidationError(_('OpenRouter API Key not configured. Get from https://openrouter.ai/keys'))
        try:
            import requests
            headers = {
                'Authorization': f'Bearer {self.openrouter_api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://odoo-multichannel.local',
                'X-Title': 'Odoo Multi-Channel AI'
            }
            data = {
                'model': self.openrouter_model,
                'messages': [
                    {'role': 'system', 'content': 'You are a helpful AI assistant.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 2000
            }
            response = requests.post(f'{self.openrouter_base_url}/chat/completions', json=data, headers=headers, timeout=120)
            if response.status_code != 200:
                raise ValidationError(_(f'OpenRouter API Error: {response.status_code} - {response.text}'))
            result = response.json()
            return result['choices'][0]['message']['content']
        except ImportError: raise ValidationError(_('requests library not available'))
        except Exception as e: raise ValidationError(_(f'OpenRouter Error: {str(e)}'))

    def _call_local(self, prompt):
        try:
            import requests
            response = requests.post(self.local_endpoint, json={'model': self.local_model, 'prompt': prompt, 'stream': False}, timeout=120)
            return response.json().get('response', '')
        except ImportError: raise ValidationError(_('requests library not available'))


    def _create_category_mapping(self, product_name, category_id, confidence):
        if confidence < 0.5: return
        existing = self.env['ai.category.mapping'].search([('product_name', '=', product_name), ('category_id', '=', category_id)], limit=1)
        if not existing:
            self.env['ai.category.mapping'].create({'engine_id': self.id, 'product_name': product_name, 'category_id': category_id, 'confidence': confidence, 'mapping_count': 1})
        else:
            existing.write({'confidence': (existing.confidence + confidence) / 2, 'mapping_count': existing.mapping_count + 1})


class AICategoryMapping(models.Model):
    _name = 'ai.category.mapping'
    _description = 'AI Category Mapping'
    engine_id = fields.Many2one('ai.engine', string='AI Engine')
    product_name = fields.Char(string='Product Name', index=True)
    category_id = fields.Many2one('product.category', string='Odoo Category', required=True)
    confidence = fields.Float(string='Confidence', digits=(3, 2))
    mapping_count = fields.Integer(string='Mapping Count', default=1)
    last_used = fields.Datetime(string='Last Used', default=fields.Datetime.now)
    _sql_constraints = [('product_category_unique', 'unique(product_name, category_id)', 'This mapping already exists!')]