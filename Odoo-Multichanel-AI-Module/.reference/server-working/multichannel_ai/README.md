# Multi-Channel AI E-Commerce Integration for Odoo 16

## Overview

This module integrates Odoo 16 with major e-commerce platforms (Shopee, Lazada, TikTok Shop) with AI-powered features for product classification and pricing recommendations, using **OpenRouter API** to access multiple AI models (GPT-4, Claude, Gemini, etc.).

## Features

- **Multi-Channel Management**: Manage products and orders from Shopee, Lazada, and TikTok Shop
- **AI Product Classification**: Automatically classify products into Odoo categories using AI
- **AI Pricing Recommendations**: Get recommended selling prices with profit calculations
- **Profit Calculator**: Calculate detailed profit breakdowns including:
  - Platform fees (Commission)
  - Payment processing fees
  - Shipping subsidies
  - VAT calculations
  - Net profit margins
- **Order Management**: Create Sales Orders, Delivery Orders, and Invoices automatically
- **Stock Synchronization**: Keep inventory synced across all channels
- **Webhook Support**: Receive real-time order notifications

## Installation

### Prerequisites

1. Odoo 16 installed
2. Python libraries required:

```bash
pip install requests
```

3. Get OpenRouter API key from https://openrouter.ai/keys

### Installation Steps

1. Copy this module to your Odoo addons directory:
   ```
   /path/to/odoo/addons/multichannel_ai
   ```

2. Update apps list in Odoo

3. Install the module "Multi-Channel AI E-Commerce Integration"

### Configuration

1. Go to **Sales > Channels** and configure each channel:
   - Enter API credentials
   - Set warehouse and pricelist
   - Configure fee rates

2. Configure AI Engine:
   - Go to **Sales > AI Engine**
   - Enter OpenRouter API key (get from https://openrouter.ai/keys)
   - Select AI model (recommended: google/gemini-2.0-flash-exp:free for free tier)
   - Set default fee rates

## Module Structure

```
multichannel_ai/
├── models/
│   ├── channel_config.py      # Channel configuration
│   ├── ai_engine.py           # AI classification & pricing
│   ├── channel_product.py     # Product mapping
│   └── channel_order.py       # Order management
├── controllers/
│   ├── webhook_controller.py   # Webhook endpoints
│   └── main_controller.py     # Dashboard & API
├── wizards/
│   ├── profit_calculator_wizard.py
│   └── sync_wizard.py
├── views/                     # XML views
├── security/                  # Access control
└── static/                   # JS & CSS
```

## Usage

### Adding Products to Channels

1. Go to **Sales > Channel Products**
2. Create new product mapping
3. Select product and channel
4. Set channel price
5. Click "AI Classify" to auto-categorize
6. Click "Sync to Channel" to upload

### Viewing Profit Calculator

1. Go to **Sales > Profit Calculator**
2. Select product and channel
3. Enter selling price
4. View detailed profit breakdown

### Syncing Orders

Orders are automatically created via webhooks when customers place orders on channels. You can also:
1. Go to **Sales > Channel Orders**
2. Click "Create Sale Order" to convert to Odoo SO
3. Click "Create Invoice" for billing

## Fee Structure (Thailand 2024)

| Channel | Commission | Payment Fee | Shipping Subsidy |
|---------|------------|-------------|-----------------|
| Shopee | 5% | 2% | 2.5% |
| Lazada | 5% | 2% | 3% |
| TikTok Shop | 3.5% | 1.5% | 2% |

All rates are before VAT (7%).

## API Webhooks

The module provides webhook endpoints:
- `POST /multichannel/shopee/webhook`
- `POST /multichannel/lazada/webhook`
- `POST /multichannel/tiktok/webhook`

## Support

For issues or questions, please contact the development team.

## License

LGPL-3