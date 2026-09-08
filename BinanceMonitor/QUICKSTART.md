# 🚀 Quick Start — AI Crypto Trading Monitor

## TL;DR (3 Commands)

```bash
# 1. ติดตั้ง
git clone https://github.com/bbcnsshop/AI-Crypto-Trading-Monitor.git
cd AI-Crypto-Trading-Monitor
pip install -r requirements.txt

# 2. ตั้งค่า API Key
cp .env.example .env
# แก้ .env → ใส่ OPENROUTER_API_KEY=https://openrouter.ai/api/v1?api_key=YOUR_KEY

# 3. รัน
python3 maincli.py analyze -s BTC/USDT -t 1h
```

## 🚀 Performance Notes (v1.5.3)

- Analyze: ~2-3 วินาที (ด้วย shared CCXT exchange + df reuse)
- Backtest 1000 candles: ~1.5-2 วินาที
- Monitor mode: ทุกๆ 5 นาทีใช้เวลา ~8-10 วินาที
- ลดการสร้าง Exchange object ซ้ำ (config.py, main.py, maincli.py, backtest.py)

## 📊 Quick Commands

### Analyze (วิเคราะห์ครั้งเดียว)
```bash
python3 maincli.py analyze -s BTC/USDT -t 1h
python3 maincli.py analyze -s ETH/USDT -t 4h -m compact   # compact mode
python3 maincli.py analyze -s SOL/USDT -t 5m -m verbose   # verbose (มีคำอธิบาย indicators)
```

### Monitor (วิเคราะห์ต่อเนื่อง)
```bash
python3 maincli.py monitor -s BTC/USDT -t 1h -i 5        # ทุก 5 นาที
python3 maincli.py monitor -s BTC/USDT -t 1h -i 5 --once  # ครั้งเดียว
python3 maincli.py monitor -s ETH/USDT -t 5m -i 1 -m compact
```

### Backtest (ทดสอบกลยุทธ์)
```bash
python3 maincli.py backtest -s BTC/USDT -t 1h -l 500     # 500 candles
python3 maincli.py backtest -s ETH/USDT -t 4h -l 1000
```

### Config & Info
```bash
python3 maincli.py config        # ดู settings
python3 maincli.py symbols       # ดู symbols ที่รองรับ
python3 maincli.py --help        # help ทั้งหมด
```

---

## ⚙️ Configuration

### Trigger Modes
```bash
# SMART (แนะนำ) — AI ทำงานเมื่อ RSI/MACD/Pattern trigger
python3 maincli.py analyze -s BTC/USDT -t 1h -m smart

# SCHEDULE — AI ทำงานทุก interval
python3 maincli.py monitor -s BTC/USDT -t 1h -m schedule

# MANUAL — AI ทำงานเมื่อกด enter
python3 maincli.py monitor -s BTC/USDT -t 1h -m manual
```

### Display Modes
| Mode | Description |
|------|-------------|
| `standard` | Full display (default) |
| `compact` | Compact (เหมาะ terminal เล็ก) |
| `verbose` | มีคำอธิบาย indicators |

---

## 🔧 Troubleshooting

### "Module not found"
```bash
pip install -r requirements.txt
```

### "OPENROUTER_API_KEY"
```bash
# ตรวจสอบว่าใส่ key ใน .env แล้ว
cat .env | grep OPENROUTER
```

### SSL Error (macOS)
```bash
# แก้ SSL ใน config.py
# TEST_MODE = True  # ปิด SSL verify ชั่วคราว
```

---

## 📁 Files

| ไฟล์ | คำอธิบาย |
|------|-----------|
| `maincli.py` | CLI Interface (แนะนำ) |
| `main.py` | Full Version |
| `config.py` | Configuration |
| `BUG_FIXES.md` | Bug Fixes Report |
| `CHANGELOG.md` | Change Log |

---

## 📈 Indicators ที่ใช้

- **RSI (14)** — Overbought/Oversold
- **MACD** — Trend Direction
- **ATR (14)** — Volatility
- **EMA 20** — Moving Average
- **Fibonacci** — Support/Resistance
- **VPVR** — Volume Profile

## 🕯️ Candlestick Patterns

| Bullish | Bearish | Neutral |
|---------|---------|---------|
| Hammer | Shooting Star | Doji |
| Bullish Engulfing | Bearish Engulfing | Spinning Top |
| Morning Star | Evening Star | — |

---

**Version:** 1.5.3 | **Last Updated:** 2026-09-07
