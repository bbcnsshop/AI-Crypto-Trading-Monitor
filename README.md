# AI Crypto Trading Monitor

บอทสแกนกราฟคริปโท (BTC/USDT) ดึงข้อมูลจาก Binance คำนวณ Indicators (RSI, MACD, ATR, EMA), ตรวจจับ Candlestick Patterns (11 แบบ), Fibonacci และ VPVR แล้วส่งให้ AI วิเคราะห์จุดเข้า 3 ระดับ (3-Tier Entry) พร้อม TP/SL แสดงผลบน Terminal ด้วย Rich UI

---

## 📋 สารบัญ

1. [โครงสร้างโปรเจกต์](#-โครงสร้างโปรเจกต์)
2. [วิธีติดตั้ง](#-วิธีติดตั้ง)
3. [การตั้งค่า](#-การตั้งค่า)
4. [วิธีใช้งาน](#-วิธีใช้งาน)
5. [AI Trigger System](#-ai-trigger-system)
6. [Display Modes](#-display-modes)
7. [Logging System](#-logging-system)
8. [Candlestick Patterns](#-candlestick-patterns)
9. [การแก้ปัญหา](#-การแก้ปัญหา)
10. [คำศัพท์ที่ควรรู้](#-คำศัพท์ที่ควรรู้)
11. [คำเตือน](#-คำเตือน)

---

## 📁 โครงสร้างโปรเจกต์

| ไฟล์ | คำอธิบาย |
|--------|-----------|
| `main.py` | Entry point + main loop (232 บรรทัด) |
| `config.py` | Configuration ทั้งหมด |
| `indicators.py` | Indicators, Fibonacci, VPVR |
| `ai_trigger.py` | Smart Trigger + Cooldown System |
| `ai_client.py` | AI Context + OpenRouter API |
| `display.py` | Rich UI Display (3 modes) |
| `candlestick_patterns.py` | Candlestick Patterns (11 แบบ) |
| `backtest.py` | Backtest/Winrate |

---

## 🚀 วิธีติดตั้ง

```bash
# 1. Clone
cd /Users/Parinya/VSCode/BinanceMonitor

# 2. Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 3. ติดตั้ง Dependencies
pip3 install -r requirements.txt

# 4. ตั้งค่า
cp .env.example .env

# 5. กรอก API Key ในไฟล์ .env
```

---

## ⚙️ การตั้งค่า

### ไฟล์ `.env`

```env
OPENROUTER_API_KEY=your_api_key_here
BINANCE_API_KEY=
BINANCE_API_SECRET=
SYMBOL=BTC/USDT
TIMEFRAME=1h
```

### ไฟล์ `config.py`

```python
TEST_MODE = True              # True = รัน 1 รอบ, False = รันทุกชั่วโมง
SYMBOL = "BTC/USDT"
TIMEFRAME = "1h"
DISPLAY_MODE = "standard"    # standard | compact | verbose
```

---

## ▶️ วิธีใช้งาน

```bash
# รันแบบ Test (1 รอบ)
python3 main.py

# รันแบบ Scheduled (ทุกชั่วโมง)
# แก้ config.py: TEST_MODE = False
python3 main.py

# รัน Backtest
python3 backtest.py
```

---

## 🤖 AI Trigger System

ระบบ Trigger อัจฉริยะประหยัด API

### Smart Triggers

| Trigger | Default | คำอธิบาย |
|---------|---------|-----------|
| RSI Extreme | ✅ ON | RSI < 30 หรือ > 70 |
| Pattern | ✅ ON | มี Bullish/Bearish pattern |
| MACD Cross | ✅ ON | MACD ตัด Signal line |
| Near Level | ✅ ON | ใกล้ Fib/VPVR ±0.5% |
| High Volatility | ✅ ON | ATR > 1.5% ของราคา |
| Big Move | ❌ OFF | ราคาเปลี่ยน > 1% |

### Cooldown

- ส่งได้สูงสุด **3 ครั้ง/ชั่วโมง**
- ห่างกันอย่างน้อย **5 นาที**

### ตัวอย่าง Output

```
Step 6: ส่ง AI... (SMART_TRIGGER)
  RSI Overbought (70.4 > 70) | Near Key Level
  ✓ AI (1/3)
```

---

## 🎨 Display Modes

| Mode | คำอธิบาย |
|------|-----------|
| `standard` | ตาราง + Key Levels + Patterns |
| `compact` | 1 บรรทัดสรุป เห็นเร็วๆ |
| `verbose` | มีคำอธิบายใต้ตาราง (Thai) |

เปลี่ยนโหมดใน `config.py`:
```python
DISPLAY_MODE = "verbose"
```

---

## 📝 Logging System

### ตำแหน่ง Log Files

```
logs/
├── trading_monitor.log      # Log ปัจจุบัน
├── trading_monitor.log.1    # Backup 1
├── trading_monitor.log.2   # Backup 2
└── trading_monitor.log.3   # Backup 3
```

### ระดับ Log

| Level | Console | File |
|-------|---------|------|
| `INFO` | ✅ | ❌ |
| `ERROR` | ✅ | ✅ |

---

## 🕯️ Candlestick Patterns (11 แบบ)

### Bullish (สัญญาณขาขึ้น)
- Bullish Engulfing, Bullish Pin Bar, Hammer, Piercing Line

### Bearish (สัญญาณขาลง)
- Bearish Engulfing, Bearish Pin Bar, Shooting Star, Hanging Man, Dark Cloud Cover

### Neutral
- Doji, Inverted Hammer

---

## 🐛 การแก้ปัญหา

```bash
# Module not found
pip3 install -r requirements.txt

# API Key error
# เปิด .env แล้วใส่ OPENROUTER_API_KEY
```

---

## 📚 คำศัพท์ที่ควรรู้

| คำศัพท์ | ความหมาย |
|---------|-----------|
| RSI | Relative Strength Index - วัดโมเมนตัม 0-100 |
| MACD | Moving Average Convergence Divergence - ดูเทรนด์ |
| ATR | Average True Range - วัดความผันผวน |
| EMA | Exponential Moving Average - ค่าเฉลี่ยเคลื่อนที่ |
| Fibonacci | ระดับราคาจากสัดส่วนทองคำ |
| VPVR | Volume Profile - โปรไฟล์ปริมาณซื้อขาย |
| POC | Point of Control - ราคาที่มี volume สูงสุด |
| TP/SL | Take Profit / Stop Loss |

---

## ⚠️ คำเตือน

> **สำคัญ:** โปรแกรมนี้เป็นเครื่องมือช่วยวิเคราะห์เท่านั้น **ไม่ใช่คำแนะนำในการลงทุน**
>
> - ผลการวิเคราะห์จาก AI เป็นเพียงข้อมูลประกอบการตัดสินใจ
> - การลงทุนในคริปโทมีความเสี่ยงสูง

---

**เวอร์ชัน:** 1.3.0  
**อัปเดตล่าสุด:** 2026-08-30  
**GitHub:** https://github.com/bbcnsshop/AI-Crypto-Trading-Monitor
