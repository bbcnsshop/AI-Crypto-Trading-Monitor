# AI Crypto Trading Monitor

บอทสแกนกราฟคริปโท (BTC/USDT) ดึงข้อมูลจาก Binance คำนวณ Indicators (RSI, MACD, ATR, EMA), ตรวจจับ Candlestick Patterns (11 แบบ), Fibonacci และ VPVR แล้วส่งให้ AI วิเคราะห์จุดเข้า 3 ระดับ (3-Tier Entry) พร้อม TP/SL แสดงผลบน Terminal ด้วย Rich UI

---

## 📋 สารบัญ

1. [วิธีติดตั้ง](#-วิธีติดตั้ง)
2. [วิธีใช้งาน](#-วิธีใช้งาน)
3. [การตั้งค่า](#-การตั้งค่า)
4. [ค่าพารามิเตอร์](#-ค่าพารามิเตอร์)
5. [ผลลัพธ์ที่ได้](#-ผลลัพธ์ที่ได้)
6. [การปรับแต่งขั้นสูง](#-การปรับแต่งขั้นสูง)
7. [การแก้ปัญหา](#-การแก้ปัญหา)
8. [📁 ไฟล์ในโปรเจกต์](#-ไฟล์ในโปรเจกต์)
9. [📝 Logging System](#-logging-system)

---

## 🚀 วิธีติดตั้ง

### 1. Clone หรือ Copy โฟลเดอร์

```bash
cd /Users/Parinya/VSCode/BinanceMonitor
```

### 2. สร้าง Virtual Environment (แนะนำ)

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# หรือ venv\Scripts\activate  # Windows
```

### 3. ติดตั้ง Dependencies

```bash
pip3 install --user -r requirements.txt
```

> หมายเหตุ: รองรับ Python 3.9+ ไม่ต้องติดตั้ง `pandas_ta` โปรแกรมคำนวณ Indicators ด้วย `ta` library และ Candlestick Patterns ด้วย custom library

### 4. ตั้งค่า Environment

```bash
cp .env.example .env
```

### 5. กรอก API Key

เปิดไฟล์ `.env` และใส่ API Key:
---

## ⚙️ การตั้งค่า

### ไฟล์ `.env`

```env
# ===== REQUIRED =====
OPENROUTER_API_KEY=your_api_key_here

# ===== OPTIONAL: Binance API (เพิ่ม Rate Limit) =====
BINANCE_API_KEY=
BINANCE_API_SECRET=

# ===== OPTIONAL: ปรับแต่ง =====
SYMBOL=BTC/USDT
TIMEFRAME=1h
CANDLE_LIMIT=100
OPENROUTER_MODEL=deepseek/deepseek-chat
```

> **หมายเหตุ:** Binance API Key มีหรือไม่มีก็ได้ โปรแกรมใช้ Public API ได้ปกติ (Rate Limit ~50 req/min)

### ไฟล์ `main.py` (ส่วนบนสุด)

```python
# ===== TEST MODE =====
TEST_MODE = True  # True = รัน 1 รอบ, False = รันตามเวลา

# ===== TRADING CONFIG =====
SYMBOL = "BTC/USDT"
TIMEFRAME = "1h"
CANDLE_LIMIT = 100
SWING_LOOKBACK = 5
VPVR_BINS = 50
VALUE_AREA_PCT = 0.70
```

---

## 📊 ค่าพารามิเตอร์

### 🔧 ค่าหลักที่ควรเข้าใจ

| พารามิเตอร์ | ค่า Default | คำอธิบาย |
|-------------|-------------|-----------|
| `TEST_MODE` | `True` | เปิดโหมดทดสอบ (รัน 1 รอบ) |
| `SYMBOL` | `"BTC/USDT"` | คู่เทรดที่ต้องการวิเคราะห์ |
| `TIMEFRAME` | `"1h"` | ช่วงเวลาของแท่งเทียน |
| `CANDLE_LIMIT` | `100` | จำนวนแท่งที่ดึงมาคำนวณ |

### 🔬 ค่าขั้นสูง

| พารามิเตอร์ | ค่า Default | คำอธิบาย |
|-------------|-------------|-----------|
| `SWING_LOOKBACK` | `5` | จำนวนแท่งที่ใช้หา Swing High/Low |
## 📖 คำอธิบายรายละเอียด

### TEST_MODE

```
True  = รันการวิเคราะห์ 1 รอบแล้วจบโปรแกรม
False = รันทุก 1 ชั่วโมง (นาทีที่ 0) ตลอดเวลา
```

### SYMBOL

```
รูปแบบ: "BASE/QUOTE"
ตัวอย่าง:
- "BTC/USDT"  = Bitcoin vs Tether
- "ETH/USDT"  = Ethereum vs Tether
- "BNB/BTC"   = BNB vs Bitcoin
```

### TIMEFRAME

```
รูปแบบ: ตัวเลข + ตัวอักษร
ตัวอย่าง:
- "1m"   = 1 นาที
- "5m"   = 5 นาที
- "15m"  = 15 นาที
- "1h"   = 1 ชั่วโมง (ค่าแนะนำ)
- "4h"   = 4 ชั่วโมง
- "1d"   = 1 วัน

💡 คำแนะนำ: Timeframe ยาวขึ้น = Signal น่าเชื่อถือมากขึ้น แต่โอกาสเข้าน้อยลง
```

### CANDLE_LIMIT

```
ค่า: ตัวเลขจำนวนเต็ม
ค่าแนะนำ: 100-500 แท่ง
ค่า Default: 100 แท่ง

ผลกระทบ:
- มาก = ใช้ข้อมูลย้อนหลังเยอะ, คำนวณนานขึ้น
- น้อย = อาจไม่เพียงพอหาจุด Swing High/Low
```

### SWING_LOOKBACK

```
ค่า: ตัวเลขจำนวนเต็ม
ค่าแนะนำ: 3-10 แท่ง
ค่า Default: 5 แท่ง

ความหมาย:
- หมายถึงการหาจุดที่ราคาสูงสุด/ต่ำสุดในช่วง 5 แท่งด้านซ้าย-ขวา
- ค่ามากขึ้น = หาจุด Swing ที่ใหญ่ขึ้น (Longer-term)
- ค่าน้อยลง = หาจุด Swing ที่เล็กลง (Shorter-term)
```

### VPVR_BINS

```
ค่า: ตัวเลขจำนวนเต็ม
ค่าแนะนำ: 30-100 ช่อง
ค่า Default: 50 ช่อง

ความหมาย:
- แบ่งช่วงราคาออกเป็น 50 ช่องเท่าๆ กัน
- แต่ละช่องจะถูกนับ Volume ที่ผ่านช่วงนั้น
- ช่องที่มี Volume มากที่สุด = POC (Point of Control)
```

### VALUE_AREA_PCT

```
ค่า: ทศนิยม 0-1
ค่าแนะนำ: 0.65-0.80
ค่า Default: 0.70 (70%)

ความหมาย:
- กำหนดว่า Value Area ครอบคลุม Volume กี่เปอร์เซ็นต์
- 70% = Value Area ครอบคลุม 70% ของ Volume ทั้งหมด
- VAH/VAL จะอยู่ที่ขอบเขตของ Value Area นี้
```

---

## 📈 ผลลัพธ์ที่ได้

### หน้าจอ Rich UI ประกอบด้วย:

#### 1. Table: Market & Indicators
| Metric | Value | Signal |
|--------|-------|--------|
| Price | $xx,xxx.xx | - |
| RSI (14) | xx.xx | Overbought/Oversold/Neutral |
| MACD Hist | x.xxxx | Bullish/Bearish |
| ATR (14) | x.xxx | - |
| EMA 20 | $xx,xxx.xx | - |

#### 2. Table: Key Levels (Fibonacci & VPVR)
| Level | Price | Distance % |
|-------|-------|------------|
| Fib 0.382 | $xx,xxx.xx | +x.xx% |
| Fib 0.500 | $xx,xxx.xx | +x.xx% |
| Fib 0.618 | $xx,xxx.xx | +x.xx% |
| POC | $xx,xxx.xx | +x.xx% |
| VAH | $xx,xxx.xx | +x.xx% |
| VAL | $xx,xxx.xx | +x.xx% |

#### 3. Table: Candlestick Patterns
| Pattern | Status |
|---------|--------|
| Bullish Engulfing | DETECTED / None |
| Bearish Engulfing | DETECTED / None |
| Bullish Pin Bar | DETECTED / None |
| Bearish Pin Bar | DETECTED / None |
| Doji | DETECTED / None |
| Hammer | DETECTED / None |
| Inverted Hammer | DETECTED / None |
| Shooting Star | DETECTED / None |
| Hanging Man | DETECTED / None |
| Piercing Line | DETECTED / None |
| Dark Cloud Cover | DETECTED / None |
| **Summary** | Bull: X / Bear: Y |

#### 4. Panel: AI Analysis
คำวิเคราะห์จาก AI แบ่งเป็น 3 ส่วน:
- โครงสร้างราคา & VPVR Zone
- แผนเทรด 3-Tier Entry (Entry, SL, TP1, TP2, R:R)
- คำแนะนำ Position Sizing %

| `VPVR_BINS` | `50` | จำนวนช่องราคาสำหรับ Volume Profile |
| `VALUE_AREA_PCT` | `0.70` | สัดส่วน Value Area (70% ของ Volume) |

---


```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
```

**วิธีขอ API Key:**
---

## 🔧 การปรับแต่งขั้นสูง

### เปลี่ยนคู่เทรด

```python
# main.py
SYMBOL = "ETH/USDT"  # แทน BTC
```

### เปลี่ยน Timeframe

```python
# main.py
TIMEFRAME = "4h"  # 4 ชั่วโมงแทน 1 ชั่วโมง
```

### เพิ่มจำนวนแท่งที่ดึง

```python
# main.py
CANDLE_LIMIT = 200  # ดึง 200 แท่ง
```

### ใช้ Timeframe อื่นๆ

```python
# ด้านล่างนี้คือตัวอย่าง
TIMEFRAME = "15m"   # 15 นาที - Scalping
TIMEFRAME = "1h"    # 1 ชั่วโมง - Day Trading
TIMEFRAME = "4h"    # 4 ชั่วโมง - Swing Trading
TIMEFRAME = "1d"    # 1 วัน - Position Trading
```

### เปลี่ยน Model AI

```env
# .env
OPENROUTER_MODEL=anthropic/claude-3-haiku
# หรือ
OPENROUTER_MODEL=openai/gpt-4o-mini
```

### เพิ่ม/ลด Bins ของ VPVR

```python
# main.py
VPVR_BINS = 100  # เพิ่มความละเอียดของ Volume Profile
```

---

## 🐛 การแก้ปัญหา

### ปัญหา: ModuleNotFoundError

```bash
pip3 install --user -r requirements.txt
```

### ปัญหา: API Key ผิดพลาด

```
[ERROR] OPENROUTER_API_KEY ไม่ได้ตั้งค่าใน .env
```

**แก้ไข:** ตรวจสอบว่าใส่ API Key ถูกต้องในไฟล์ `.env`

### ปัญหา: Network Error

```
[ERROR] OpenRouter API: Connection error
```

**แก้ไข:**
- ตรวจสอบอินเทอร์เน็ต
- ลองรอสักครู่แล้วรันใหม่

### ปัญหา: Rate Limit

```
[ERROR] OpenRouter API: Rate limit exceeded
```

**แก้ไข:**
- รอ 1 นาทีแล้วรันใหม่
- หรือเปลี่ยน API Key

### ปัญหา: ข้อมูลไม่พอ

```
[yellow]ข้อมูลไม่เพียงพอ[/yellow]
```

**แก้ไข:**
- เพิ่ม `CANDLE_LIMIT` ใน main.py
- ลอง timeframe ที่มีข้อมูลมากกว่า
---

## 🕯️ Candlestick Patterns (11 รูปแบบ)

บอทตรวจจับ **11 Candlestick Patterns** แบ่งเป็น Bullish / Bearish และแสดงผลรวม Bull/Bear Signals:

### Bullish Patterns (สัญญาณขาขึ้น)
| Pattern | คำอธิบาย |
|---------|----------|
| **Bullish Engulfing** | แท่งเขียวกลืนแท่งแดงก่อนหน้า |
| **Bullish Pin Bar** | แท่งที่มีไส้ล่างยาว (rejection ขาลง) |
| **Hammer** | ไส้ล่างยาว ≥ 50% ของ range, body อยู่ล่าง, เกิดหลังขาลง |
| **Inverted Hammer** | ไส้บนยาว ≥ 50%, body อยู่ล่าง, เกิดหลังขาลง (สัญญาณกลับตัว) |
| **Piercing Line** | แท่งเขียวเปิดต่ำกว่า low ของแท่งแดง และปิดเหนือ midpoint |

### Bearish Patterns (สัญญาณขาลง)
| Pattern | คำอธิบาย |
|---------|----------|
| **Bearish Engulfing** | แท่งแดงกลืนแท่งเขียวก่อนหน้า |
| **Bearish Pin Bar** | แท่งที่มีไส้บนยาว (rejection ขาขึ้น) |
| **Shooting Star** | ไส้บนยาว ≥ 50%, body อยู่บน, เกิดหลังขาขึ้น |
| **Hanging Man** | ไส้ล่างยาว, body อยู่บน, เกิดหลังขาขึ้น (สัญญาณกลับตัว) |
| **Dark Cloud Cover** | แท่งแดงเปิดสูงกว่า high ของแท่งเขียว และปิดต่ำกว่า midpoint |

### Neutral Pattern
| Pattern | คำอธิบาย |
|---------|----------|
| **Doji** | body ≤ 10% ของ range (ตลาดลังเล, ไม่มีทิศทางชัดเจน) |

### การตีความใน UI

ใน Rich UI จะแสดงตาราง **Candlestick Patterns** พร้อม:
- ✅ **DETECTED** = ตรวจพบ pattern นี้ในแท่งล่าสุด
- ⬜ **None** = ไม่พบ pattern นี้
- **Summary** = จำนวน Bullish signals vs Bearish signals ที่ตรวจพบทั้งหมด

> 💡 **Pattern Logic:** ใช้ custom geometric detection (wick ratio, body position, trend context) สำหรับ candlestick patterns ทั้ง 11 แบบ

---

## 📚 คำศัพท์ที่ควรรู้

| คำศัพท์ | ความหมาย |
|---------|----------|
| **POC** | Point of Control - ราคาที่มี Volume สูงสุด |
| **VAH** | Value Area High - ขอบบนของ Value Area |
| **VAL** | Value Area Low - ขอบล่างของ Value Area |
| **Fibonacci** | สัดส่วนทองคำใช้หาแนวรับ/แนวต้าน |
| **RSI** | Relative Strength Index - วัดโมเมนตัม |
| **MACD** | Moving Average Convergence Divergence |
| **ATR** | Average True Range - วัดความผันผวน |
| **Engulfing** | Pattern ที่แท่งปัจจุบันกลืนแท่งก่อนหน้า |
| **Pin Bar** | Pattern ที่มีไส้เทียนยาว |
| **Swing High/Low** | จุดสูงสุด/ต่ำสุดในช่วงที่กำหนด |
| **R:R** | Risk:Reward Ratio - อัตราส่วนความเสี่ยงต่อผลตอบแทน |
| **3-Tier Entry** | แผนเข้าซื้อ 3 ระดับ (Aggressive, Moderate, Conservative) |

---


## 📁 ไฟล์ในโปรเจกต์

| ไฟล์ | คำอธิบาย |
|------|----------|
| `main.py` | ไฟล์หลัก - รันการวิเคราะห์ทั้งหมด |
| `candlestick_patterns.py` | Custom library สำหรับตรวจจับ 11 Candlestick Patterns |
| `requirements.txt` | รายการ dependencies ที่ต้องติดตั้ง |
| `.env.example` | ตัวอย่างไฟล์ตั้งค่า environment |
| `README.md` | เอกสารประกอบโปรเจกต์ |
| `logs/` | โฟลเดอร์เก็บ log files (สร้างอัตโนมัติ) |

### candlestick_patterns.py

Custom library สำหรับตรวจจับ Candlestick Patterns โดยใช้ geometric detection:

```python
from candlestick_patterns import detect_candlestick_patterns

# ผลลัพธ์มี keys:
# - bullish_engulfing, bearish_engulfing (bool)
# - bullish_pin_bar, bearish_pin_bar (bool)
# - doji, hammer, inverted_hammer (bool)
# - shooting_star, hanging_man (bool)
# - piercing_line, dark_cloud_cover (bool)
# - bullish_signals, bearish_signals (list)
# - latest_pattern, pattern_candle_num (str/int)

result = detect_candlestick_patterns(df)
```

**Constants ที่ปรับแต่งได้:**
```python
DOJI_BODY = 0.1        # body ≤ 10% ของ range = Doji
PIN_RATIO = 2.0        # wick ≥ 2x body = Pin Bar
HAMMER_WICK = 0.5      # wick ≥ 50% ของ range
HAMMER_POS = 0.6       # body position ≥ 60% (บนสุด)
SHOOT_POS = 0.4        # body position ≤ 40% (ล่างสุด)
```

---


## 🤖 AI Trigger System (Smart + Cooldown)

โปรแกรมมีระบบ Trigger อัจฉริยะสำหรับส่งข้อมูลให้ AI วิเคราะห์ (ประหยัด API)

### Smart Triggers (ค่าเริ่มต้น)
| Trigger | Default | คำอธิบาย |
|---------|---------|-----------|
| RSI Extreme | ✅ ON | RSI < 30 หรือ > 70 |
| Pattern Detected | ✅ ON | มี Bullish/Bearish pattern |
| MACD Crossover | ✅ ON | MACD ตัด Signal line |
| Near Key Level | ✅ ON | ใกล้ Fib/VPVR ±0.5% |
| High Volatility | ✅ ON | ATR > 1.5% ของราคา |
| Big Move | ❌ OFF | ราคาเปลี่ยน > 1% (conservative) |

### Cooldown
- ส่งได้สูงสุด **3 ครั้ง/ชั่วโมง**
- ห่างกันอย่างน้อย **5 นาที**

### ตัวอย่าง Output
```
Step 6: ส่งข้อมูลให้ AI วิเคราะห์... (SMART_TRIGGER)
  Bullish Pattern (2 detected) | Near Key Level ($71800, 0.32%)
  ✓ AI Analyzed (Used: 1/3 this hour)
```

หรือเมื่อไม่มี trigger:
```
Step 6: ข้าม AI (ไม่มี trigger หรือ cooldown)
  Reason: No trigger conditions
  Used: 1/3 this hour
```

### การตั้งค่า
```python
TRIGGER_RSI_EXTREME = True
TRIGGER_PATTERN = True
TRIGGER_MACD_CROSS = True
TRIGGER_NEAR_LEVEL = True
TRIGGER_HIGH_VOLATILITY = True
TRIGGER_BIG_MOVE = False
AI_COOLDOWN_MAX_PER_HOUR = 3
AI_COOLDOWN_SECONDS = 300
```

---

## 🎨 Display Modes (3 โหมดแสดงผล)
## 🎨 Display Modes (3 โหมดแสดงผล)

โปรแกรมมีโหมดแสดงผล 3 รูปแบบให้เลือก แก้ที่ `main.py` บรรทัด 55-56:

```python
# Display mode: 'standard' | 'compact' | 'verbose'
DISPLAY_MODE = "standard"
```

### 🟢 Standard Mode (default - แบบเดิม)
- ตาราง Market & Indicators + Key Levels + Patterns
- ไม่มีคำอธิบาย (compact + clean)

### 🟡 Compact Mode (แบบย่อ)
- **1 บรรทัดสรุป**: Price + RSI + MACD + EMA20 พร้อม Signal
- **1 บรรทัด Key Levels**: Fib/POC/VAH/VAL
- **Pattern count**: Bull vs Bear

### 🔵 Verbose Mode (แบบเต็ม มีคำอธิบาย)
- ตารางทุกอย่าง + **คอลัมน์ "สถานะ"** (ภาษาไทย)
- **ใต้ตารางมี Definition Box** อธิบาย RSI, MACD, ATR, EMA, Fibonacci, VPVR, Patterns

### วิธีเปลี่ยนโหมด
```bash
# ใน main.py
DISPLAY_MODE = "verbose"  # เปลี่ยนเป็น standard | compact | verbose

# หรือผ่าน ENV
DISPLAY_MODE=verbose python3 main.py
```

---

## 📝 Logging System
## 📝 Logging System

โปรแกรมมีระบบ Logging ที่บันทึกข้อมูลการทำงานลงไฟล์และแสดงที่ Console

### ตำแหน่ง Log Files
```
logs/
├── trading_monitor.log      # Log file ปัจจุบัน
├── trading_monitor.log.1    # Backup 1
├── trading_monitor.log.2    # Backup 2
├── trading_monitor.log.3    # Backup 3
└── trading_monitor.log.4    # Backup 4
```

### การตั้งค่า
| พารามิเตอร์ | ค่า | คำอธิบาย |
|-------------|-----|----------|
| `LOG_DIR` | `logs/` | โฟลเดอร์เก็บ log |
| `LOG_FILE` | `logs/trading_monitor.log` | ชื่อไฟล์ log |
| `LOG_MAX_BYTES` | `10 MB` | ขนาดสูงสุดต่อไฟล์ |
| `LOG_BACKUP_COUNT` | `5` | จำนวน backup files |

### ระดับ Log (Log Levels)
| Level | คำอธิบาย |
|-------|----------|
| `INFO` | ข้อมูลทั่วไป (STEP ต่างๆ, ผลลัพธ์) |
| `ERROR` | ข้อผิดพลาด |
| `DEBUG` | ข้อมูลละเอียด (ปิดไว้เริ่มต้น) |

### ตัวอย่าง Log Output
```
2026-08-29 21:50:31 | INFO     | === AI CRYPTO TRADING MONITOR v1.0 STARTED | BTC/USDT 1h | Mode=True ===
2026-08-29 21:50:31 | INFO     | STEP 1: ดึงข้อมูลตลาด
2026-08-29 21:50:31 | INFO     | ดึงข้อมูลสำเร็จ: 100 แท่ง | Symbol=BTC/USDT | Timeframe=1h
2026-08-29 21:50:33 | INFO     | STEP 2: คำนวณ Indicators
2026-08-29 21:50:33 | INFO     | คำนวณ Indicators สำเร็จ (ta library)
...
```

### การดู Log
```bash
# ดู log ล่าสุด
cat logs/trading_monitor.log

# ดู log พร้อม tail (ติดตาม realtime)
tail -f logs/trading_monitor.log

# ดู log หลังจากเวลาที่กำหนด
grep "21:50" logs/trading_monitor.log

# ดูเฉพาะ ERROR
grep "ERROR" logs/trading_monitor.log
```

> 💡 **Tip:** Log file จะถูกหมุนเวียนอัตโนมัติเมื่อถึง 10 MB ระบบจะเก็บ backup ไว้ 5 ไฟล์

---

## ⚠️ คำเตือน

> **สำคัญ:** โปรแกรมนี้เป็นเครื่องมือช่วยวิเคราะห์เท่านั้น **ไม่ใช่คำแนะนำในการลงทุน**
>
> - ผลการวิเคราะห์จาก AI เป็นเพียงข้อมูลประกอบการตัดสินใจ
> - ควรศึกษาข้อมูลและบริหารความเสี่ยงด้วยตัวเอง
> - การลงทุนในคริปโทมีความเสี่ยงสูง ลงทุนเท่าที่พร้อมจะสูญเสียได้

---

## 📝 ตัวอย่างการตั้งค่าตามสไตล์การเทรด

### Scalping (1-15 นาที)
```python
TIMEFRAME = "1m"
CANDLE_LIMIT = 200
SWING_LOOKBACK = 3
```

### Day Trading (1h-4h)
```python
TIMEFRAME = "1h"
CANDLE_LIMIT = 100
SWING_LOOKBACK = 5
```

### Swing Trading (4h-1D)
```python
TIMEFRAME = "4h"
CANDLE_LIMIT = 100
SWING_LOOKBACK = 10
```

### Position Trading (1D+)
```python
TIMEFRAME = "1d"
CANDLE_LIMIT = 100
SWING_LOOKBACK = 20
```

---

**เวอร์ชัน:** 1.3.0
**อัปเดตล่าสุด:** 2026-08-30 (v1.3 - AI Smart Trigger + Cooldown System)

---
