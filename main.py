"""
AI Crypto Trading Monitor
========================
บอทสแกนกราฟคริปโท (BTC/USDT) ดึงข้อมูลจาก Binance ผ่าน ccxt
คำนวณ Indicators (RSI, MACD, ATR, EMA) ด้วย ta library
ตรวจจับ Candlestick Patterns (Engulfing, Pin Bar, Doji, Hammer, Shooting Star,
Piercing Line, Dark Cloud Cover) ด้วย custom library
Fibonacci Retracement/Extension, VPVR (Volume Profile)
แล้วส่งข้อมูลให้ AI ผ่าน OpenRouter เพื่อวิเคราะห์จุดเข้า 3 ระดับ (3-Tier Entry)
พร้อม TP/SL และแสดงผลบน Terminal ด้วย Rich UI
"""

import os
import sys
import time
import traceback
from datetime import datetime
from typing import Dict, Optional, Tuple, Any

import numpy as np
import pandas as pd
from candlestick_patterns import detect_candlestick_patterns
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import AverageTrueRange

import ccxt
from openai import OpenAI
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import logging
from logging.handlers import RotatingFileHandler
from rich import box
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# ============================================================
# โหมดทดสอบ (Test Mode)
# ============================================================
# True  = รันทันที 1 รอบ แล้วจบโปรแกรม
# False = ใช้ APScheduler ตั้งเวลาทุกต้นชั่วโมง (minute=0)
TEST_MODE = True

# ============================================================
# Configuration
# ============================================================
SYMBOL = "BTC/USDT"
TIMEFRAME = "1h"
CANDLE_LIMIT = 100
SWING_LOOKBACK = 5
VPVR_BINS = 50
VALUE_AREA_PCT = 0.70

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

console = Console()

# Logging
LOG_DIR = "logs"
LOG_FILE = f"{LOG_DIR}/trading_monitor.log"   # เก็บเฉพาะ ERROR (สำหรับ debug บนเครื่องอื่น)
LOG_MAX_BYTES = 1 * 1024 * 1024                # 1 MB (เล็ก เพราะเก็บแค่ ERROR)
LOG_BACKUP_COUNT = 3                            # เก็บ backup 3 ไฟล์

def setup_logging():
    """ตั้งค่า Logging
    - Console: แสดง INFO+ (เห็นผลเต็มๆ เวลา run)
    - File: เก็บเฉพาะ ERROR (ส่งไปเปิดเครื่องอื่น debug ได้, ไม่บวม)
    - Rotation: 1MB × 3 backups (กันไฟล์บวม)
    """
    if not os.path.exists(LOG_DIR):
        try:
            os.makedirs(LOG_DIR)
        except Exception:
            pass
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    file_fmt = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    console_fmt = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S')
    # File Handler: เก็บเฉพาะ ERROR
    try:
        # เคลียร์ log เก่าทุกครั้งที่ start ใหม่ (กันบวม + เอาเฉพาะ error รอบล่าสุด)
        for old_file in [LOG_FILE] + [f"{LOG_FILE}.{i}" for i in range(1, LOG_BACKUP_COUNT + 1)]:
            if os.path.exists(old_file):
                try:
                    os.remove(old_file)
                except Exception:
                    pass
        fh = RotatingFileHandler(LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding='utf-8')
        fh.setLevel(logging.ERROR)  # เก็บเฉพาะ ERROR (สำหรับ debug บนเครื่องอื่น)
        fh.setFormatter(file_fmt)
        logger.addHandler(fh)
    except Exception:
        pass
    # Console Handler: แสดง INFO+ (เห็นผลเต็มๆ)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(console_fmt)
    logger.addHandler(ch)
    # ลด noise จาก library ภายนอก
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logger.info(f"Logging initialized: {LOG_FILE} (Console: INFO+ | File: ERROR only)")

setup_logging()
# Binance API Keys (Optional - for higher rate limits)
# Without keys: Public data works fine, rate limit ~50 req/min
# With keys: Higher rate limit ~1200 req/min
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")

SYSTEM_PROMPT = """คุณคือผู้เชี่ยวชาญด้านการเทรดคริปโท AI Trading Analyst

**ห้ามใช้คำทักทาย ห้ามเกริ่นนำ ตอบเป็นภาษาไทยอย่างกระชับ**

แสดงผลลัพธ์ใน 3 ส่วนชัดเจน:

---

**1) โครงสร้างราคา & VPVR Zone**
- อธิบายระดับราคาสำคัญจาก Fibonacci และ Volume Profile
- ระบุ POC, VAH, VAL ที่ชัดเจน
- วิเคราะห์ Indicators และ Candlestick Patterns ประกอบ

---

**2) แผนเทรด 3-Tier Entry (Entry, SL, TP1, TP2, R:R)**
- Entry 1 (Aggressive): ราคาปิดปัจจุบัน หรือ Fib 0.382
- Entry 2 (Moderate): Fib 0.5 หรือ EMA 20
- Entry 3 (Conservative): Fib 0.618 หรือ POC
- TP1: VAH หรือ Fib Ext 1.272
- TP2: Fib Ext 1.618
- SL: ใต้ VAL/POC/Fib 0.618 + 0.5 * ATR

---

**3) คำแนะนำการบริหารเงินทุน (Position Sizing %)**
- แสดงเปอร์เซ็นต์การลงทุนแต่ละระดับ
- Risk ไม่เกิน 1-2% ต่อไม้"""

# ============================================================
# TradingData Container
# ============================================================

class TradingData:
    """Container for all trading data and analysis results"""
    def __init__(self):
        self.df = None
        self.latest_close = 0.0
        self.indicators = {}
        self.fibonacci = {}
        self.vpvr = {}
        self.patterns = {}
        self.strategy = {}
        self.ai_analysis = ""
    def clear(self):
        self.df = None
        self.latest_close = 0.0
        self.indicators = {}
        self.fibonacci = {}
        self.vpvr = {}
        self.patterns = {}
        self.strategy = {}
        self.ai_analysis = ""


# ============================================================
# Section 1: Data & Indicators
# ============================================================

def fetch_market_data(symbol: str = SYMBOL, timeframe: str = TIMEFRAME, limit: int = CANDLE_LIMIT) -> Optional[pd.DataFrame]:
    """
    ดึงข้อมูล OHLCV จาก Binance ผ่าน ccxt
    
    รองรับ 2 โหมด:
    - ไม่มี API Key: ใช้ Public API (Rate limit ~50 req/min)
    - มี API Key: ใช้ Authenticated API (Rate limit ~1200 req/min)
    """
    try:
        if BINANCE_API_KEY and BINANCE_API_SECRET:
            # ใช้ Authenticated API (สำหรับ Higher Rate Limit)
            exchange = ccxt.binance({
                'apiKey': BINANCE_API_KEY,
                'secret': BINANCE_API_SECRET,
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'},
            })
            api_mode = "Authenticated API"
        else:
            # ใช้ Public API
            exchange = ccxt.binance({
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'},
            })
            api_mode = "Public API"
        
        console.print(f"[dim]กำลังดึงข้อมูล {symbol} Timeframe {timeframe} ({api_mode})...[/dim]")
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        console.print(f"[green]ดึงข้อมูลสำเร็จ: {len(df)} แท่ง ({api_mode})[/green]")
        return df
    except Exception as e:
        logging.error(f"เกิดข้อผิดพลาด: {e}"); logging.debug(traceback.format_exc()); console.print(f"[red]เกิดข้อผิดพลาด: {e}[/red]")
        return None


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """คำนวณ Indicators: RSI (14), MACD (12,26,9), ATR (14), EMA 20 ใช้ ta library"""
    if df is None or len(df) < 30:
        console.print("[yellow]ข้อมูลไม่เพียงพอ[/yellow]")
        return df
    try:
        # RSI (14) - ใช้ RSIIndicator จาก ta.momentum
        rsi_indicator = RSIIndicator(close=df['close'], window=14, fillna=False)
        df['rsi'] = rsi_indicator.rsi()
        
        # MACD (12, 26, 9) - ใช้ MACD จาก ta.trend
        macd_indicator = MACD(close=df['close'], window_slow=26, window_fast=12, window_sign=9, fillna=False)
        df['macd_line'] = macd_indicator.macd()
        df['macd_signal'] = macd_indicator.macd_signal()
        df['macd_hist'] = macd_indicator.macd_diff()
        
        # ATR (14) - ใช้ AverageTrueRange จาก ta.volatility
        atr_indicator = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14, fillna=False)
        df['atr'] = atr_indicator.average_true_range()
        
        # EMA 20 - ใช้ EMAIndicator จาก ta.trend
        ema_indicator = EMAIndicator(close=df['close'], window=20, fillna=False)
        df['ema20'] = ema_indicator.ema_indicator()
        
        logging.info("คำนวณ Indicators สำเร็จ (ta library)"); console.print("[green]คำนวณ Indicators สำเร็จ (ta library)[/green]")
        return df
    except Exception as e:
        console.print(f"[red]เกิดข้อผิดพลาด: {e}[/red]")
        import traceback
        traceback.print_exc()
        return df
# ============================================================
# Section 2: Fibonacci & VPVR
# ============================================================

def find_swing_high_low(df: pd.DataFrame, lookback: int = SWING_LOOKBACK) -> Tuple[float, float, int, int]:
    """หา Swing High และ Swing Low"""
    if len(df) < lookback * 2 + 1:
        return float(df['high'].max()), float(df['low'].min()), 0, 0
    highs, lows = df['high'].values, df['low'].values
    n = len(df)
    sh_val, sl_val = -np.inf, np.inf
    sh_idx, sl_idx = 0, 0
    for i in range(lookback, n - lookback):
        is_high = all(highs[j] <= highs[i] for j in range(max(0, i-lookback), min(n, i+lookback+1)) if j != i)
        is_low = all(lows[j] >= lows[i] for j in range(max(0, i-lookback), min(n, i+lookback+1)) if j != i)
        if is_high and highs[i] > sh_val:
            sh_val, sh_idx = highs[i], i
        if is_low and lows[i] < sl_val:
            sl_val, sl_idx = lows[i], i
    return float(sh_val), float(sl_val), sh_idx, sl_idx

def calculate_fibonacci_levels(swing_high: float, swing_low: float) -> Dict[str, float]:
    """คำนวณ Fibonacci Levels"""
    diff = swing_high - swing_low
    return {
        'swing_high': swing_high, 'swing_low': swing_low,
        'fib_382': swing_high - diff * 0.382, 'fib_500': swing_high - diff * 0.500,
        'fib_618': swing_high - diff * 0.618, 'fib_786': swing_high - diff * 0.786,
        'ext_1272': swing_high + diff * 1.272, 'ext_1618': swing_high + diff * 1.618,
    }

def calculate_vpvr(df: pd.DataFrame, bins: int = VPVR_BINS, value_area_pct: float = VALUE_AREA_PCT) -> Dict[str, Any]:
    """คำนวณ Volume Profile (VPVR)"""
    if len(df) < 2:
        return {}
    min_p, max_p = float(df['low'].min()), float(df['high'].max())
    if max_p == min_p:
        return {}
    price_bins = np.linspace(min_p, max_p, bins + 1)
    vol_profile = np.zeros(bins)
    for _, row in df.iterrows():
        lb = int(np.searchsorted(price_bins, row['low'], side='right') - 1)
        hb = int(np.searchsorted(price_bins, row['high'], side='right') - 1)
        lb, hb = max(0, min(lb, bins-1)), max(0, min(hb, bins-1))
        if hb == lb:
            vol_profile[lb] += row['volume']
        else:
            vp = row['volume'] / (hb - lb + 1)
            for b in range(lb, hb + 1):
                vol_profile[b] += vp
    poc_idx = np.argmax(vol_profile)
    poc = (price_bins[poc_idx] + price_bins[poc_idx + 1]) / 2
    total_vol = np.sum(vol_profile)
    target_vol = total_vol * value_area_pct
    va_vol = vol_profile[poc_idx]
    va_l, va_h = poc_idx, poc_idx
    while va_vol < target_vol and (va_l > 0 or va_h < bins - 1):
        lv = vol_profile[va_l - 1] if va_l > 0 else -1
        rv = vol_profile[va_h + 1] if va_h < bins - 1 else -1
        if lv >= rv and va_l > 0:
            va_l -= 1
            va_vol += lv
        elif va_h < bins - 1:
            va_h += 1
            va_vol += rv
        else:
            break
    return {
        'poc': poc, 'vah': (price_bins[va_h] + price_bins[va_h + 1]) / 2,
        'val': (price_bins[va_l] + price_bins[va_l + 1]) / 2,
        'total_volume': float(total_vol),
    }


# ============================================================
# Section 2: Fibonacci & VPVR
# ============================================================

def find_swing_high_low(df: pd.DataFrame, lookback: int = SWING_LOOKBACK) -> Tuple[float, float, int, int]:
    """หา Swing High และ Swing Low"""
    if len(df) < lookback * 2 + 1:
        return float(df['high'].max()), float(df['low'].min()), 0, 0
    highs, lows = df['high'].values, df['low'].values
    n = len(df)
    sh_val, sl_val = -np.inf, np.inf
    sh_idx, sl_idx = 0, 0
    for i in range(lookback, n - lookback):
        is_high = all(highs[j] <= highs[i] for j in range(max(0, i-lookback), min(n, i+lookback+1)) if j != i)
        is_low = all(lows[j] >= lows[i] for j in range(max(0, i-lookback), min(n, i+lookback+1)) if j != i)
        if is_high and highs[i] > sh_val:
            sh_val, sh_idx = highs[i], i
        if is_low and lows[i] < sl_val:
            sl_val, sl_idx = lows[i], i
    return float(sh_val), float(sl_val), sh_idx, sl_idx

def calculate_fibonacci_levels(swing_high: float, swing_low: float) -> Dict[str, float]:
    """คำนวณ Fibonacci Levels"""
    diff = swing_high - swing_low
    return {
        'swing_high': swing_high, 'swing_low': swing_low,
        'fib_382': swing_high - diff * 0.382, 'fib_500': swing_high - diff * 0.500,
        'fib_618': swing_high - diff * 0.618, 'fib_786': swing_high - diff * 0.786,
        'ext_1272': swing_high + diff * 1.272, 'ext_1618': swing_high + diff * 1.618,
    }

def calculate_vpvr(df: pd.DataFrame, bins: int = VPVR_BINS, value_area_pct: float = VALUE_AREA_PCT) -> Dict[str, Any]:
    """คำนวณ Volume Profile (VPVR)"""
    if len(df) < 2:
        return {}
    min_p, max_p = float(df['low'].min()), float(df['high'].max())
    if max_p == min_p:
        return {}
    price_bins = np.linspace(min_p, max_p, bins + 1)
    vol_profile = np.zeros(bins)
    for _, row in df.iterrows():
        lb = int(np.searchsorted(price_bins, row['low'], side='right') - 1)
        hb = int(np.searchsorted(price_bins, row['high'], side='right') - 1)
        lb, hb = max(0, min(lb, bins-1)), max(0, min(hb, bins-1))
        if hb == lb:
            vol_profile[lb] += row['volume']
        else:
            vp = row['volume'] / (hb - lb + 1)
            for b in range(lb, hb + 1):
                vol_profile[b] += vp
    poc_idx = np.argmax(vol_profile)
    poc = (price_bins[poc_idx] + price_bins[poc_idx + 1]) / 2
    total_vol = np.sum(vol_profile)
    target_vol = total_vol * value_area_pct
    va_vol = vol_profile[poc_idx]
    va_l, va_h = poc_idx, poc_idx
    while va_vol < target_vol and (va_l > 0 or va_h < bins - 1):
        lv = vol_profile[va_l - 1] if va_l > 0 else -1
        rv = vol_profile[va_h + 1] if va_h < bins - 1 else -1
        if lv >= rv and va_l > 0:
            va_l -= 1
            va_vol += lv
        elif va_h < bins - 1:
            va_h += 1
            va_vol += rv
        else:
            break
    return {
        'poc': poc, 'vah': (price_bins[va_h] + price_bins[va_h + 1]) / 2,
        'val': (price_bins[va_l] + price_bins[va_l + 1]) / 2,
        'total_volume': float(total_vol),
    }


# ============================================================
# Section 3: AI Integration
# ============================================================

def build_ai_context(data: TradingData) -> str:
    """สร้าง Context ข้อมูลทั้งหมดสำหรับส่งให้ AI"""
    ctx = []
    ctx.append(f"SYMBOL: {SYMBOL}")
    ctx.append(f"TIMEFRAME: {TIMEFRAME}")
    ctx.append(f"CURRENT PRICE: {data.latest_close:.2f}")
    ctx.append("")
    
    if data.indicators:
        ctx.append("=== TECHNICAL INDICATORS ===")
        for k, v in data.indicators.items():
            if v is not None and not pd.isna(v):
                ctx.append(f"{k.upper()}: {v:.4f}")
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
    """เรียก OpenRouter API"""
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


# ============================================================


# ============================================================
# Main Process
# ============================================================

def run_analysis():
    """รันกระบวนการวิเคราะห์ทั้งหมด"""
    data = TradingData()
    try:
        logging.info("="*60); logging.info("STEP 1: ดึงข้อมูลตลาด"); console.print("[bold]Step 1:[/bold] ดึงข้อมูลตลาด...")
        df = fetch_market_data(SYMBOL, TIMEFRAME, CANDLE_LIMIT)
        if df is None or df.empty:
            console.print("[red]ไม่สามารถดึงข้อมูลได้[/red]")
            return
        data.df = df
        data.latest_close = float(df['close'].iloc[-1])
        
        logging.info("STEP 2: คำนวณ Indicators"); console.print("[bold]Step 2:[/bold] คำนวณ Indicators...")
        df = calculate_indicators(df)
        data.indicators = {
            'rsi': df['rsi'].iloc[-1] if 'rsi' in df else None,
            'macd_line': df['macd_line'].iloc[-1] if 'macd_line' in df else None,
            'macd_signal': df['macd_signal'].iloc[-1] if 'macd_signal' in df else None,
            'macd_hist': df['macd_hist'].iloc[-1] if 'macd_hist' in df else None,
            'atr': df['atr'].iloc[-1] if 'atr' in df else None,
            'ema20': df['ema20'].iloc[-1] if 'ema20' in df else None,
        }
        
        logging.info("STEP 3: ตรวจจับ Candlestick Patterns"); console.print("[bold]Step 3:[/bold] ตรวจจับ Candlestick Patterns...")
        data.patterns = detect_candlestick_patterns(df)
        
        logging.info("STEP 4: คำนวณ Fibonacci Levels"); console.print("[bold]Step 4:[/bold] คำนวณ Fibonacci Levels...")
        sh, sl, _, _ = find_swing_high_low(df)
        data.fibonacci = calculate_fibonacci_levels(sh, sl)
        
        logging.info("STEP 5: คำนวณ Volume Profile (VPVR)"); console.print("[bold]Step 5:[/bold] คำนวณ Volume Profile (VPVR)...")
        data.vpvr = calculate_vpvr(df)
        
        logging.info("STEP 6: ส่งข้อมูลให้ AI วิเคราะห์"); console.print("[bold]Step 6:[/bold] ส่งข้อมูลให้ AI วิเคราะห์...")
        context = build_ai_context(data)
        data.ai_analysis = call_openrouter_ai(context)
        
        logging.info("STEP 7: แสดงผล"); console.print("[bold]Step 7:[/bold] แสดงผล...")
        display_rich_ui(data)
    except Exception as e:
        console.print(f"[red]เกิดข้อผิดพลาด: {e}[/red]")
        console.print(f"[red]{traceback.format_exc()}[/red]")

def main():
    """Entry Point"""
    logging.info(f"=== AI CRYPTO TRADING MONITOR v1.0 STARTED | {SYMBOL} {TIMEFRAME} | Mode={TEST_MODE} ==="); console.print("[bold green]========================================[/bold green]")
    console.print("[bold green]  AI CRYPTO TRADING MONITOR v1.0[/bold green]")
    console.print("[bold green]========================================[/bold green]")
    console.print(f"Symbol: {SYMBOL} | Timeframe: {TIMEFRAME} | Mode: {'TEST' if TEST_MODE else 'SCHEDULED'}")
    console.print("")
    
    if TEST_MODE:
        run_analysis()
    else:
        scheduler = BlockingScheduler()
        scheduler.add_job(run_analysis, CronTrigger(minute=0))
        console.print("[yellow]Scheduler started - รันทุกต้นชั่วโมง[/yellow]")
        try:
            run_analysis()
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            console.print("[yellow]Scheduler stopped[/yellow]")


# ============================================================
# Section 4: Rich UI Display
# ============================================================

def display_rich_ui(data: TradingData):
    """แสดงผล Rich UI บน Terminal"""
    console.clear()
    console.print(Panel.fit(
        f"[bold cyan]AI CRYPTO TRADING MONITOR[/bold cyan] | {SYMBOL} {TIMEFRAME}",
        border_style="cyan"
    ))
    console.print("")
    
    # Table 1: Market & Indicators
    table1 = Table(title="[bold]Market & Indicators[/bold]", box=box.ROUNDED)
    table1.add_column("Metric", style="cyan", width=20)
    table1.add_column("Value", style="white", width=15)
    table1.add_column("Signal", style="yellow", width=15)
    
    rsi = data.indicators.get('rsi', 0) or 0
    rsi_sig = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
    macd_hist = data.indicators.get('macd_hist', 0) or 0
    macd_sig = "Bullish" if macd_hist > 0 else "Bearish"
    
    table1.add_row("Price", f"${data.latest_close:.2f}", "-")
    table1.add_row("RSI (14)", f"{rsi:.2f}", rsi_sig)
    table1.add_row("MACD Hist", f"{macd_hist:.4f}", macd_sig)
    table1.add_row("ATR (14)", f"{data.indicators.get('atr', 0):.4f}", "-")
    table1.add_row("EMA 20", f"${data.indicators.get('ema20', 0):.2f}", "-")
    console.print(table1)
    console.print("")
    
    # Table 2: Key Levels
    table2 = Table(title="[bold]Key Levels (Fibonacci & VPVR)[/bold]", box=box.ROUNDED)
    table2.add_column("Level", style="cyan", width=15)
    table2.add_column("Price", style="white", width=15)
    table2.add_column("Distance %", style="yellow", width=15)
    
    for k, label in [('fib_382', 'Fib 0.382'), ('fib_500', 'Fib 0.500'), 
                     ('fib_618', 'Fib 0.618'), ('poc', 'POC'), ('vah', 'VAH'), ('val', 'VAL')]:
        if k in data.fibonacci:
            v = data.fibonacci[k]
            table2.add_row(label, f"${v:.2f}", f"{((data.latest_close - v) / v * 100):+.2f}%")
        elif k in data.vpvr:
            v = data.vpvr[k]
            table2.add_row(label, f"${v:.2f}", f"{((data.latest_close - v) / v * 100):+.2f}%")
    console.print(table2)
    console.print("")
    
    # Table 3: Candlestick Patterns
    table3 = Table(title="[bold]Candlestick Patterns[/bold]", box=box.ROUNDED)
    table3.add_column("Pattern", style="cyan", width=25)
    table3.add_column("Status", style="white", width=15)
    
    # All 11 patterns to display
    all_patterns = [
        ('bullish_engulfing', 'Bullish Engulfing'),
        ('bearish_engulfing', 'Bearish Engulfing'),
        ('bullish_pin_bar', 'Bullish Pin Bar'),
        ('bearish_pin_bar', 'Bearish Pin Bar'),
        ('doji', 'Doji'),
        ('hammer', 'Hammer'),
        ('inverted_hammer', 'Inverted Hammer'),
        ('shooting_star', 'Shooting Star'),
        ('hanging_man', 'Hanging Man'),
        ('piercing_line', 'Piercing Line'),
        ('dark_cloud_cover', 'Dark Cloud Cover'),
    ]
    for k, label in all_patterns:
        if k in data.patterns:
            status = "[green]DETECTED[/green]" if data.patterns[k] else "[dim]None[/dim]"
            table3.add_row(label, status)
    bull = len(data.patterns.get('bullish_signals', []))
    bear = len(data.patterns.get('bearish_signals', []))
    table3.add_row("[bold]Summary[/bold]", f"[yellow]Bull: {bull} | Bear: {bear}[/yellow]")
    console.print(table3)
    console.print("")
    
    if data.ai_analysis:
        console.print(Panel.fit(
            data.ai_analysis,
            title="[bold cyan]AI Analysis & Trading Plan[/bold cyan]",
            border_style="green", padding=(1, 2)
        ))
    console.print(f"[dim]Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")


if __name__ == "__main__":
    main()



