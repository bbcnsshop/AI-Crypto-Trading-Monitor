# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ChannelProduct(models.Model):
    _name = 'channel.product'
    _description = 'Channel Product'
    _order = 'id desc'

    name = fields.Char(string='Display Name', compute='_compute_name', store=True)
    product_id = fields.Many2one('product.product', string='Product', required=True, index=True)
    channel_id = fields.Many2one('channel.config', string='Channel', required=True, index=True)
    product_category = fields.Char(related='product_id.categ_id.name', string='Category', store=True)
    product_cost = fields.Float(related='product_id.standard_price', string='Cost', store=True)
    odoo_qty = fields.Float(related='product_id.qty_available', string='Odoo Stock', store=True)

    channel_product_id = fields.Char(string='Channel Product ID')
    channel_price = fields.Float(string='Channel Price', required=True)
    channel_qty = fields.Integer(string='Channel Stock', default=0)
    channel_url = fields.Char(string='Channel URL')

    # Channel Category (auto-mapped from product.category.mapping)
    channel_category_id = fields.Char(string='Channel Category ID', help='Category ID บน platform')
    channel_category_name = fields.Char(string='Channel Category Name', help='ชื่อ category บน platform')
    channel_category_mapping_id = fields.Many2one('product.category.mapping', string='Category Mapping')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], string='Status', default='draft', index=True)

    sync_status = fields.Selection([
        ('synced', 'Synced'),
        ('pending', 'Pending'),
        ('error', 'Error'),
        ('never', 'Never Synced'),
    ], string='Sync', default='never', index=True)
    sync_message = fields.Text(string='Sync Message')
    last_sync = fields.Datetime(string='Last Sync')

    ai_recommended_price = fields.Float(string='AI Recommended Price')
    ai_confidence = fields.Float(string='AI Confidence')

    # AI Auto-Fill Tracking
    ai_auto_fill_date = fields.Datetime(string='AI Auto-Fill Date')
    ai_auto_fill_status = fields.Selection([
        ('pending', 'Pending'),
        ('filled', 'Filled'),
        ('error', 'Error'),
    ], string='AI Auto-Fill Status', default='pending')
    ai_barcode_suggestion = fields.Char(string='AI Suggested Barcode')
    ai_condition_suggestion = fields.Selection([
        ('new', 'New'),
        ('used', 'Used'),
        ('refurbished', 'Refurbished'),
    ], string='AI Suggested Condition')
    ai_brand_suggestion = fields.Char(string='AI Suggested Brand')
    
    # ============================================================
    # MEDIA: Images & Videos
    # ============================================================
    image_ids = fields.One2many(
        'channel.product.image',
        'channel_product_id',
        string='Images',
    )
    image_count = fields.Integer(
        string='Image Count',
        compute='_compute_image_count',
    )
    
    video_ids = fields.One2many(
        'channel.product.video',
        'channel_product_id',
        string='Videos',
    )
    video_count = fields.Integer(
        string='Video Count',
        compute='_compute_video_count',
    )

    # Per-channel overrides
    channel_weight = fields.Float(string='Weight (kg)', digits=(8, 3), help='Weight override')
    channel_length = fields.Float(string='Length (cm)', digits=(8, 2))
    channel_width = fields.Float(string='Width (cm)', digits=(8, 2))
    channel_height = fields.Float(string='Height (cm)', digits=(8, 2))
    channel_brand = fields.Char(string='Brand', help='Platform-specific brand (Lazada requires this)')
    
    # ============================================================
    # Platform-Specific Fields (Priority 1 - Critical)
    # ============================================================
    barcode = fields.Char(
        string='Barcode',
        help='สำหรับ Lazada (required) - รหัสสินค้า/Barcode ของ Platform'
    )
    condition = fields.Selection([
        ('new', 'New'),
        ('used', 'Used'),
        ('refurbished', 'Refurbished'),
    ], string='Condition', default='new',
        help='สภาพสินค้า - Shopee และ Lazada ต้องการ field นี้'
    )
    channel_description = fields.Text(string='Description', help='Channel-specific description override')
    channel_video_url = fields.Char(string='Video URL', help='Video URL for TikTok or Shopee')
    channel_completeness_ids = fields.One2many(
        'channel.product.completeness', 'channel_product_id', string='Completeness'
    )
    completeness_pct = fields.Float(string='% Complete', digits=(5, 1),
                                    compute='_compute_completeness', store=True)
    has_missing_required = fields.Boolean(string='Missing Required',
                                          compute='_compute_completeness', store=True)

    @api.depends('product_id.name', 'channel_id.name')
    def _compute_name(self):
        for rec in self:
            rec.name = '%s (%s)' % (rec.product_id.name, rec.channel_id.name)

    @api.depends('image_ids')
    def _compute_image_count(self):
        for record in self:
            record.image_count = len(record.image_ids)

    @api.depends('video_ids')
    def _compute_video_count(self):
        for record in self:
            record.video_count = len(record.video_ids)

    # ============================================================
    # ACTIONS: View Media
    # ============================================================
    def action_view_images(self):
        """เปิดหน้า Images ของ channel product นี้"""
        self.ensure_one()
        return {
            'name': 'Images: %s' % self.display_name,
            'type': 'ir.actions.act_window',
            'res_model': 'channel.product.image',
            'view_mode': 'tree,form,kanban',
            'domain': [('channel_product_id', '=', self.id)],
            'context': {
                'default_channel_product_id': self.id,
                'search_default_group_by_type': 1,
            },
        }

    def action_view_videos(self):
        """เปิดหน้า Videos ของ channel product นี้"""
        self.ensure_one()
        return {
            'name': 'Videos: %s' % self.display_name,
            'type': 'ir.actions.act_window',
            'res_model': 'channel.product.video',
            'view_mode': 'tree,form,kanban',
            'domain': [('channel_product_id', '=', self.id)],
            'context': {
                'default_channel_product_id': self.id,
                'search_default_group_by_channel': 1,
            },
        }

    @api.depends('channel_completeness_ids.completeness_pct',
                 'channel_completeness_ids.status',
                 'channel_completeness_ids.channel_id')
    def _compute_completeness(self):
        for rec in self:
            if not rec.channel_id:
                rec.completeness_pct = 100.0
                rec.has_missing_required = False
                continue
            cp = rec.channel_completeness_ids.filtered(lambda c: c.channel_id == rec.channel_id)
            if cp:
                rec.completeness_pct = cp[0].completeness_pct
                rec.has_missing_required = (cp[0].status == 'incomplete')
            else:
                rec.completeness_pct = 100.0
                rec.has_missing_required = False

    @api.onchange('product_id')
    def _onchange_product(self):
        if self.product_id:
            self.channel_price = self.product_id.list_price or 0
            self.channel_qty = int(self.product_id.qty_available or 0)
            # Auto-map channel category from Odoo category
            self._auto_map_category()

    def _auto_map_category(self):
        """Auto-find channel category from product.category.mapping.

        ถ้ามี mapping ใน product.category.mapping สำหรับ Odoo category นี้
        จะ set channel_category_id และ channel_category_name ให้อัตโนมัติ
        """
        self.ensure_one()
        if not (self.product_id and self.product_id.categ_id and self.channel_id):
            return
        mapping = self.env['product.category.mapping'].search([
            ('channel_id', '=', self.channel_id.id),
            ('odoo_category_id', '=', self.product_id.categ_id.id),
            ('auto_map', '=', True),
            ('active', '=', True),
        ], limit=1)
        if mapping:
            self.channel_category_id = mapping.channel_category_id
            self.channel_category_name = mapping.channel_category_name
            self.channel_category_mapping_id = mapping.id

    @api.onchange('channel_id')
    def _onchange_channel(self):
        if self.channel_id and self.product_id:
            self._call_ai_recommend_price()

    def _call_ai_recommend_price(self):
        """Call AI engine to get price recommendation and create price.recommendation record.

        Returns:
            dict: AI result with selling_price, confidence, reasoning
        """
        self.ensure_one()
        if not (self.channel_id and self.product_id):
            return {}
        try:
            ai = self.env['multichannel.ai.engine'].get_default_engine()
            result = ai.recommend_price(
                {'name': self.product_id.name, 'cost': self.product_id.standard_price or 0},
                self.channel_id.code
            )
            self.ai_recommended_price = result.get('selling_price', 0)
            self.ai_confidence = result.get('confidence', 0)

            # Create price.recommendation record for tracking
            self.env['price.recommendation'].create({
                'product_id': self.product_id.id,
                'channel_id': self.channel_id.id,
                'ai_recommended_price': result.get('selling_price', 0),
                'recommended_reasoning': result.get('reasoning', ''),
                'cost_price': self.product_id.standard_price or 0,
                'platform_fee': result.get('platform_fee', 0),
                'payment_fee': result.get('payment_fee', 0),
                'shipping_fee': result.get('shipping_fee', 0),
                'status': 'pending',
            })
            return result
        except Exception as e:
            _logger.warning('AI price recommend error for %s: %s' % (self.name, str(e)))
            return {}

    def action_check_completeness(self):
        for rec in self:
            if rec.channel_id:
                self.env['channel.product.completeness'].upsert(rec.id, rec.channel_id.id)
            # Auto-create variant records if this is a variant product
            product = rec.product_id
            if product and product.product_template_attribute_value_ids:
                for variant in product.product_tmpl_id.product_variant_ids:
                    existing = self.env['channel.product.variant'].search([
                        ('channel_product_id', '=', rec.id),
                        ('product_variant_id', '=', variant.id)
                    ], limit=1)
                    if not existing:
                        self.env['channel.product.variant'].create({
                            'channel_product_id': rec.id,
                            'product_variant_id': variant.id,
                            'channel_price': rec.channel_price,
                            'channel_qty': int(variant.qty_available or 0),
                            'channel_weight': rec.channel_weight,
                        })
        return True

    def toggle_active(self):
        for rec in self:
            rec.state = 'active' if rec.state == 'draft' else 'draft'

    def _validate_for_sync(self):
        self.ensure_one()
        if not self.channel_id:
            raise ValidationError(_('No channel selected.'))
        missing = []
        for mapping in self.env['channel.product.field.mapping'].search([
            ('channel_id', '=', self.channel_id.id),
            ('active', '=', True),
            ('is_required', '=', True),
        ]):
            val = mapping.get_platform_value(self)
            if val is False or val == '' or val is None:
                missing.append(mapping.description or mapping.platform_field)
        if missing:
            lines = '\n'.join('- %s' % m for m in missing)
            raise ValidationError(
                _('Cannot sync to %s. Missing required fields:\n%s') %
                (self.channel_id.name, lines)
            )
        return True

    def sync_to_channel(self):
        for rec in self:
            try:
                rec.action_check_completeness()
                rec._validate_for_sync()
                if rec.channel_id.code == 'shopee':
                    rec._sync_shopee()
                elif rec.channel_id.code == 'lazada':
                    rec._sync_lazada()
                elif rec.channel_id.code == 'tiktok':
                    rec._sync_tiktok()
                rec.write({
                    'sync_status': 'synced',
                    'last_sync': fields.Datetime.now(),
                    'state': 'active',
                })
            except ValidationError:
                rec.write({
                    'sync_status': 'error',
                    'sync_message': 'Missing required fields',
                })
                raise
            except Exception as e:
                rec.write({
                    'sync_status': 'error',
                    'sync_message': str(e),
                })
                raise ValidationError(_('Sync failed: %s') % str(e))

    def _sync_shopee(self):
        _logger.info('Syncing %s to Shopee' % self.name)
        # Upload images first
        for img in self.image_ids.filtered(lambda i: i.upload_status != 'uploaded'):
            img.action_upload()

    def _sync_lazada(self):
        _logger.info('Syncing %s to Lazada' % self.name)
        for img in self.image_ids.filtered(lambda i: i.upload_status != 'uploaded'):
            img.action_upload()

    def _sync_tiktok(self):
        _logger.info('Syncing %s to TikTok' % self.name)
        for img in self.image_ids.filtered(lambda i: i.upload_status != 'uploaded'):
            img.action_upload()

    def unlink(self):
        for rec in self:
            if rec.sync_status == 'synced':
                _logger.warning('Deleting synced product %s from %s' % (rec.name, rec.channel_id.name))
        return super().unlink()

    # ============================================================
    # Cron Job Methods
    # ============================================================
    @api.model
    def cron_sync_pending_products(self):
        """Auto sync all products in pending state."""
        pending = self.search([
            ('sync_status', '=', 'pending'),
            ('state', 'in', ('active', 'draft')),
        ], limit=100)
        synced = 0
        errors = 0
        for cp in pending:
            try:
                cp.sync_to_channel()
                synced += 1
            except Exception as e:
                errors += 1
                _logger.error('Cron sync error for %s: %s' % (cp.name, str(e)))
        _logger.info('Auto sync: %d synced, %d errors' % (synced, errors))
        return True

    @api.model
    def cron_sync_channel_stock(self):
        """Sync stock from Odoo to channels for all active products."""
        active_cps = self.search([
            ('state', '=', 'active'),
        ])
        updated = 0
        for cp in active_cps:
            new_qty = int(cp.product_id.qty_available or 0)
            if new_qty != cp.channel_qty:
                cp.write({'channel_qty': new_qty})
                updated += 1
        _logger.info('Stock sync: %d products updated' % updated)
        return True

    @api.model
    def cron_refresh_ai_prices(self):
        """Refresh AI-recommended prices for all channel products.
        
        Uses ai_engine if available, falls back to formula-based pricing.
        """
        cps = self.search([('state', 'in', ('active', 'draft'))], limit=200)
        refreshed = 0
        errors = 0
        
        # Check AI availability once
        try:
            ai_engine = self.env['multichannel.ai.engine'].get_default_engine()
            ai_available = True
        except Exception:
            ai_engine = None
            ai_available = False
            _logger.info('AI engine not available, using formula-based pricing')
        
        for cp in cps:
            try:
                product_data = {
                    'name': cp.product_id.name,
                    'cost': cp.product_id.standard_price or 0,
                }
                
                if ai_available:
                    result = ai_engine.recommend_price(product_data, cp.channel_id.code)
                else:
                    # Use formula fallback
                    result = self.env['multichannel.ai.engine'].recommend_price(
                        product_data,
                        cp.channel_id.code
                    ) if hasattr(self.env['multichannel.ai.engine'], 'recommend_price') else {
                        'selling_price': cp.product_id.list_price or 0,
                        '_source': 'default',
                    }
                
                if result.get('selling_price'):
                    cp.write({
                        'ai_recommended_price': result.get('selling_price', 0),
                    })
                    refreshed += 1
            except Exception as e:
                errors += 1
                _logger.error('AI price refresh error for %s: %s' % (cp.name, str(e)))
        
        _logger.info('AI price refresh: %d updated, %d errors' % (refreshed, errors))
        return True

    @api.model
    def cron_check_completeness(self):
        """Run completeness check on all channel products."""
        cps = self.search([])
        for cp in cps:
            try:
                cp._compute_completeness()
            except Exception as e:
                _logger.error('Completeness check error for %s: %s' % (cp.name, str(e)))
        return True

    @api.model
    def cron_sync_error_alert(self):
        """Log alerts for products with sync errors."""
        errored = self.search([('sync_status', '=', 'error')])
        if errored:
            _logger.warning(
                'Channel Products with sync errors (%d): %s' % (
                    len(errored),
                    ', '.join(errored.mapped('name')[:10]),
                )
            )
        return True

    # ============================================================
    # AI Auto-Fill Functions
    # ============================================================

    def ai_suggest_barcode(self):
        """Suggest barcode for channel product.

        Logic: product.barcode -> product.default_code -> Generate 'CH{channel}{id}'
        """
        self.ensure_one()
        product = self.product_id

        # Priority 1: Use product.barcode if available
        if product.barcode:
            return product.barcode

        # Priority 2: Use product.default_code (internal reference)
        if product.default_code:
            return product.default_code

        # Priority 3: Generate unique barcode
        channel_code = self.channel_id.code[:3].upper() if self.channel_id else 'CHN'
        return 'CH{}{:06d}'.format(channel_code, self.id)

    def ai_suggest_condition(self):
        """Suggest condition (new/used/refurbished) based on product description.

        Logic: Check product description for keywords like 'มือสอง', 'used', 'refurbished'
        """
        self.ensure_one()
        product = self.product_id

        if not product or not product.description:
            return 'new'

        desc = product.description.lower()

        # Check for used/refurbished keywords
        used_keywords = ['มือสอง', 'second hand', 'used', 'second-hand', 'pre-owned', 'preowned']
        refurbished_keywords = ['refurbished', 'reconditioned', 'remanufactured', 'รีเฟอร์', 'รีเฟอร์บิช']

        for kw in refurbished_keywords:
            if kw in desc:
                return 'refurbished'

        for kw in used_keywords:
            if kw in desc:
                return 'used'

        return 'new'

    def ai_suggest_brand(self):
        """Suggest brand from product name using keyword matching.

        Logic: Match known brand keywords from product name
        """
        self.ensure_one()
        product = self.product_id

        if not product or not product.name:
            return False

        name = product.name.lower()

        # Known brands for IT/Electronics (Thailand market)
        brand_keywords = {
            'apple': 'Apple',
            'samsung': 'Samsung',
            'sony': 'Sony',
            'xiaomi': 'Xiaomi',
            'huawei': 'Huawei',
            'oppo': 'OPPO',
            'vivo': 'Vivo',
            'realme': 'Realme',
            'oneplus': 'OnePlus',
            'nothing': 'Nothing',
            'google': 'Google',
            'microsoft': 'Microsoft',
            'asus': 'ASUS',
            'acer': 'ACER',
            'lenovo': 'Lenovo',
            'hp': 'HP',
            'dell': 'Dell',
            'msi': 'MSI',
            'lg': 'LG',
            'panasonic': 'Panasonic',
            'canon': 'Canon',
            'nikon': 'Nikon',
            'fujifilm': 'Fujifilm',
            'dyson': 'Dyson',
            'jbl': 'JBL',
            'bose': 'Bose',
            'sennheiser': 'Sennheiser',
            'audio-technica': 'Audio-Technica',
            'logitech': 'Logitech',
            'razer': 'Razer',
            'corsair': 'Corsair',
            'steelseries': 'SteelSeries',
            'hyperx': 'HyperX',
            'cooler master': 'Cooler Master',
            'nzxt': 'NZXT',
            'fractal design': 'Fractal Design',
            'be quiet': 'Be Quiet!',
            'seasonic': 'Seasonic',
            'evga': 'EVGA',
            'gigabyte': 'Gigabyte',
            'asus rog': 'ASUS ROG',
            'rog': 'ASUS ROG',
        }

        for keyword, brand in brand_keywords.items():
            if keyword in name:
                return brand

        return False

    def ai_auto_fill_fields(self):
        """Auto-fill all AI-suggested fields for this channel product.
        
        Fills: barcode, condition, brand
        Returns dict with filled fields and suggestions
        """
        self.ensure_one()
        
        results = {
            'barcode': False,
            'condition': False,
            'brand': False,
            'updated': False,
        }
        
        try:
            # Suggest barcode if missing
            if not self.barcode:
                barcode = self.ai_suggest_barcode()
                self.barcode = barcode
                results['barcode'] = barcode
            
            # Suggest condition if not set (still default 'new')
            if not self.condition or self.condition == 'new':
                condition = self.ai_suggest_condition()
                if condition and condition != self.condition:
                    self.condition = condition
                    results['condition'] = condition
            
            # Suggest brand if missing
            if not self.channel_brand:
                brand = self.ai_suggest_brand()
                if brand:
                    self.channel_brand = brand
                    results['brand'] = brand
            
            # Update AI tracking fields
            results['updated'] = True
            self.write({
                'ai_auto_fill_date': fields.Datetime.now(),
                'ai_auto_fill_status': 'filled',
                'ai_barcode_suggestion': results['barcode'] or False,
                'ai_condition_suggestion': results['condition'] or False,
                'ai_brand_suggestion': results['brand'] or False,
            })
            
            _logger.info('AI Auto-fill completed for %s: %s' % (self.name, results))
            
        except Exception as e:
            _logger.error('AI Auto-fill error for %s: %s' % (self.name, str(e)))
            self.write({
                'ai_auto_fill_date': fields.Datetime.now(),
                'ai_auto_fill_status': 'error',
            })
            results['error'] = str(e)
        
        return results

    @api.model
    def cron_ai_auto_fill_missing(self):
        """Daily cron job to auto-fill missing fields for channel products.
        
        Targets: Products with missing barcode, condition, or brand
        Limit: 200 records per run
        """
        # Search for products that need AI fill
        domain = [
            ('state', 'in', ('draft', 'active')),
            '|', '|', '|',
                ('barcode', '=', False),
                ('channel_brand', '=', False),
                ('condition', '=', 'new'),
        ]
        
        cps = self.search(domain, limit=200)
        filled_count = 0
        error_count = 0
        
        for cp in cps:
            try:
                result = cp.ai_auto_fill_fields()
                if result.get('updated'):
                    filled_count += 1
            except Exception as e:
                error_count += 1
                _logger.error('Cron AI auto-fill error for %s: %s' % (cp.name, str(e)))
        
        _logger.info('Cron AI auto-fill: %d filled, %d errors' % (filled_count, error_count))
        return True
# ProductCategoryMapping and PriceRecommendation moved to:
# - models/category_mapping.py
# - models/price_recommendation.py