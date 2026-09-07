# AI Engine - OpenRouter Integration for Odoo 16

## Overview

Standalone AI Engine module for Odoo 16 that provides AI-powered product classification and pricing recommendations using **OpenRouter API**.

## Features

- **OpenRouter API Integration** - Access multiple AI models through a single API:
  - GPT-4 / GPT-4o
  - Claude 3 (Sonnet, Opus, Haiku)
  - Gemini 2.0 Flash
  - Llama 3.1
  - Qwen 2.5
  - DeepSeek V3
  - And many more...

- **Local LLM Support** - Connect to Ollama for offline AI processing

- **AI Product Classification** - Automatically classify products into Odoo categories

- **AI Pricing Recommendations** - Get optimal selling prices considering:
  - Platform fees (Shopee, Lazada, TikTok Shop)
  - Payment processing fees
  - Shipping subsidies
  - VAT calculations (Thailand 7%)

## Installation

1. Copy module to your Odoo addons path:
   ```
   /path/to/odoo/addons/ai_engine
   ```

2. Update apps list in Odoo

3. Install module "AI Engine - OpenRouter Integration"

4. Get OpenRouter API key: https://openrouter.ai/keys

5. Configure AI Engine:
   - Go to **Settings > Technical > AI Engine**
   - Enter API Key
   - Select model (recommended: `google/gemini-2.0-flash-exp:free` for free tier)

## Configuration

| Setting | Description |
|---------|-------------|
| API Provider | OpenRouter (default) or Local Ollama |
| API Key | Get from https://openrouter.ai/keys |
| Model | Select from available models |
| Default Platform Fee | Commission rate % |
| Default Payment Fee | Payment processing fee % |
| Default Shipping Fee | Shipping subsidy % |
| VAT Rate | Thai VAT (default: 7%) |

## Available AI Models

### Free Tier
- `google/gemini-2.0-flash-exp:free` - Fast, recommended for start
- `meta-llama/llama-3.1-8b-instruct:free` - Open source
- `qwen/qwen-2.5-72b-instruct:free` - Large model

### Paid Tier
- `openai/gpt-4o` - Best overall performance
- `anthropic/claude-3.5-sonnet` - Excellent reasoning
- `deepseek/deepseek-chat` - Cost effective

## Usage

The AI Engine provides these methods that can be called from other modules:

```python
# Get default AI engine
ai_engine = self.env['ai.engine'].get_default_engine()

# Classify product
result = ai_engine.classify_product({
    'name': 'Product Name',
    'description': 'Product Description',
    'attributes': 'RAM: 16GB, CPU: i7'
})

# Get price recommendation
result = ai_engine.recommend_price({
    'name': 'Product Name',
    'cost': 15000
}, 'shopee')

# Calculate profit breakdown
result = ai_engine.calculate_profit(selling_price=20000, cost=15000, channel_code='shopee')
```

## Dependencies

- Odoo 16
- Python `requests` library

```bash
pip install requests
```

## License

LGPL-3