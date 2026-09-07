{
    "name": "Multi-Channel E-Commerce Integration",
    "version": "16.0.3.0",
    "category": "Sales",
    "summary": "Multi-channel e-commerce integration (Shopee, Lazada, TikTok Shop) with integrated AI",
    "description": """Multi-Channel E-Commerce Integration for Odoo 16.

Features:
- Channel product management with integrated AI pricing
- Bulk add/remove products to channels
- Bidirectional sync with Shopee, Lazada, TikTok Shop
- Channel order webhook ingestion
- Profit margin calculator (AI or formula-based)
- Sale order channel tracking
- Data completeness validation

AI Features (Integrated):
- AI-powered pricing recommendations
- AI category classification
- OpenRouter integration (supports free & paid models)
- Formula-based fallback when AI unavailable
""",
    "author": "BBCNS Shop",
    "website": "https://github.com/bbcnsshop/Odoo-Multichanel-AI-Module",
    "license": "LGPL-3",
    "depends": [
        "base",
        "sale",
        "sale_management",
        "stock",
        "account",
        "product",
        "uom",
        "web",
        # REMOVED: ai_engine is now optional - use ai_bridge.AIAvailability instead
    ],
    "external_dependencies": {
        "python": ["requests"],
    },
    "data": [
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "data/channel_data.xml",
        "data/default_field_mappings.xml",
        "data/category_mapping.xml",
        "data/cron.xml",
        "views/channel_list_module_views.xml",
        "views/channel_config_views.xml",
        "views/channel_product_views.xml",
        "views/channel_field_mapping_views.xml",
        "views/product_channel_views.xml",
        "views/add_to_channel_wizard_views.xml",
        "views/channel_order_views.xml",
        "views/sale_order_channel_views.xml",
        "views/product_channel_search_views.xml",
        "views/profit_calculator_views.xml",
        "views/channel_product_image_views.xml",
        "views/channel_product_video_views.xml",
        "views/channel_product_attribute_views.xml",
        "views/category_mapping_views.xml",
        "views/price_recommendation_views.xml",
        "views/product_template_views.xml",
        "views/channel_product_ai_fill_views.xml",
        "views/channel_menus.xml",
        "views/templates/layout.xml",
        "views/templates/dashboard.xml",
        "views/templates/channel_products.xml",
        "views/templates/sync.xml",
        "views/templates/channels.xml",
        "views/templates/field_mappings.xml"
    ],
    "demo": [
        "demo/demo.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "multichannel_ai/static/src/js/multichannel_widget.js",
            "multichannel_ai/static/src/css/multichannel.css"
        ]
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
