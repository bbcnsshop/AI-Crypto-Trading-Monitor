"""
AI Client Module
================
ส่งข้อมูลไปให้ OpenRouter AI วิเคราะห์
"""

from openai import OpenAI
from config import (
    OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL
)


# System prompt สำหรับ AI
SYSTEM_PROMPT = """You are an expert crypto trading analyst.
Analyze the provided market data (price, indicators, patterns, Fibonacci, VPVR)
and give a concise trading plan with 3-tier entry, TP, and SL.
Be brief and structured."""


def build_ai_context(data) -> str:
    """
    สร้าง Context ข้อมูลทั้งหมดสำหรับส่งให้ AI
    """
    ctx = []
    ctx.append("=== MARKET DATA ===")
    ctx.append(f"Symbol: {data.symbol if hasattr(data, 'symbol') else 'BTC/USDT'}")
    ctx.append(f"Timeframe: {data.timeframe if hasattr(data, 'timeframe') else '1h'}")
    ctx.append(f"Latest Price: {data.latest_close:.2f}")
    ctx.append("")
    
    if data.indicators:
        ctx.append("=== INDICATORS ===")
        for k, v in data.indicators.items():
            if v is not None:
                if isinstance(v, float):
                    ctx.append(f"{k}: {v:.4f}")
                else:
                    ctx.append(f"{k}: {v}")
        ctx.append("")
    
    if data.patterns:
        ctx.append("=== CANDLESTICK PATTERNS ===")
        for k, v in data.patterns.items():
            if isinstance(v, bool):
                ctx.append(f"{k.replace('_', ' ').title()}: {'DETECTED' if v else 'None'}")
            elif k == 'latest_pattern' and v != 'None':
                ctx.append(f"Latest Pattern: {v}")
        ctx.append("")
    
    if data.fibonacci:
        ctx.append("=== FIBONACCI RETRACEMENT ===")
        for k in ['fib_382', 'fib_500', 'fib_618', 'fib_786']:
            if k in data.fibonacci:
                ctx.append(f"Fib {k.replace('fib_', '')}: {data.fibonacci[k]:.2f}")
        ctx.append("=== FIBONACCI EXTENSION (TP TARGETS) ===")
        for k in ['ext_1272', 'ext_1618']:
            if k in data.fibonacci:
                ctx.append(f"Extension {k.replace('ext_', '')}: {data.fibonacci[k]:.2f}")
        ctx.append("")
    
    if data.vpvr:
        ctx.append("=== VOLUME PROFILE (VPVR) ===")
        ctx.append(f"POC (Point of Control): {data.vpvr.get('poc', 0):.2f}")
        ctx.append(f"VAH (Value Area High): {data.vpvr.get('vah', 0):.2f}")
        ctx.append(f"VAL (Value Area Low): {data.vpvr.get('val', 0):.2f}")
        ctx.append("")
    
    if 'atr' in data.indicators:
        ctx.append(f"ATR (14): {data.indicators['atr']:.4f}")
        ctx.append(f"SL Buffer (0.5 * ATR): {data.indicators['atr'] * 0.5:.4f}")
        ctx.append("")
    
    return "\n".join(ctx)


def call_openrouter_ai(context: str) -> str:
    """
    เรียก OpenRouter API
    """
    if not OPENROUTER_API_KEY:
        return "[ERROR] OPENROUTER_API_KEY ไม่ได้ตั้งค่าใน .env"
    try:
        client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context},
            ],
            temperature=0.3, max_tokens=2500,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[ERROR] OpenRouter API: {e}"
