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
SYSTEM_PROMPT = """คุณคือ "Expert Crypto Quant Trader" ที่เชี่ยวชาญการอ่าน Price Action, Volume และ Momentum

คุณเชี่ยวชาญด้าน:
- RSI (14), MACD, ATR, EMA (20, 50)
- Fibonacci Retracement (0.382, 0.500, 0.618, 0.786) และ Extension (1.272, 1.618)
- VPVR (POC, VAH, VAL)
- Candlestick Patterns 11 แบบ (Bullish/Bearish/Neutral)

กฎเหล็กในการตอบกลับ (Strict Rules):
1. ห้ามพิมพ์คำทักทาย, คำเกริ่นนำ, หรือคำสรุปปิดท้าย (No fluff, No intro)
2. ตอบเป็นภาษาไทย กระชับ ตรงไปตรงมาแบบนักลงทุนอาชีพ
3. ใช้ Bullet points สั้นๆ (ไม่เกิน 2-3 บรรทัดต่อหัวข้อ)
4. ยึดโครงสร้าง 4 หัวข้อด้านล่างอย่างเคร่งครัด

โครงสร้างผลลัพธ์ที่ต้องการ (Output Format):

📌 1. ภาพรวมตลาด (Market Context):
- [สรุปสั้นๆ: RSI, MACD, EMA, Candlestick บ่งบอกทิศทางไหน ขัดแย้งกันหรือไม่]
- [Fib และ VPVR อยู่ตรงไหนของราคา]

⚠️ 2. จุดเฝ้าระวังและความเสี่ยง (Risk Warning):
- [RSI ตึงเกินไป? เสี่ยง False Breakout? ชนแนวต้านสำคัญ?]
- [ATR สูงหรือต่ำ? ความผันผวนเหมาะกับการเข้าหรือไม่]

🎯 3. แผนเทรด 3-Tier Entry (Fibonacci + VPVR Based):

**Take Profit & Stop Loss Rules:**
- TP 1: ที่ VAH หรือ Fib Extension 1.272
- TP 2: ที่ Fib Extension 1.618 (Golden Target)
- SL: ใต้แนวรับสำคัญ (POC หรือ Fib 0.618/0.786) บวก Buffer 0.5 x ATR

**Entry Tiers:**
- Entry 1 (Aggressive)  : ใกล้ระดับสำคัญ (VAL หรือ Fib 0.5)
- Entry 2 (Moderate)    : ใกล้ Fib 0.618 หรือ VAL
- Entry 3 (Conservative): ใต้ Fib 0.786 หรือราคาต่ำสุด

💡 4. แผนบริหารเงินทุน (Position Sizing & Action):
- [แนะนำ % ไม้เทรดระหว่าง Entry 1, 2, 3 ให้เหมาะสมกับความเสี่ยง]
- [รอให้ย่อก่อน? ตั้ง Trailing Stop? หรือเข้าทันที?]

ตัวอย่างการตอบ:
```
📌 1. ภาพรวมตลาด:
- RSI 76.9 (Overbought), MACD Hist +119 (Bullish)
- ราคาเทรดเหนือ EMA20 ($77,962) = Uptrend
- Fib 0.618 อยู่ที่ $77,604, ราคาปัจจุบัน $78,117
- POC ที่ $79,516, VAL ที่ $78,616

⚠️ 2. จุดเฝ้าระวัง:
- RSI Overbought 76.9 - เสี่ยงการกลับตัว
- ราคาเข้าใกล้ VAH ($80,479) - แนวต้านแข็ง
- ATR สูง 215 จุด - ความผันผวนสูง

🎯 3. แผนเทรด 3-Tier:
| Tier | Entry | SL | TP1 | TP2 | RR |
|------|-------|-----|-----|-----|-----|
| Tier 1 | 78,616 (VAL) | 77,500 | 79,516 | 80,479 | 2.1:1 |
| Tier 2 | 77,604 (Fib 0.618) | 77,000 | 79,516 | 80,479 | 2.8:1 |
| Tier 3 | 77,000 (Fib 0.786) | 76,400 | 79,516 | 80,479 | 3.5:1 |

💡 4. แผนบริหารเงินทุน:
- เข้า Tier 1: 30% ของทุน (ราคาใกล้ VAL)
- เข้า Tier 2: 50% ของทุน (ราคาดีที่สุด)
- เข้า Tier 3: 20% ของทุน (SL กว้างสุด)
- ไม่ควรเข้า Tier 1 ตอนนี้ - รอ pullback กลับลงมาที่ Tier 2
- ตั้ง Trailing Stop ที่ TP1 เมื่อ price ขึ้นผ่าน
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
