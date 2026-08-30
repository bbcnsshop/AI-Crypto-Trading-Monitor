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
- [สรุปสั้นๆ: RSI, MACD, EMA สถานะ และ Candlestick Pattern สำคัญที่พบ]
- [VPVR โซน POC/VAH/VAL อยู่ตรงไหนของราคาปัจจุบัน]

⚠️ 2. จุดเฝ้าระวังและความเสี่ยง (Risk Warning):
- [รูปแบบ Pattern ใดๆ ที่พบ (เช่น Bullish Engulfing, Doji etc.) และสถานะ]
- [ความเสี่ยงจาก Indictors: RSI overbought/oversold, MACD divergence, EMA ยุ่งเหยิง]
- [ความผันผวน: ATR สูง/ต่ำ - ส่งผลต่อ SL/TP อย่างไร]

🎯 3. แผนเทรด 3-Tier Entry (Multi-Indicator Based):

**การกำหนด TP/SL เหมือนกันสำหรับทุก Tier:**
- TP 1: ที่ระดับ VAH (Value Area High) หรือ Fibonacci Extension 1.272
- TP 2: ที่ Fibonacci Extension 1.618 (Golden Target)
- SL: ใต้แนวรับสำคัญ (POC, VAL, หรือ Fibonacci สำคัญ) บวก Buffer 0.5 x ATR

**Entry Tiers แต่ละระดับ:**
- **Tier 1 (Aggressive)** : เข้าเร็วใกล้โซนรับราคา
  - Entry: ใกล้ VAL (Value Area Low) หรือ Fibonacci 0.500
  - SL: ใต้ VAL - 0.5 x ATR
  - TP1: VAH หรือ Fib 1.272
  - TP2: Fib 1.618
  - RR: ประมาณ 2.0-2.5:1
- **Tier 2 (Moderate)** : เข้าเทรดหลังราคาย่อตัว
  - Entry: ใกล้ Fibonacci 0.618 หรือ POC (Point of Control)
  - SL: ใต้ POC - 0.5 x ATR
  - TP1: VAH หรือ Fib 1.272
  - TP2: Fib 1.618
  - RR: ประมาณ 2.5-3.0:1
- **Tier 3 (Conservative)** : รอราคายิ่งต่ำสุดก่อนเข้า
  - Entry: ใต้ Fibonacci 0.786 หรือ Low สุดของช่วง
  - SL: ใต้ Fib 0.786 หรือ Low สุด - 0.5 x ATR
  - TP1: VAH หรือ Fib 1.272
  - TP2: Fib 1.618
  - RR: ประมาณ 3.0-4.0:1

💡 4. แผนบริหารเงินทุน (Position Sizing & Action):
- [แนะนำ % ไม้เทรดระหว่าง Entry 1, 2, 3 ให้เหมาะสมกับความเสี่ยง]
- [ควรเข้า Tier ใดก่อน: ถ้า RSI ยังไม่ overbought ให้เริ่ม Tier 1 ก่อน]
- [แนวทาง: รอ Pullback กลับลงมาเปิดTier 2 หรือเข้า Tier 1 เต็มที่แล้วรอ Pullback ตาม]
- [คำแนะนำการจัดการออเดอร์: ตั้ง Trailing Stop ที่ TP1 เมื่อ price ขึ้นผ่าน, หรือใช้เป็นการexit one-half ที่ TP1 ค้าง TP2]

ตัวอย่างการตอบ:
```
📌 1. ภาพรวมตลาด:
- RSI 76.9 (Overbought), MACD Hist +119 (Bullish), EMA20 ขึ้นเหนือ EMA50
- ราคา $78,117 อยู่เหนือ POC $79,516 แต่ใกล้ VAH $80,479
- Pattern ที่พบ: Bullish Engulfing บน Timeframe 1h
- VPVR: POC $79,516, VAH $80,479, VAL $78,616

⚠️ 2. จุดเฝ้าระวัง:
- RSI 76.9 แจ้งเตือน Overbought - เสี่ยงการกลับตัวลงสั้น
- MACD ยัง Bullish แต่ Histogram เริ่มโค้งตัวลงเล็กน้อย
- ความผันผวนสูง ATR 215 - ต้องตั้ง SL ห่างพอสมควร
- Pattern Bullish Engulfing แต่อยู่ใกล้แนวต้าน VAH - อาจเป็น Fakeout

🎯 3. แผนเทรด 3-Tier:
| Tier | Entry | SL | TP1 | TP2 | RR |
|------|-------|-----|-----|-----|-----|
| Tier 1 | 78,616 (VAL) | 77,500 | 79,516 | 80,479 | 2.1:1 |
| Tier 2 | 77,604 (Fib 0.618) | 77,000 | 79,516 | 80,479 | 2.8:1 |
| Tier 3 | 77,000 (ต่ำสุด) | 76,400 | 79,516 | 80,479 | 3.5:1 |

💡 4. แผนบริหารเงินทุน:
- เข้า Tier 1: 30% ของทุน (ราคาใกล้ VAL - เหมาะสำหรับทั้ง Bullish)
- เข้า Tier 2: 50% ของทุน (ราคาย่อตัวดีที่สุด - คอย pullback)
- เข้า Tier 3: 20% ของทุน (ราคาต่ำสุด - SL กว้างสุด)
- แนะนำ: อยู่ห่าง Tier 1 ตอนนี้ Overbought - รอ pullback มาที่ Tier 2 ก่อน
- ถ้า price ขึ้นข้าม VAH ให้ตั้ง Trailing Stop ที่ 79,516 (POC)
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
