# AI Crypto Trading Monitor

บอทสแกนกราฟคริปโต (BTC/USDT) ดึงข้อมูลจาก Binance คำนวณ Indicators (RSI, MACD, ATR, EMA), ตรวจจับ Candlestick Patterns (11 แบบ), Fibonacci และ VPVR แล้วส่งให้ AI วิเคราะห์จุดเข้า 3 ระดับ (3-Tier Entry) พร้อม TP/SL แสดงผลบน Terminal ด้วย Rich UI

**เวอร์ชัน:** 1.5.1

---

## 📋 สารบัญ

1. [โครงสร้างโปรเจกต์](#-โครงสร้างโปรเจกต์)
2. [วิธีติดตั้ง](#-วิธีติดตั้ง)
3. [การตั้งค่า](#-การตั้งค่า)
4. [วิธีใช้งาน](#-วิธีใช้งาน)
5. [Display Modes](#-display-modes)
6. [AI Trigger System](#-ai-trigger-system)
7. [Indicators และการปรับแต่ง](#-indicators-และการปรับแต่ง)
8. [Candlestick Patterns](#-candlestick-patterns)
9. [การแก้ปัญหา](#-การแก้ปัญหา)
10. [คำเตือน](#-คำเตือน)

---

## 📁 โครงสร้างโปรเจกต์

| ไฟล์ | คำอธิบาย |
|-------|-----------|
| `main.py` | Entry point + main loop (Full Version) |
| `maincli.py` | CLI Interface (Click-based) |
| `config.py` | Configuration ทั้งหมด |
| `indicators.py` | Indicators, Fibonacci, VPVR |
| `ai_trigger.py` | Smart Trigger + Cooldown System |
| `ai_client.py` | AI Context + OpenRouter API |
| `display.py` | Rich UI Display (3 modes) |
| `candlestick_patterns.py` | Candlestick Patterns (11 แบบ) |
| `backtest.py` | Backtest Performance |

---

## 🚀 วิธีติดตั้ง

```bash
# 1. Clone หรือ cd เข้าโฟลเดอร์
cd /Users/Parinya/VSCode/BinanceMonitor

# 2. สร้าง Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 3. ติดตั้ง Dependencies
pip3 install -r requirements.txt

# 4. คัดลอก .env.example เป็น .env
cp .env.example .env

# 5. กรอก API Key ในไฟล์ .env (ดูวิธีด้านล่าง)
```

### การขอ API Key

**OpenRouter API Key (จำเป็นสำหรับ AI วิเคราะห์):**
1. ไปที่ https://openrouter.ai/
2. สมัครสมาชิก + เติมเครดิต (เริ่มต้น $5)
3. สร้าง API Key แล้วกรอกใน `.env`

**Binance API Key (ไม่บังคับ - สำหรับเพิ่ม rate limit):**
1. ไปที่ https://www.binance.com/
2. Settings > API Management
3. สร้าง API Key (แนะนำ Read-Only)



---

## ⚙️ การตั้งค่า

### ไฟล์ `.env`

```env
# จำเป็น - OpenRouter API Key
OPENROUTER_API_KEY=your_openrouter_api_key_here

# ไม่บังคับ - Binance API Keys
BINANCE_API_KEY=
BINANCE_API_SECRET=

# ไม่บังคับ - เปลี่ยน Model
OPENROUTER_MODEL=deepseek/deepseek-chat
```

### ไฟล์ `config.py`

```python
# Trading Configuration
SYMBOL = "BTC/USDT"              # คู่เทรด
TIMEFRAME = "1h"                # Timeframe: 1m, 5m, 15m, 1h, 4h, 1d
CANDLE_LIMIT = 100              # จำนวน candles ที่ดึง
SWING_LOOKBACK = 5              # หา Swing High/Low
VPVR_BINS = 50                  # จำนวน bins สำหรับ VPVR
VALUE_AREA_PCT = 0.70           # Value Area (70% ของ volume)

# Display Configuration
DISPLAY_MODE = "standard"        # standard | compact | verbose

# AI Trigger Mode
AI_TRIGGER_MODE = "smart"        # smart | schedule | manual

# Smart Trigger Settings
TRIGGER_RSI_EXTREME = True
TRIGGER_PATTERN = True
TRIGGER_MACD_CROSS = True
TRIGGER_NEAR_LEVEL = True
TRIGGER_HIGH_VOLATILITY = True
TRIGGER_BIG_MOVE = False

# Cooldown
AI_COOLDOWN_MAX_PER_HOUR = 3
AI_COOLDOWN_SECONDS = 300

# Test Mode
TEST_MODE = True                 # True = 1 รอบ, False = รันต่อเนื่อง
```

---

## ▶️ วิธีใช้งาน

### 🖥️ แบบที่ 1: `main.py` (Full Version)
```bash
# รันแบบ Test (1 รอบแล้วจบ)
python3 main.py

# รันแบบ Scheduled (ทุกชั่วโมง)
# แก้ config.py: TEST_MODE = False
python3 main.py
```

### 🖥️ แบบที่ 2: `maincli.py` (CLI Interface - แนะนำ)
```bash
# ดูคำสั่งทั้งหมด
python3 maincli.py --help

# วิเคราะห์ครั้งเดียว
python3 maincli.py analyze -s BTC/USDT -t 1h -m compact
python3 maincli.py analyze -s ETH/USDT -t 4h -m standard

# Monitor ต่อเนื่อง
python3 maincli.py monitor -s BTC/USDT -t 1h -i 15 --max-runs 5

# Quick Backtest
python3 maincli.py backtest -s BNB/USDT -t 1h -l 100

# แสดง Configuration
python3 maincli.py config

# แสดง Symbols ยอดนิยม
python3 maincli.py symbols
```

| คำสั่ง | Options | คำอธิบาย |
|--------|---------|----------|
| `analyze` | `-s, --symbol` `-t, --timeframe` `-m, --mode` | วิเคราะห์ตลาดครั้งเดียว |
| `monitor` | `-s, --symbol` `-t, --timeframe` `-i, --interval` `--max-runs` | วิเคราะห์ต่อเนื่อง |
| `backtest` | `-s, --symbol` `-t, --timeframe` `-l, --limit` | Quick Backtest |
| `config` | - | แสดงค่า Configuration |
| `symbols` | - | แสดง Symbols ยอดนิยม |

---

## 🎨 Display Modes

| Mode | คำอธิบาย | Backtest | Definitions |
|------|-----------|----------|-------------|
| `standard` | ตาราง + Key Levels + Patterns | ✅ | ❌ |
| `compact` | 1 บรรทัดสรุป เห็นเร็วๆ | ❌ | ❌ |
| `verbose` | มีคำอธิบายใต้ตาราง (ภาษาไทย) | ✅ | ✅ |

---

## 🤖 AI Trigger System

### Trigger Modes

| Mode | คำอธิบาย |
|------|-----------|
| `smart` | ส่งเมื่อ indicators ตรงเงื่อนไข (แนะนำ) |
| `schedule` | ส่งทุก X นาทีตาม `SCHEDULE_INTERVAL_MINUTES` |
| `manual` | กด A เพื่อส่ง AI เอง |

### Smart Triggers

| Trigger | Default | คำอธิบาย | ค่าที่ปรับ |
|---------|---------|-----------|------------|
| RSI Extreme | ✅ | RSI < 30 หรือ > 70 | `RSI_OVERSOLD`, `RSI_OVERBOUGHT` |
| Pattern | ✅ | มี Bullish/Bearish pattern | - |
| MACD Cross | ✅ | MACD ตัด Signal line | - |
| Near Level | ✅ | ใกล้ Fib/VPVR ±0.5% | `LEVEL_DISTANCE_PCT` |
| High Volatility | ✅ | ATR > 1.5% ของราคา | `ATR_HIGH_PCT` |
| Big Move | ❌ | ราคาเปลี่ยน > 1% | `BIG_MOVE_PCT` |

### Cooldown

- **ส่งได้สูงสุด:** 3 ครั้ง/ชั่วโมง
- **ห่างกันอย่างน้อย:** 5 นาที (300 วินาที)



---

## 📊 Indicators และการปรับแต่ง

### RSI (Relative Strength Index)

| ค่า | สถานะ | ความหมาย |
|-----|--------|----------|
| 0-30 | 🟢 Oversold | ราคาขายมากเกินไป แนวโน้มกลับตัวขึ้น |
| 30-70 | ⚪ Neutral | โมเมนตัมปกติ ไม่มีสัญญาณชัด |
| 70-100 | 🔴 Overbought | ราคาซื้อมากเกินไป แนวโน้มกลับตัวลง |

**ปรับแต่ง:**
```python
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
```

**คำแนะนำ:**
- **Scalping (5m-15m):** ใช้ RSI 20/80 (ไวต่อการกลับตัว)
- **Swing (1h-4h):** ใช้ RSI 30/70 (default)
- **Long-term (1d):** ใช้ RSI 40/60 (ไม่ไวเกินไป)

### MACD

| Histogram | สถานะ | ความหมาย |
|-----------|--------|----------|
| > 0 | 🟢 Bullish | แรงซื้อเพิ่ม แนวโน้มขาขึ้น |
| < 0 | 🔴 Bearish | แรงขายเพิ่ม แนวโน้มขาลง |
| ตัด 0 ขึ้น | 🟢 Signal | กลับตัวเป็นขาขึ้น |
| ตัด 0 ลง | 🔴 Signal | กลับตัวเป็นขาลง |

### ATR (Average True Range)

ใช้วัด **ความผันผวน** และกำหนด Stop Loss / Take Profit

| ATR | ความผันผวน | คำแนะนำ |
|-----|-------------|----------|
| < 1% | ต่ำ | ตลาดเงียบ ไม่ควรเข้า |
| 1-2% | ปกติ | ควรเข้าได้ |
| > 2% | สูง | ระวัง มี news |

```python
ATR_HIGH_PCT = 1.5    # ATR > 1.5% = high volatility
# SL = ราคา - (ATR × 1.5)
# TP = ราคา + (ATR × 2)
```

### EMA

| EMA vs ราคา | สถานะ | ความหมาย |
|-------------|--------|----------|
| ราคา > EMA | 🟢 Uptrend | แนวโน้มขาขึ้น |
| ราคา < EMA | 🔴 Downtrend | แนวโน้มขาลง |
| ราคา ≈ EMA | ⚪ Sideways | ไม่ชัดเจน |

### Fibonacci Retracement

| ระดับ | ความสำคัญ |
|--------|-----------|
| 0.382 | ระดับตั้งต้น |
| 0.500 | กึ่งกลาง |
| **0.618** | Golden Ratio - โอกาสกลับตัวสูงสุด |

### VPVR (Volume Profile)

| ระดับ | ความหมาย |
|--------|----------|
| POC | ราคาที่มี volume ซื้อขายสูงสุด |
| VAH | ขอบบน Value Area 70% - แนวต้าน |
| VAL | ขอบล่าง Value Area 70% - แนวรับ |

---

## 🕯️ Candlestick Patterns (11 แบบ)

### 🟢 Bullish
- **Bullish Engulfing** - กลืนขาขึ้น
- **Hammer** - ค้อน
- **Bullish Pin Bar** - Pin Bar ขาขึ้น
- **Piercing Line** - เจาะทะลุ

### 🔴 Bearish
- **Bearish Engulfing** - กลืนขาลง
- **Bearish Pin Bar** - Pin Bar ขาลง
- **Shooting Star** - ดาวตก
- **Hanging Man** - คนแขวน
- **Dark Cloud Cover** - เมฆคลุม

### ⚪ Neutral
- **Doji** - เทียนศูนย์
- **Inverted Hammer** - ค้อนกลับ

### ปรับแต่ง Sensitivity
```python
DOJI_BODY = 0.1
PIN_RATIO = 2.0
HAMMER_WICK = 0.5
HAMMER_POS = 0.6
SHOOT_POS = 0.4
```

**ค่าที่สูงขึ้น = Pattern ยากขึ้น (ผ่านน้อยกว่า)**
**ค่าที่ต่ำลง = Pattern ง่ายขึ้น (ผ่านมากขึ้น)**

---

## 🐛 การแก้ปัญหา

### Module not found
```bash
pip3 install -r requirements.txt
```

### API Key error
1. เปิดไฟล์ `.env`
2. ใส่ `OPENROUTER_API_KEY=your_key_here`
3. รีสตาร์ทโปรแกรม

### SSL Error (macOS)
```bash
brew install openssl@3
```

### SSL Warning (urllib3 + LibreSSL)
โปรแกรมนี้ suppress warning เรียบร้อยแล้ว (macOS, Linux, Windows)  
ถ้ายังเจอ warning ให้ลอง:
```bash
pip3 install --upgrade urllib3 certifi
```

---

## ⚠️ คำเตือน

> **โปรแกรมนี้เป็นเครื่องมือช่วยวิเคราะห์เท่านั้น ไม่ใช่คำแนะนำในการลงทุน**
>
> - ผลการวิเคราะห์จาก AI เป็นเพียงข้อมูลประกอบการตัดสินใจ
> - การลงทุนในคริปโตมีความเสี่ยงสูง
> - ควรศึกษาข้อมูลและบริหารความเสี่ยงด้วยตนเอง

---

## 📚 คำศัพท์ที่ควรรู้

| คำศัพท์ | ความหมาย |
|----------|----------|
| RSI | Relative Strength Index |
| MACD | Moving Average Convergence Divergence |
| ATR | Average True Range |
| EMA | Exponential Moving Average |
| Fibonacci | ระดับราคาจากสัดส่วนทองคำ |
| VPVR | Volume Profile |
| POC | Point of Control |
| TP/SL | Take Profit / Stop Loss |
| Bullish | แนวโน้มขาขึ้น |
| Bearish | แนวโน้มขาลง |

---

**เวอร์ชัน:** 1.5.1  
**อัปเดตล่าสุด:** 2026-08-30  
**GitHub:** https://github.com/bbcnsshop/AI-Crypto-Trading-Monitor
