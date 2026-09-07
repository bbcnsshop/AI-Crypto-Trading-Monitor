# -*- coding: utf-8 -*-
"""
Price Recommendation Model
บันทึกคำแนะนำราคาจาก AI พร้อมคำนวณกำไร
"""

from odoo import models, fields, api


class PriceRecommendation(models.Model):
    """AI-recommended pricing with profit calculations.
    
    ใช้สำหรับ:
    - บันทึกคำแนะนำราคาจาก AI
    - คำนวณ gross profit, margin, net profit
    - Track status: pending/accepted/rejected/applied
    """
    _name = 'price.recommendation'
    _description = 'Price Recommendation'
    _order = 'create_date desc'

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        ondelete='cascade',
    )
    channel_id = fields.Many2one(
        'channel.config',
        string='Channel',
        required=True,
        ondelete='cascade',
    )
    ai_recommended_price = fields.Float(
        string='AI Recommended Price',
        digits='Product Price',
    )
    recommended_reasoning = fields.Text(
        string='Recommendation Reasoning',
        help='เหตุผลที่ AI แนะนำราคานี้',
    )
    cost_price = fields.Float(
        string='Cost Price',
        digits='Product Price',
    )

    # Profit fields
    gross_profit = fields.Float(
        string='Gross Profit',
        compute='_compute_profit',
        store=True,
        digits='Product Price',
    )
    gross_margin = fields.Float(
        string='Gross Margin %',
        compute='_compute_margin',
        store=True,
        digits=(5, 2),
    )
    platform_fee = fields.Float(
        string='Platform Fee',
        digits='Product Price',
    )
    payment_fee = fields.Float(
        string='Payment Fee',
        digits='Product Price',
    )
    shipping_fee = fields.Float(
        string='Shipping Fee',
        digits='Product Price',
    )
    vat_amount = fields.Float(
        string='VAT Amount',
        digits='Product Price',
    )
    net_profit = fields.Float(
        string='Net Profit',
        compute='_compute_net_profit',
        store=True,
        digits='Product Price',
    )

    # Status
    status = fields.Selection([
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('applied', 'Applied'),
    ], string='Status', default='pending')

    create_date = fields.Datetime(
        string='Created',
        default=fields.Datetime.now,
        readonly=True,
    )

    @api.depends('ai_recommended_price', 'cost_price')
    def _compute_profit(self):
        for rec in self:
            rec.gross_profit = rec.ai_recommended_price - rec.cost_price

    @api.depends('gross_profit', 'ai_recommended_price')
    def _compute_margin(self):
        for rec in self:
            if rec.ai_recommended_price:
                rec.gross_margin = (rec.gross_profit / rec.ai_recommended_price) * 100
            else:
                rec.gross_margin = 0.0

    @api.depends('platform_fee', 'payment_fee', 'shipping_fee', 'vat_amount', 'gross_profit')
    def _compute_net_profit(self):
        for rec in self:
            rec.net_profit = (
                rec.gross_profit
                - rec.platform_fee
                - rec.payment_fee
                - rec.shipping_fee
                - rec.vat_amount
            )

    def action_accept(self):
        """ยอมรับคำแนะนำ"""
        self.write({'status': 'accepted'})

    def action_reject(self):
        """ปฏิเสธคำแนะนำ"""
        self.write({'status': 'rejected'})

    def action_apply(self):
        """นำราคาที่แนะนำไปใช้กับ product"""
        self.ensure_one()
        if self.product_id and self.ai_recommended_price:
            # อัปเดต list_price ของ product
            self.product_id.write({
                'list_price': self.ai_recommended_price,
            })
            self.write({'status': 'applied'})
            return True
        return False
