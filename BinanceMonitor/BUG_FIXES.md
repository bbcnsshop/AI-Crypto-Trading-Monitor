# 🐛 Bug Fixes Report (v1.5.3)

## Overview
**Version:** 1.5.3  
**Total Bugs Fixed:** 11  
**Performance Optimizations:** 1 (Phase 1)  
**Date:** 2026-09-07  
**Scope:** Bug #14–#24 (Code Review Rounds 1–3) + Performance Phase 1

---

## ⚡ Performance Optimization — Phase 1

| # | File | Change | Impact |
|---|------|--------|--------|
| P1 | `config.py` | Add `get_exchange()` shared CCXT instance | Eliminates exchange object recreation on every fetch |
| P2 | `maincli.py` | `run_quick_backtest()` accepts `df=None` parameter | Eliminates duplicate fetch in `analyze_market()` |
| P3 | `maincli.py` | Skip indicator recalculation if columns already present | Eliminates duplicate indicator computation |
| P4 | `maincli.py` | `fetch_data()` uses shared exchange instance | Reuses connection across calls |
| P5 | `main.py` | Uses `get_exchange()` instead of `ccxt.binance()` | Reduces object creation overhead |
| P6 | `backtest.py` | Uses `get_exchange()` for shared instance | Reuses connection in backtest module |

**Speedup:** ~2x on `analyze`, ~1.5x on `backtest`, ~2x on `monitor` cycles  
**Commit:** `baf2cbb`

---

## Bug #14 — Monitor Loop Missing `data.patterns` Dict
**File:** `maincli.py`  
**Symptom:** Smart Trigger ใน monitor loop ไม่ทำงานเพราะ `data.patterns` ไม่ได้ถูก set  
**Fix:** เพิ่ม `data.patterns = patterns` ใน monitor loop  
**Commit:** `221c330`

---

## Bug #15 — Backtest Command Price = $0.00
**File:** `maincli.py`  
**Symptom:** คำสั่ง `backtest` แสดง Price เป็น $0.00 เพราะ `data.latest_close` ไม่ได้ถูก populate  
**Fix:** ใช้ `df['close'].iloc[-1]` จาก `run_quick_backtest` return  
**Commit:** `878429a`

---

## Bug #16 — `run_quick_backtest` Missing MACD/EMA20
**File:** `maincli.py`  
**Symptom:** Backtest display ขาด MACD, EMA20 columns  
**Fix:** เพิ่ม `macd_line`, `macd_signal`, `ema20` ใน result dict  
**Commit:** `878429a`

---

## Bug #17 — `run_quick_backtest` Return Type Mismatch
**File:** `maincli.py`  
**Symptom:** ฟังก์ชัน return dict แต่ caller คาดหวัง tuple `(result, df)` → fetch ซ้ำ  
**Fix:** เปลี่ยน return เป็น tuple `(result, df)`  
**Commit:** `878429a`

---

## Bug #18 — Big Move ZeroDivisionError
**File:** `ai_trigger.py` line ~128  
**Symptom:** `price_change_pct = (close - prev_close) / prev_close * 100` → crash ถ้า `prev_close = 0`  
**Fix:** เพิ่ม guard `if prev_close > 0`  
**Commit:** `bb9042e`

---

## Bug #19 — `build_ai_context` Crash on `latest_close=None`
**File:** `ai_client.py` line ~119  
**Symptom:** Crash เมื่อ `data.latest_close = None` ใน format string  
**Fix:** ใช้ `getattr(data, 'latest_close', None) or 0`  
**Commit:** `f683f5e`

---

## Bug #20 — Monitor `price_change_pct` Division by Zero
**File:** `maincli.py`  
**Symptom:** Monitor loop crash ถ้า `prev_close = 0` หรือ `df` มี 1 candle  
**Fix:** เพิ่ม `if len(df) >= 2 and prev_close > 0` guard  
**Commit:** `70b8342`

---

## Bug #21 — Backtest `price_change_pct` Division by Zero
**File:** `maincli.py`  
**Symptom:** Backtest crash ถ้า `prev_close = 0` หรือ `df` มี 1 candle  
**Fix:** เพิ่ม `if len(df) >= 2 and prev_close > 0` guard  
**Commit:** `70b8342`

---

## Bug #22 — RSI NaN + VPVR N/A + Trigger Type Fallback
**File:** `main.py`  
**Symptom:**  
1. RSI progress bar crash เมื่อ RSI = NaN  
2. VPVR แสดง "POC: N/A" แม้มี POC  
3. `trigger_type` ไม่มี fallback  
**Fix:**  
1. ใช้ `if rsi != rsi` (NaN check) แทน `or 0`  
2. แก้ condition `if poc_bin is not None`  
3. เพิ่ม `trigger_type or 'OK'` fallback  
**Commit:** `ccaca4f`

---

## Bug #23 — Backtest `if not result:` Falsy Dict Bug
**File:** `maincli.py`  
**Symptom:** Empty dict `{}` เป็น falsy → เข้า error branch ผิด (result คือ empty signals ไม่ใช่ error)  
**Fix:** เปลี่ยนเป็น `if df is None:` เพื่อตรวจจับ error จริง  
**Commit:** `ddaa287`

---

## Bug #24 — Config Command Named `config-cmd`
**File:** `maincli.py` line ~371  
**Symptom:** `@cli.command()` derive name จาก function → `config_cmd` → `config-cmd`  
**Fix:** ใช้ `@cli.command('config')` explicit name  
**Commit:** `d59ff6e`

---

## Additional Fixes (Pre-Bug #14)
(จาก Round 1 — ไม่ได้นับใน Bug #14–#24)

| File | Issue |
|------|-------|
| `indicators.py` | `find_swing_high_low()` logic fix (track highest/lowest value จริงๆ) |
| `indicators.py` | `calculate_vpvr()` double-count POC bin fix |
| `ai_trigger.py` | `ScheduleTracker` state persistence fix |
| `display.py` | `_get_rsi_signal()` threshold edge case (`>` `<` → `>=` `<=`) |
| `display.py` | `_display_compact()` missing Backtest Performance panel |
| `candlestick_patterns.py` | `_down()` / `_up()` ใช้ 3 candles แทน 1 candle |
| `main.py` | ลบ duplicate `except Exception` block (dead code) |
| `main.py` | เพิ่ม `symbol`/`timeframe` attributes ใน `TradingData` class |
| `maincli.py` | เพิ่ม `symbol`/`timeframe` defaults ใน `MarketData.__init__()` |
| `maincli.py` | `fetch_data()`: retry mechanism (3 ครั้ง, delay 2 วินาที) |
| `maincli.py` | แก้ hardcoded `candles=100` → ใช้ `CANDLE_LIMIT` |

---

## Testing Matrix

| Command | Symbol | Timeframe | Mode | Status |
|---------|--------|-----------|------|--------|
| `analyze` | BTC/USDT | 1h | standard | ✅ |
| `analyze` | ETH/USDT | 4h | standard | ✅ |
| `analyze` | SOL/USDT | 1h | compact | ✅ |
| `analyze` | BTC/USDT | 1h | verbose | ✅ |
| `backtest` | ETH/USDT | 1h | — | ✅ |
| `backtest` | BTC/USDT | 1h | — | ✅ |
| `backtest` | BNB/USDT | 5m | — | ✅ |
| `monitor --once` | BTC/USDT | 5m | compact | ✅ |
| `config` | — | — | — | ✅ |
| `symbols` | — | — | — | ✅ |

## Edge Cases Tested

| Scenario | Before Fix | After Fix |
|----------|-----------|-----------|
| `prev_close = 0` | ZeroDivisionError | Guarded ✅ |
| 1 candle df | price_change_pct crash | Guarded ✅ |
| RSI = NaN | Progress bar crash | NaN check ✅ |
| Empty signals `{}` | Wrong error path | `df is None` check ✅ |
| `latest_close = None` | Format string crash | `getattr or 0` ✅ |
| VPVR with no POC | "POC: N/A" shown | Fixed condition ✅ |
| Trigger with no patterns | Patterns not set | Fixed ✅ |
