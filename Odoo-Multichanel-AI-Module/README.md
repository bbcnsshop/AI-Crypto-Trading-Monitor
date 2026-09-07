# Odoo Multi-Channel AI Module

> Multi-Channel E-Commerce Integration for Odoo 16 with AI Engine (OpenRouter)

รองรับ Shopee, Lazada, TikTok Shop - รวม Sync, OAuth, AI Auto-Fill

**🧪 Tested:** ~370 tests across 30+ test files — 6 ก.ย. 2569

**📊 Coverage:** 16/20 models at 100% + Wizards + Mixins + Connectors (Shopee/Lazada/TikTok) + Cron + OAuth + i18n

**✅ Phases 1-38 Complete:** ai_engine + <MODULE_NAME> installed on server

**📦 Modules:**
- `ai_engine` - AI Product Classification & Price Recommendation (OpenRouter)
- `<MODULE_NAME>` - Multi-Channel E-Commerce Integration

---

## 📋 Features

### 🛒 Multi-Channel Support
- Shopee, Lazada, TikTok Shop
- Sandbox (MOCK) / Production mode (`api_url='sandbox'` / `api_url='production'`)
- OAuth token management with auto-refresh
- 39 connector methods (13 per platform × 3 platforms)

### 🛒 Order Management (Enhanced)
- Channel Order Line with margin tracking
- Sale Order Channel integration
- Order sync from platforms
- Create Delivery/Invoice from Channel Order
- Cancel/Refund on platform

### 🧙 Wizards (5 wizards)
- **Add to Channel Wizard** - Add products to channel with preview
- **Channel List Add Wizard** - Add new platform channel
- **Channel Product AI Fill Wizard** - Bulk AI auto-fill
- **Channel Product Attribute Wizard** - Generate attribute mappings
- **Profit Calculator Wizard** - Calculate profit with fees

### 🔧 Mixins (4 mixins)
- **ConnectionMixin** - Connector factory + test connection
- **CountsMixin** - Computed counts + navigation actions
- **SyncActionsMixin** - Bulk sync actions
- **TokenActionsMixin** - Token refresh + cron job

### 🤖 AI Engine (OpenRouter)
- Auto-fill product fields (barcode, condition, brand)
- Price recommendation
- Product classification

### 📸 Image & Video Management
- Channel Product Image with multi-source (product/variant/URL)
- Channel Product Video with S3 integration
- Platform-specific image IDs (Shopee/Lazada/TikTok)
- Auto alt text generation

### 📊 Order Management
- Webhook integration
- Create Sale Order from Channel Order
- Order status tracking

### 🧪 Quality Assurance
- **Remote Dry-Run Validation** - validate XML + Python บน production server ก่อน deploy
- ตรวจ 72 ไฟล์ (32 XML + 40 Python) ใช้เวลา < 1 วินาที
- Bug detection: mismatched tag, orphan entry, indentation, duplicated code

---

## 📁 Structure

```
<MODULE_NAME>/
├── models/
│   ├── channel_config.py           # Channel settings
│   ├── channel_product.py         # Channel product management
│   ├── channel_product_image.py   # Product images
│   ├── channel_product_video.py   # Product videos
│   ├── channel_product_attribute.py # Attribute mappings
│   ├── channel_product_field_mapping.py # Field mappings + completeness
│   ├── channel_order.py           # Order management
│   ├── sale_order_channel.py      # Sale order integration
│   ├── price_recommendation.py    # AI pricing
│   ├── category_mapping.py         # Category mapping
│   ├── channel_list_module.py     # Platform list
│   ├── mixins/                    # Method mixins
│   │   ├── sync_actions.py        # Sync products/orders
│   │   ├── connection.py          # Connector factory
│   │   ├── token_actions.py       # Token refresh
│   │   └── counts.py              # Computed counts
│   └── connectors/                # API connectors
│       ├── base.py                # Abstract base
│       ├── shopee.py              # Shopee API
│       ├── lazada.py              # Lazada API
│       ├── tiktok.py              # TikTok API
│       └── mock_data.py           # Mock data
├── controllers/
│   ├── main_controller.py         # Dashboard & API
│   ├── oauth_controller.py        # OAuth flow
│   ├── webhook_controller.py      # Webhooks
│   └── video_controller.py        # Video serving
├── wizards/
├── views/
└── i18n/                          # Translations (POT/TH)

ai_engine/
├── models/
│   ├── ai_engine.py               # AI Engine (OpenRouter)
│   └── ai_category_mapping.py     # Category mappings
└── tests/                         # AI tests
```

---

## 🚀 Quick Start

### 1. Install Module
```bash
# Copy to Odoo addons path
cp -r <MODULE_NAME> <ADDONS_PATH>/
cp -r ai_engine <ADDONS_PATH>/

# Update apps list and install
odoo-bin -d <DB_NAME> -i <MODULE_NAME> --stop-after-init
```

### 2. Configure Channel
Go to **Sales > Channels** and add Shopee/Lazada/TikTok credentials.

### 3. Sync Products
Select products and click **Add to Channel**.

### 4. Sync Orders
Orders sync automatically via webhooks.

---

## 🧪 Test Coverage

| Category | Files | Methods |
|----------|-------|---------|
| Models | 16 | ~180 |
| AI Engine | 3 | ~20 |
| Integration | 13 | ~162 |
| **รวม** | **32** | **~362** |

Run tests:
```bash
odoo-bin -d <DB_NAME> -i <MODULE_NAME> --test-enable --stop-after-init
```

---

## ✅ Validation

```bash
# Python syntax
python3 -m py_compile <MODULE_NAME>/models/*.py

# XML validation
python3 -c "import xml.etree.ElementTree as ET; ET.parse('<MODULE_NAME>/views/*.xml')"
```

---

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for full history.

---

## 📄 License

LGPL-3
