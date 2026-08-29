# 📋 Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.4.2] - 2026-08-30

### ✨ Added

#### 📊 Progress Bar (7 Steps)
- แสดงความคืบหน้าขณะวิเคราะห์ด้วย Rich Progress Bar
- แต่ละ step มี icon และรายละเอียด:

| Step | Icon | รายละเอียด |
|------|------|------------|
| 1. ดึงข้อมูล | 📥 | ราคาปัจจุบัน + จำนวน candles |
| 2. Indicators | 📊 | RSI, MACD values |
| 3. Patterns | 🔍 | Bullish/Bearish count |
| 4. Fibonacci | 📐 | Fib 61.8% price |
| 5. Volume Profile | 📈 | POC price |
| 6. AI Trigger | 🤖 | Trigger type หรือ skipped |
| 7. แสดงผล | 🎨 | Done! |

#### 📊 Backtest Performance Panel
- แสดงใน **standard** และ **verbose** mode
- แสดง: Winrate, Total Trades, Profit Factor, Total P&L
- แสดง Long/Short winrate breakdown
- Verdict: ✅ GOOD / ⚠️ MARGINAL / ❌ POOR

### 🐛 Fixed

#### Backtest Panel ไม่แสดง
- **สาเหตุ 1:** `run_quick_backtest()` ไม่ได้แปลง `df['timestamp']` เป็น datetime
  - เพิ่ม `df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')`
- **สาเหตุ 2:** `_display_standard()` ไม่มีโค้ดเรียก `_display_backtest_summary()`
  - เพิ่ม Backtest Performance block ใน `_display_standard()`
- **สาเหตุ 3:** `return None` เมื่อไม่มี signals
  - เปลี่ยนเป็น `return {empty dict}` แทน

#### Header ซ้ำซ้อน
- ลบ Panel header ซ้ำใน `_display_standard()`, `_display_compact()`, `_display_verbose()`
- ใช้ subtitle แทน: `BTC/USDT 1h` หรือ `BTC/USDT 1h | COMPACT`

### 📝 Changed
- `display.py` - เพิ่ม Backtest Panel ใน `_display_standard()` + ลบ header ซ้ำ
- `main.py` - ใช้ `with Progress()` context แทน console.print แต่ละ step
- `config.py` - VERSION = "1.4.2"

---

## [1.4.1] - 2026-08-30

### ✨ Added

#### 🎯 AI Trigger Modes (3 โหมด)
- **SMART Mode** - ส่ง AI เฉพาะเมื่อ indicators ตรงเงื่อนไข
- **SCHEDULE Mode** - ส่ง AI ทุก X นาที
- **MANUAL Mode** - กด A เพื่อส่ง AI เอง

#### 📅 ScheduleTracker Class
- ติดตาม `last_send_time`, `send_today_count`
- Auto reset counter เมื่อข้ามวัน

#### ⚙️ Config Table Display
- แสดง config เป็น Rich Table ตอน startup

### 🐛 Fixed
- ZeroDivisionError ใน `_get_ema_signal()`
- ATR% ZeroDivisionError
- Table 3 แสดง 11 candlestick patterns ครบ

---

## [1.4.0] - 2026-08-30

### ♻️ Refactored (Code Modularization)

#### 🏗️ Module Structure
แยก `main.py` (750+ บรรทัด) ออกเป็น 7 modules

| Module | หน้าที่ |
|--------|--------|
| `main.py` | Entry point + main loop |
| `config.py` | Configuration ทั้งหมด |
| `indicators.py` | RSI, MACD, ATR, EMA, Fibonacci, VPVR |
| `ai_trigger.py` | Smart Trigger + Cooldown System |
| `ai_client.py` | AI Context + OpenRouter API |
| `display.py` | Rich UI (3 modes) |
| `candlestick_patterns.py` | 11 Candlestick Patterns |

---

## [1.3.0] - 2026-08-30

### ✨ Added
- AI Smart Trigger System (6 triggers)
- Cooldown System (3 ครั้ง/ชม, ห่างกัน 5 นาที)
- 3-Tier Entry Plan

---

## [1.2.0] - 2026-08-30

### ✨ Added
- Display Module 3 โหมด (standard, compact, verbose)
- Thai Knowledge Base

---

## [1.1.0] - 2026-08-29

### ✨ Added
- Custom Candlestick Patterns Library (11 แบบ)

---

## [1.0.0] - 2026-08-29

### ✨ Initial Release
- ดึงข้อมูลจาก Binance
- Indicators: RSI, MACD, ATR, EMA
- Fibonacci + VPVR
- OpenRouter AI วิเคราะห์

---

## 📊 Version Summary

| Version | Date | Highlight |
|---------|------|-----------|
| **1.4.2** | 2026-08-30 | Progress Bar + Backtest Panel |
| 1.4.1 | 2026-08-30 | AI Trigger Modes (3 โหมด) |
| 1.4.0 | 2026-08-30 | Refactor: Split into 7 modules |
| 1.3.0 | 2026-08-30 | AI Smart Trigger + Cooldown |
| 1.2.0 | 2026-08-30 | Display Module (3 modes) |
| 1.1.0 | 2026-08-29 | Custom Candlestick Patterns |
| 1.0.0 | 2026-08-29 | Initial Release |

---

## 🔮 Roadmap

### v1.5.0 (TBD)
- [ ] Manual Trigger ครบ
- [ ] Web UI Dashboard
- [ ] Telegram Notification
- [ ] Multi-Symbol Support

### v2.0.0 (TBD)
- [ ] Live Trading (Binance Futures)
- [ ] Risk Management Module
- [ ] Auto-execute trades
