"""
Configuration Module for AI Crypto Trading Monitor
================================================
รวมตัวแปร config ทั้งหมดไว้ที่นี่ เวลาแก้ไข/เพิ่ม/ลบ config จะได้ไม่กระทบ main.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# Version
# ============================================================
VERSION = "1.4.0"  # ต้องตรงกับ CHANGELOG.md

# ============================================================
# Test Mode
# ============================================================
TEST_MODE = True  # True = รัน 1 รอบ, False = รันตามเวลา

# ============================================================
# Trading Configuration
# ============================================================
SYMBOL = "BTC/USDT"
TIMEFRAME = "1h"
CANDLE_LIMIT = 100
SWING_LOOKBACK = 5
VPVR_BINS = 50
VALUE_AREA_PCT = 0.70

# ============================================================
# Display Configuration
# ============================================================
# Display mode: 'standard' | 'compact' | 'verbose'
DISPLAY_MODE = "standard"

# ============================================================
# API Configuration
# ============================================================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ============================================================
# AI Trigger Mode
# ============================================================
# เลือกโหมดการส่ง AI:
# - 'smart'     : ส่งเมื่อมี trigger จาก indicators (RSI, Pattern, MACD, etc.)
# - 'schedule'  : ส่งตามเวลาที่กำหนด (ทุก X นาที)
# - 'manual'    : กด A เพื่อส่ง AI เอง
AI_TRIGGER_MODE = "smart"

# ============================================================
# Smart Trigger Settings (ใช้เมื่อ AI_TRIGGER_MODE = 'smart')
# ============================================================
TRIGGER_RSI_EXTREME = True        # RSI < 30 หรือ > 70
TRIGGER_PATTERN = True             # มี Bullish/Bearish pattern
TRIGGER_MACD_CROSS = True          # MACD ตัด Signal line
TRIGGER_NEAR_LEVEL = True          # ใกล้ Fib/VPVR ±0.5%
TRIGGER_HIGH_VOLATILITY = True     # ATR > 1.5% ของราคา
TRIGGER_BIG_MOVE = False           # ราคาเปลี่ยน > 1%

# ============================================================
# Schedule Settings (ใช้เมื่อ AI_TRIGGER_MODE = 'schedule')
# ============================================================
SCHEDULE_INTERVAL_MINUTES = 60     # ส่งทุก 60 นาที
SCHEDULE_MAX_PER_DAY = 24          # ส่งได้สูงสุด 24 ครั้ง/วัน

# ============================================================
# Cooldown (ใช้ทุกโหมด)
# ============================================================
AI_COOLDOWN_MAX_PER_HOUR = 3       # ส่งได้สูงสุด 3 ครั้ง/ชั่วโมง
AI_COOLDOWN_SECONDS = 300          # ห่างกันอย่างน้อย 5 นาที (300s)

# Manual Trigger (ใช้เมื่อ AI_TRIGGER_MODE = 'manual')
ENABLE_MANUAL_TRIGGER = True       # เปิดให้กดคีย์เพื่อส่ง AI เอง
MANUAL_KEY_ANALYZE = 'a'           # กด A เพื่อส่ง AI ทันที
MANUAL_KEY_QUIT = 'q'              # กด Q เพื่อออก

# Trigger Thresholds
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
ATR_HIGH_PCT = 1.5                 # ATR > 1.5% ของราคา
LEVEL_DISTANCE_PCT = 0.5           # ใกล้ support/resistance ±0.5%
BIG_MOVE_PCT = 1.0                 # ราคาเปลี่ยน > 1%

# ============================================================
# Logging Configuration
# ============================================================
LOG_DIR = "logs"
LOG_FILE = f"{LOG_DIR}/trading_monitor.log"
LOG_MAX_BYTES = 1 * 1024 * 1024   # 1 MB
LOG_BACKUP_COUNT = 3               # 3 backup files

# ============================================================
# Candlestick Pattern Constants (ถ้าต้องการปรับ)
# ============================================================
DOJI_BODY = 0.1
PIN_RATIO = 2.0
HAMMER_WICK = 0.5
HAMMER_POS = 0.6
SHOOT_POS = 0.4
