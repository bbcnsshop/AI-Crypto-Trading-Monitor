# 📋 Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.4.0] - 2026-08-30

### ♻️ Refactored (Code Modularization)

#### 🏗️ Module Structure
แยก `main.py` (750+ บรรทัด) ออกเป็น 7 modules เพื่อให้ง่ายต่อการดูแลและแก้ไข

| Module | บรรทัด | หน้าที่ |
|--------|--------|--------|
| `main.py` | 232 | Entry point + main loop (ลดลง ~70%) |
| `config.py` | ~100 | Configuration ทั้งหมด |
| `indicators.py` | ~170 | RSI, MACD, ATR, EMA, Fibonacci, VPVR |
| `ai_trigger.py` | ~160 | Smart Trigger + Cooldown System |
| `ai_client.py` | ~100 | AI Context + OpenRouter API |
| `display.py` | ~440 | Rich UI (3 modes) |
| `candlestick_patterns.py` | ~170 | 11 Candlestick Patterns |

#### ✅ Benefits
- **Maintainability** - แก้ไขแต่ละส่วนแยกกันชัดเจน
- **Testability** - ทดสอบแต่ละ module ได้
- **Readability** - อ่านง่ายขึ้น แต่ละไฟล์ไม่เกิน 500 บรรทัด
- **Reusability** - นำ module ไปใช้ซ้ำได้ง่าย

#### 🆕 New Files
- `config.py` - แยก config ออกจาก main
- `indicators.py` - แยกฟังก์ชัน indicators
- `ai_trigger.py` - แยก logic Smart Trigger + Cooldown
- `ai_client.py` - แยก AI Context + API calls
- `CHANGELOG.md` - บันทึกการเปลี่ยนแปลง

### 📝 Changed
- `main.py` - ลดขนาดจาก 750+ → 232 บรรทัด (ลดลง ~70%)
- เพิ่ม `TradingData` class เก็บข้อมูลการวิเคราะห์
- เพิ่ม `run_analysis()` function แยก business logic
- `config.py` - รวม config ทั้งหมดไว้ที่เดียว

### 📚 Documentation
- อัปเดต `README.md` เรียงลำดับ 11 sections
- เพิ่มตารางสรุป modules และหน้าที่
- เพิ่มคำอธิบาย AI Trigger System, Display Modes, Logging

---

## [1.3.0] - 2026-08-30

### ✨ Added (AI Smart Trigger System)

#### 🤖 Smart Triggers
- **RSI Extreme** - Trigger เมื่อ RSI < 30 (Oversold) หรือ > 70 (Overbought)
- **Pattern Detected** - Trigger เมื่อมี Bullish/Bearish candlestick pattern
- **MACD Crossover** - Trigger เมื่อ MACD line ตัด Signal line (bullish/bearish)
- **Near Key Level** - Trigger เมื่อราคาใกล้ Fibonacci/VPVR ±0.5%
- **High Volatility** - Trigger เมื่อ ATR > 1.5% ของราคา
- **Big Move** - Trigger เมื่อราคาเปลี่ยน > 1% (conservative, OFF by default)

#### ⏱️ Cooldown System
- **Max 3 calls/hour** - จำกัดจำนวนครั้งที่ส่ง AI ได้
- **Min 5 min gap** - ห่างกันอย่างน้อย 5 นาทีระหว่างการส่งแต่ละครั้ง
- **Auto reset** - reset counter ทุก 1 ชั่วโมง
- **Manual override ready** - hooks สำหรับ manual trigger (กด 'A' เพื่อส่ง AI ทันที)

#### 📊 Status Display
- แสดง Trigger Info ตอน startup
- แสดง Trigger Type (SMART_TRIGGER / COOLDOWN / NONE) ทุกครั้ง
- แสดงจำนวนครั้งที่ใช้ไป/ชั่วโมง

### 📝 Changed
- STEP 6 เปลี่ยนเป็น "Smart STEP 6" - ตรวจสอบ trigger ก่อนส่ง AI
- ถ้าไม่มี trigger หรือโดน cooldown จะแสดง `[AI Skipped: reason]` แทน
- เพิ่ม logging สำหรับ trigger decisions

### ⚙️ Configuration
```python
# Smart Triggers (เปิด/ปิดแต่ละตัว)
TRIGGER_RSI_EXTREME = True
TRIGGER_PATTERN = True
TRIGGER_MACD_CROSS = True
TRIGGER_NEAR_LEVEL = True
TRIGGER_HIGH_VOLATILITY = True
TRIGGER_BIG_MOVE = False  # conservative

# Cooldown
AI_COOLDOWN_MAX_PER_HOUR = 3
AI_COOLDOWN_SECONDS = 300

# Manual Trigger (พร้อมใช้)
ENABLE_MANUAL_TRIGGER = True
MANUAL_KEY_ANALYZE = 'a'
MANUAL_KEY_QUIT = 'q'
```

---

## [1.2.0] - 2026-08-30

### ✨ Added (Display Module)

#### 🎨 Display Modes (3 โหมด)
- **Standard Mode** (default) - แบบเดิม ไม่มีคำอธิบาย
- **Compact Mode** - แบบย่อ เห็นภาพรวมเร็วๆ
- **Verbose Mode** - แบบเต็ม มีคำอธิบายความหมายใต้ทุกตัวเลข

#### 📚 Knowledge Base (INDICATOR_DEFINITIONS)
- **RSI** - คำอธิบายช่วง 0-30 (Oversold) / 30-70 (Neutral) / 70-100 (Overbought)
- **MACD** - คำอธิบาย Bullish/Bearish Momentum + Crossover
- **ATR** - คำอธิบายการใช้กับ SL/TP
- **EMA** - คำอธิบาย Uptrend/Downtrend/Sideways
- **Fibonacci** - คำอธิบาย 0.382/0.500/0.618 (Golden Ratio)
- **VPVR** - คำอธิบาย POC/VAH/VAL
- **Patterns** - คำอธิบาย 11 แบบ พร้อมความหมายภาษาไทย

#### 🆕 New File
- `display.py` (440 บรรทัด) - แยกออกมาเป็น module แสดงผล

### 📝 Changed
- `main.py` - refactor ใช้ `display_rich_ui_new` จาก display.py
- เพิ่ม config `DISPLAY_MODE = "standard"` (standard | compact | verbose)

---

## [1.1.0] - 2026-08-29

### ✨ Added
- **Custom Candlestick Patterns Library** - ตรวจจับ 11 แบบ
  - Bullish Engulfing, Bearish Engulfing
  - Bullish Pin Bar, Bearish Pin Bar
  - Doji, Hammer, Inverted Hammer
  - Shooting Star, Hanging Man
  - Piercing Line, Dark Cloud Cover

### 📝 Changed
- เปลี่ยนจาก `pandas_ta` เป็น `ta` library
- เพิ่ม geometric detection สำหรับ candlestick patterns

### 🔧 Constants
```python
DOJI_BODY = 0.1
PIN_RATIO = 2.0
HAMMER_WICK = 0.5
HAMMER_POS = 0.6
SHOOT_POS = 0.4
```

---

## [1.0.0] - 2026-08-29

### ✨ Initial Release

#### 📊 Features
- ดึงข้อมูลจาก Binance API (BTC/USDT)
- คำนวณ Indicators: RSI, MACD, ATR, EMA
- ตรวจจับ Candlestick Patterns
- คำนวณ Fibonacci Retracement
- คำนวณ Volume Profile (VPVR)
- ส่งข้อมูลให้ OpenRouter AI (DeepSeek) วิเคราะห์
- 3-Tier Entry Plan พร้อม TP/SL
- Rich UI แสดงผลบน Terminal

#### 🔧 Configuration
- `.env` สำหรับ API Keys
- `main.py` config สำหรับ Symbol/Timeframe
- Logging system (File: ERROR only, Console: INFO+)

#### 📁 Files
- `main.py` - Main process
- `requirements.txt` - Dependencies
- `README.md` - Documentation
- `.env.example` - API key template
- `.gitignore` - Git ignore rules

---

## 📊 Version Summary

| Version | Date | Highlight |
|---------|------|-----------|
| **1.4.0** | 2026-08-30 | Refactor: Split into 7 modules (~70% code reduction) |
| 1.3.0 | 2026-08-30 | AI Smart Trigger + Cooldown |
| 1.2.0 | 2026-08-30 | Display Module (3 modes) + Thai Definitions |
| 1.1.0 | 2026-08-29 | Custom Candlestick Patterns Library |
| 1.0.0 | 2026-08-29 | Initial Release |

---

## 🔮 Roadmap (Upcoming)

### v1.5.0 (TBD)
- [ ] Manual Trigger ครบ (Keyboard listener thread)
- [ ] Web UI Dashboard
- [ ] Telegram Notification เมื่อ trigger
- [ ] Multi-Symbol Support (เฝ้าหลายคู่เทรดพร้อมกัน)

### v1.5.0 (TBD)
- [ ] Backtest UI (เลือก parameters แล้วรัน backtest)
- [ ] Strategy Optimization (RSI, TP/SL, ATR multipliers)
- [ ] Performance Metrics Dashboard
- [ ] Database Storage (เก็บ trades/logs)

### v2.0.0 (TBD)
- [ ] Live Trading (Binance Futures Testnet)
- [ ] Risk Management Module
- [ ] Portfolio Management
- [ ] Auto-execute trades

---

## 📝 Migration Guide

### จาก v1.2 → v1.3
ไม่ต้องแก้ไขอะไร - แค่ `pip install -r requirements.txt` (ถ้ามี lib ใหม่) แล้วรันได้เลย

### จาก v1.1 → v1.2
ไม่ต้องแก้ไขอะไร - `display.py` ถูกเพิ่มเป็น dependency ใหม่

### จาก v1.0 → v1.1
เปลี่ยนจาก `pandas_ta` เป็น `ta` library ใน requirements.txt
```bash
pip uninstall pandas_ta
pip install ta
```

---

**หมายเหตุ:** ทุก version จะถูก tag บน GitHub ด้วย เช่น `v1.3.0`
