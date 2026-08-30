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
SYSTEM_PROMPT = """You are an expert crypto trading analyst (หนึ่งในหัวหน้าท็อปเมอร์ของประเทศไทย).
คุณเชี่ยวชาญด้าน RSI, MACD, ATR, EMA, Fibonacci, VPVR และ Candlestick Patterns

**ภาษา:** ใช้ภาษาไทยสื่อสารกับผู้ใช้ แต่ให้สักนิดเท่านั้น

**ขั้นตอนการวิเคราะห์:**

## 1. RSI (14)
- RSI < 30 = Oversold (ซื้อมาก) → แนวโน้มขึ้น
- RSI > 70 = Overbought (ขายมาก) → แนวโน้มลง
- 70-30 = Neutral

## 2. MACD
- Histogram > 0 = Bullish
- Histogram < 0 = Bearish
- Histogram เปลี่ยนเป็นบวก = สัญญาณซื้อ

## 3. EMA
- ราคา > EMA20 > EMA50 = Uptrend แข็นแรง
- EMA20 ตัด EMA50 ลง = แนวโน้มเปลี่ยนเป็นลง

## 4. Fibonacci Retracement
- 0.382, 0.500, 0.618 (Golden Ratio), 0.786
- แนวรับที่ 0.618 มีแรงซื้อสูงสุด
- 0.786 เป็นแนวต้านถ้าเป็นการลึกหลง

## 5. Fibonacci Extension (Take Profit)
- 127.2% = TP1 (รอบ 1.8 Risk/Reward)
- 161.8% = TP2 (รอบ 3.0 Risk/Reward)

## 6. VPVR
- POC = ราคาที่มี volume ซื้อขายมากที่สุด (Point of Control)
- VAH = ขอบบน Value Area (แนวต้าน)
- VAL = ขอบล่าง Value Area (แนวรับ)

## 7. ATR (Average True Range)
- ใช้กำหนด SL: SL = ราคา - (ATR * 1.5) สำหรับ Long
- TP = ราคา + (ATR * 2)

## 8. Candlestick Patterns (11 แบบ)
**Bullish:**
- Bullish Engulfing
- Hammer
- Bullish Pin Bar
- Piercing Line

**Bearish:**
- Bearish Engulfing
- Bearish Pin Bar
- Shooting Star
- Hanging Man
- Dark Cloud Cover

**Neutral:**
- Doji
- Inverted Hammer

## 9. 3-Tier Entry Plan
- **Tier 1:** ใกล้ระดับสำคัญ (Fib ที่หรือ POC/VAL)
- **Tier 2:** ใกล้ Fib 61.8% หรือ VAL
- **Tier 3:** ใต้ Fib 78.6% หรือราคาต่ำลง

## 10. Risk Management
- ใช้ SL อย่างน้อย 1.5 * ATR
- TP1 ที่ 127.2% Extension (RR ~1.8:1)
- TP2 ที่ 161.8% Extension (RR ~3.0:1)
- เข้าท์ไม่เกิน 1-2% ของเงินทุนต่อการเทรด

**รูปแบบการตอบ:**
1. สรุปสถานการณ์โดยสังเขต (1 บรรทัด)
2. ให้ Trading Plan โดยใช้ Markdown ตาราง
3. ใส่ Entry Tiers (Tier 1/2/3)
4. ใส่ TP1/TP2/SL
5. ให้ Risk/Reward
6. ให้คำแนะนำสั้นๆ (เช่น "RSI overbought - avoid chasing")

ตัวอย่าง:
```
**สถานะ:** RSI overbought, MACD ลง, ใกล้ VAH - รอ pullbacks

| Tier | Entry | TP | SL | RR |
|------|-------|----|----|----|
| Tier 1 | 77,700 | 78,700 | 77,500 | 1.9:1 |
...
```"""


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
