{
    'name': 'AI Engine - OpenRouter Integration',
    'version': '16.0.1.0',
    'category': 'Artificial Intelligence',
    'summary': 'AI Engine with OpenRouter, OpenAI, Claude support for product classification and pricing',
    'description': """AI Engine - OpenRouter Integration for Odoo 16. AI-powered product classification and pricing recommendations.""",
    'author': 'BBCNS Shop',
    'website': 'https://github.com/bbcnsshop/Odoo-Multichanel-AI-Module',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'product',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/ai_engine_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
 