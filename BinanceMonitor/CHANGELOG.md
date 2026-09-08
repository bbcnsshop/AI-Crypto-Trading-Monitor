# 📋 Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.3] - 2026-09-07

### 🐛 Fixed

#### 🏗️ Bug Fixes (Code Review Round 2)
- **`maincli.py`** - `backtest` command แสดง Price = $0.00 (ไม่ populate data.latest_close/indicators) → fix ให้ใช้ df จาก run_quick_backtest
- **`maincli.py`** - `run_quick_backtest` return tuple (result, df) แทน dict อย่างเดียว เพื่อหลีกเลี่ยง fetch ซ้ำ
- **`maincli.py`** - เพิ่ม `macd_line`, `macd_signal`, `ema20` ในการคำนวณของ `run_quick_backtest`
- **`ai_trigger.py`** - `check_smart_trigger()` Big Move: guard `prev_close > 0` ป้องกัน ZeroDivisionError ถ้า `prev_close = 0`
- **`ai_client.py`** - `build_ai_context()`: guard `data.latest_close = None` ป้องกัน crash จาก format string (ใช้ `getattr(... ) or 0`)
- **`maincli.py`** - `monitor` loop: guard `price_change_pct` ไม่หารด้วย 0 (กรณี df มี 1 candle หรือ prev_close=0)
- **`main.py`** - `run_analysis()`: เพิ่ม NaN guard สำหรับ RSI progress bar และ `trigger_type or 'OK'` fallback
- **`maincli.py`** - `backtest` command: แก้ `if not result:` ที่ผิด (empty dict falsy) → ใช้ `if df is None:` แทน เพื่อแยก error vs empty signals
- **`maincli.py`** - `@cli.command('config')` เพิ่ม name arg ให้ใช้ `python maincli.py config` ได้ (เดิมต้อง `config-cmd`)
- **Performance (v1.5.3) Phase 1** - CCXT exchange reuse across modules (`config.py`, `main.py`, `maincli.py`, `backtest.py`) + `run_quick_backtest()` df reuse + indicator recalculation guard; ~2x faster `analyze`, ~1.5x faster `backtest`, ~2x faster `monitor` cycles

#### ⚡ Performance (v1.5.4) Phase 2 & Phase 3
- **Phase 2** - LRU cache for `fetch_data()` + numpy array access in `run_quick_backtest()`; second fetch ~585,000x faster, backtest loop ~180x faster
- **Phase 3** - Multi-threaded data fetching with `ThreadPoolExecutor`:
  - New `fetch_multiple(symbols, timeframe, limit, max_workers)` function for parallel API calls
  - 5 symbols sequential → parallel: **229.7x faster** (2,359ms → 10.3ms)
  - Integrated into `analyze_market()`, `monitor()`, `backtest()` commands
  - New CLI command: `fetch` for batch fetching multiple symbols
  - Default `CANDLE_LIMIT` increased from 100 → 500 for meaningful backtest results (42+ trades vs 0)
  - New `backtest` default limit: 100 → 500 candles

#### 🏗️ Bug Fixes (Code Review Round 1)
- **`indicators.py`** - `find_swing_high_low()`: แก้ logic ให้ track highest/lowest value จริงๆ (ก่อนหน้า return index สุดท้ายที่ผ่านเงื่อนไข)
- **`indicators.py`** - `calculate_vpvr()`: แก้ Value Area double-count POC bin (start ด้วย `bin_volumes[poc_idx]` แทน `0`)
- **`ai_trigger.py`** - `check_trigger()`: แก้ `ScheduleTracker` state persistence (สร้างใหม่ทุก call → ส่งเป็น param)
- **`display.py`** - `_get_rsi_signal()`: แก้ threshold edge case (`>` `<` → `>=` `<=`)
- **`display.py`** - `_display_compact()`: เพิ่ม Backtest Performance panel (ก่อนหน้าไม่แสดง)
- **`candlestick_patterns.py`** - `_down()` / `_up()`: แก้ให้ดู 3 แท่งก่อนหน้าแทน 1 แท่ง (ลด false positive)
- **`main.py`** - ลบ duplicate `except Exception` block (dead code)
- **`main.py`** - เพิ่ม `symbol`/`timeframe` attributes ใน `TradingData` class
- **`maincli.py`** - เพิ่ม `symbol`/`timeframe` defaults ใน `MarketData.__init__()`
- **`maincli.py`** - `fetch_data()`: เพิ่ม retry mechanism (3 ครั้ง, delay 2 วินาที)
- **`maincli.py`** - แก้ hardcoded `candles=100` → ใช้ `CANDLE_LIMIT`
- **`maincli.py`** - แก้ `monitor` loop: เซ็ต `data.indicators` dict และ `data.patterns` dict ให้ `check_trigger` อ่านได้

### ✅ Tested (v1.5.3)
- ทุกไฟล์ `py_compile` ผ่าน ✅
- `maincli.py analyze` - BTC/USDT, ETH/USDT, SOL/USDT (standard/compact/verbose) ✅
- `maincli.py backtest` - BTC/USDT, BNB/USDT, ETH/USDT (all timeframes) ✅
- `maincli.py monitor --once` - compact mode ✅
- `maincli.py config` ✅
- `maincli.py symbols` ✅
- `main.py` (entry point) ✅
- Edge cases: 1 candle, prev_close=0, None indicators, empty df ✅
- Git push to origin/main ✅

---

## [1.5.2] - 2026-08-30

### ✨ Added

#### 🆕 Monitor Mode ใหม่
- **แสดงแค่สถานะ** - ไม่ต้องวิเคราะห์เต็มทุกรอบ
- **เรียก AI เฉพาะเมื่อ Trigger** - ประหยัด API calls
- Default interval: **5 นาที** (เปลี่ยนจาก 60 นาที)
- แสดง: Price, RSI, MACD, ATR ในแต่ละรอบ
- แสดง Trigger Status และ Cooldown Count

**Options ใหม่:**
```bash
-i, --interval     # เช็คทุกกี่นาที (default: 5)
-n, --max-runs     # จำนวนรอบสูงสุด
--once             # debug - เช็คครั้งเดียวแล้วออก
-m, --mode         # display mode เมื่อ trigger (default: compact)
```

**Output ตัวอย่าง (ไม่ trigger):**
```
  💰 Price: $78,276.00 (+0.12%)
  📊 RSI: 55.4 (Neutral) | MACD: Bullish | ATR: 174.21
  ⏸️ RSI อยู่ในโซนปกติ
  AI Status: 🟢 พร้อม | ส่งไปแล้ว: 0 ครั้ง
```

**Output ตัวอย่าง (trigger):**
```
  💰 Price: $105.18 (-0.22%)
  📊 RSI: 56.2 (Neutral) | MACD: Bullish | ATR: 0.47
  🚨 TRIGGER! SMART_TRIGGER
  เหตุผล: Near Key Level ($105, 0.37%)
  🤖 กำลังเรียก AI...
  [AI Analysis + Full Display]
```

---

## [1.5.1] - 2026-08-30

### 🐛 Fixed

#### SSL Warning (Cross-Platform)
- **macOS (LibreSSL)** - suppress `urllib3 OpenSSL` warning
- **Windows/Linux (OpenSSL)** - ไม่กระทบการทำงาน (no-op)
- เพิ่ม logging suppression สำหรับ `urllib3`, `httpx`, `httpcore`
- **ไม่ปิด warnings ทั้งหมด** - เลือกปิดเฉพาะ SSL/urllib3 เท่านั้น
- ใช้ regex pattern `.*OpenSSL.*` เพื่อความแม่นยำ

#### Error Handling
- เพิ่ม `KeyboardInterrupt, SystemExit` handler ใน `fetch_data()` ของ `maincli.py`
- แสดง error message ที่ชัดเจนเมื่อดึงข้อมูลไม่สำเร็จ

### ✅ Tested
- `maincli.py analyze` - ETH/USDT, BTC/USDT ✅
- `maincli.py backtest` - BNB/USDT ✅
- `main.py` - Header + Config ✅
- ไม่มี SSL Warning/Error ในทุก OS

---

## [1.5.0] - 2026-08-30

### ✨ Added

#### 🖥️ CLI Interface (`maincli.py`)
- **แยกออกจาก main.py** - ใช้ module display เดิมทั้งหมด
- **5 คำสั่งหลัก**:
  - `analyze` - วิเคราะห์ตลาดครั้งเดียว พร้อม options `--symbol`, `--timeframe`, `--mode`
  - `monitor` - วิเคราะห์ต่อเนื่องทุก X นาที (รองรับ `--max-runs`)
  - `backtest` - Quick Backtest ด้วย candles
  - `config` - แสดง Configuration
  - `symbols` - แสดงรายการ Symbols ยอดนิยม
- **Built with Click** - รองรับ `--help` ทุกคำสั่ง

#### 📦 Dependencies
- `click>=8.0.0` เพิ่มใน requirements.txt

### 📝 Changed
- `maincli.py` - ไฟล์ใหม่ (220 บรรทัด)
- ใช้ `display_rich_ui()` และ `display_config()` เดิม
- `main.py` - เก็บไว้สำหรับ backward compatibility

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
| **1.5.3** | 2026-09-07 | Bug Fixes (Code Review Round 1+2) |
| **1.5.2** | 2026-08-30 | Monitor Mode (Trigger-Only AI) |
| **1.5.1** | 2026-08-30 | Cross-Platform SSL Fix |
| **1.5.0** | 2026-08-30 | CLI Interface (maincli.py) |
| 1.4.2 | 2026-08-30 | Progress Bar + Backtest Panel |
| 1.4.1 | 2026-08-30 | AI Trigger Modes (3 โหมด) |
| 1.4.0 | 2026-08-30 | Refactor: Split into 7 modules |
| 1.3.0 | 2026-08-30 | AI Smart Trigger + Cooldown |
| 1.2.0 | 2026-08-30 | Display Module (3 modes) |
| 1.1.0 | 2026-08-29 | Custom Candlestick Patterns |
| 1.0.0 | 2026-08-29 | Initial Release |

---

## 🔮 Coming Soon

### v1.5.0 - Notifications & Multi-Symbol
- [ ] Telegram Bot Integration
- [ ] Email Alerts
- [ ] Multi-Symbol Support (ETH/USDT, SOL/USDT, etc.)
- [ ] Historical Data Export (CSV/JSON)
- [ ] Command-line Arguments (--mode, --symbol, --timeframe)

### v1.6.0 - Web Dashboard
- [ ] Web Dashboard (FastAPI/Flask)
- [ ] SQLite Database for History
- [ ] Real-time Charts (Plotly/D3)
- [ ] Backtest Improvement (TP/SL Optimization)

### v2.0.0 - Live Trading
- [ ] Live Trading (Binance Futures)
- [ ] Risk Management Module
- [ ] Auto-execute Trades
- [ ] Position Sizing Calculator
