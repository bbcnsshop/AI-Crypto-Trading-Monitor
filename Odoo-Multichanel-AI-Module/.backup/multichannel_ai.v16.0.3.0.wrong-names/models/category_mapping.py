# -*- coding: utf-8 -*-
"""
Product Category Mapping Model
แมป Category ระหว่าง Odoo กับ Channel (Shopee, Lazada, TikTok)
"""

from odoo import models, fields, api


class ProductCategoryMapping(models.Model):
    """Map Odoo product categories to channel-specific category IDs.
    
    ใช้สำหรับ:
    - แมป Odoo product.category ไปยัง category ของ platform
    - Auto-map ตาม code matching
    """
    _name = 'product.category.mapping'
    _description = 'Product Category Mapping'
    _rec_name = 'channel_category_name'

    channel_id = fields.Many2one(
        'channel.config',
        string='Channel',
        required=True,
        ondelete='cascade',
    )
    channel_category_id = fields.Char(
        string='Channel Category ID',
        required=True,
        help='Category ID จาก platform เช่น Shopee category ID',
    )
    channel_category_name = fields.Char(
        string='Channel Category Name',
        help='ชื่อ category บน platform เพื่อแสดงใน UI',
    )
    odoo_category_id = fields.Many2one(
        'product.category',
        string='Odoo Category',
        required=True,
    )
    auto_map = fields.Boolean(
        string='Auto Map',
        default=True,
        help='ถ้าเปิด ระบบจะ map product เข้า category นี้อัตโนมัติ',
    )
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('unique_channel_category',
         'UNIQUE(channel_id, channel_category_id)',
         'Category ID นี้มีอยู่แล้วใน Channel นี้!'),
    ]
