"""
AI Crypto Trading Monitor - Main Entry Point
============================================
บอทสแกนกราฟคริปโท (BTC/USDT) ดึงข้อมูลจาก Binance ผ่าน ccxt
คำนวณ Indicators (RSI, MACD, ATR, EMA) ด้วย ta library
ตรวจจับ Candlestick Patterns ด้วย custom library
Fibonacci Retracement/Extension, VPVR (Volume Profile)
แล้วส่งข้อมูลให้ AI ผ่าน OpenRouter เพื่อวิเคราะห์จุดเข้า 3 ระดับ (3-Tier Entry)
พร้อม TP/SL และแสดงผลบน Terminal ด้วย Rich UI

Modules:
- config.py: Configuration variables
- indicators.py: Indicators, Fibonacci, VPVR
- ai_trigger.py: Smart Trigger + Cooldown
- ai_client.py: AI Context + OpenRouter API
- display.py: Rich UI Display
- candlestick_patterns.py: Candlestick Patterns
"""

import os
import sys
import time
import traceback
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any

import ccxt
import pandas as pd
import numpy as np
from rich.console import Console
from rich.panel import Panel
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Import from modules
from config import (
    TEST_MODE, SYMBOL, TIMEFRAME, CANDLE_LIMIT, SWING_LOOKBACK,
    VPVR_BINS, VALUE_AREA_PCT, DISPLAY_MODE,
    LOG_DIR, LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT,
    AI_COOLDOWN_MAX_PER_HOUR,
    TRIGGER_RSI_EXTREME, TRIGGER_PATTERN, TRIGGER_MACD_CROSS,
    TRIGGER_NEAR_LEVEL, TRIGGER_HIGH_VOLATILITY, TRIGGER_BIG_MOVE,
    RSI_OVERSOLD, RSI_OVERBOUGHT, ATR_HIGH_PCT,
    LEVEL_DISTANCE_PCT, BIG_MOVE_PCT, AI_COOLDOWN_SECONDS,
    VERSION
)
from indicators import (
    calculate_indicators, calculate_fibonacci_levels,
    calculate_vpvr, find_swing_high_low
)
from ai_trigger import CooldownTracker, should_send_ai
from ai_client import build_ai_context, call_openrouter_ai
from candlestick_patterns import detect_candlestick_patterns
from display import display_rich_ui as display_rich_ui_new

console = Console()


class TradingData:
    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.latest_close: float = 0
        self.indicators: Dict = {}
        self.fibonacci: Dict = {}
        self.vpvr: Dict = {}
        self.patterns: Dict = {}
        self.strategy: Dict = {}
        self.ai_analysis: str = ""


def setup_logging():
    """Setup logging - Console: INFO+, File: ERROR only"""
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
    try:
        for old_file in [LOG_FILE] + [f"{LOG_FILE}.{i}" for i in range(1, LOG_BACKUP_COUNT + 1)]:
            if os.path.exists(old_file):
                try:
                    os.remove(old_file)
                except Exception:
                    pass
        fh = RotatingFileHandler(LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding='utf-8')
        fh.setLevel(logging.ERROR)
        fh.setFormatter(file_fmt)
        logger.addHandler(fh)
    except Exception as e:
        console.print(f"[red]ไม่สามารถสร้าง File Handler: {e}[/red]")
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(console_fmt)
    logger.addHandler(ch)


def fetch_market_data(symbol: str, timeframe: str, limit: int) -> Optional[pd.DataFrame]:
    """ดึงข้อมูล OHLCV จาก Binance ผ่าน ccxt"""
    try:
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not ohlcv or len(ohlcv) == 0:
            console.print("[red]ไม่ได้รับข้อมูลจาก API[/red]")
            return None
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        console.print(f"[red]เกิดข้อผิดพลาดในการดึงข้อมูล: {e}[/red]")
        return None



_cooldown_tracker = CooldownTracker()

def run_analysis():
    """รันกระบวนการวิเคราะห์ทั้งหมด"""
    data = TradingData()
    try:
        # STEP 1: ดึงข้อมูล
        logging.info("STEP 1: ดึงข้อมูลตลาด")
        console.print("[bold]Step 1:[/bold] ดึงข้อมูลตลาด...")
        df = fetch_market_data(SYMBOL, TIMEFRAME, CANDLE_LIMIT)
        if df is None or df.empty:
            console.print("[red]ไม่สามารถดึงข้อมูลได้[/red]")
            return
        data.df = df
        data.latest_close = float(df['close'].iloc[-1])
        console.print(f"  [green]✓[/green] {len(df)} แท่ง, Price: ${data.latest_close:,.2f}")
        
        # STEP 2: Indicators
        logging.info("STEP 2: คำนวณ Indicators")
        console.print("[bold]Step 2:[/bold] คำนวณ Indicators...")
        df = calculate_indicators(df)
        data.indicators = {
            'rsi': df['rsi'].iloc[-1] if 'rsi' in df else None,
            'macd_line': df['macd_line'].iloc[-1] if 'macd_line' in df else None,
            'macd_signal': df['macd_signal'].iloc[-1] if 'macd_signal' in df else None,
            'macd_hist': df['macd_hist'].iloc[-1] if 'macd_hist' in df else None,
            'atr': df['atr'].iloc[-1] if 'atr' in df else None,
            'ema20': df['ema20'].iloc[-1] if 'ema20' in df else None,
        }
        console.print(f"  [green]✓[/green] RSI: {data.indicators['rsi']:.1f}, MACD: {data.indicators['macd_hist']:+.2f}")
        
        # STEP 3: Patterns
        logging.info("STEP 3: ตรวจจับ Candlestick Patterns")
        console.print("[bold]Step 3:[/bold] ตรวจจับ Candlestick Patterns...")
        data.patterns = detect_candlestick_patterns(df)
        bull = sum(1 for k, v in data.patterns.items() if v and 'bull' in k.lower())
        bear = sum(1 for k, v in data.patterns.items() if v and 'bear' in k.lower())
        console.print(f"  [green]✓[/green] Bull: {bull} | Bear: {bear}")
        
        # STEP 4: Fibonacci
        logging.info("STEP 4: คำนวณ Fibonacci Levels")
        console.print("[bold]Step 4:[/bold] คำนวณ Fibonacci Levels...")
        sh, sl, _, _ = find_swing_high_low(df, SWING_LOOKBACK)
        data.fibonacci = calculate_fibonacci_levels(sh, sl)
        if data.fibonacci:
            console.print(f"  [green]✓[/green] Fib 0.618: ${data.fibonacci.get('fib_618', 0):.2f}")
        
        # STEP 5: VPVR
        logging.info("STEP 5: คำนวณ Volume Profile")
        console.print("[bold]Step 5:[/bold] คำนวณ Volume Profile (VPVR)...")
        data.vpvr = calculate_vpvr(df, VPVR_BINS)
        if data.vpvr:
            console.print(f"  [green]✓[/green] POC: ${data.vpvr.get('poc', 0):.2f}")
        
        # STEP 6: AI Trigger
        should_send, reason, trigger_type = should_send_ai(data, df, _cooldown_tracker)
        if should_send:
            logging.info(f"STEP 6: ส่ง AI | {trigger_type} | {reason}")
            console.print(f"[bold]Step 6:[/bold] ส่ง AI... [green]({trigger_type})[/green]")
            console.print(f"  [dim]{reason}[/dim]")
            data.ai_analysis = call_openrouter_ai(build_ai_context(data))
            _cooldown_tracker.record_send()
            console.print(f"  [green]✓ AI[/green] ({_cooldown_tracker.ai_count_this_hour}/{AI_COOLDOWN_MAX_PER_HOUR})")
        else:
            logging.info(f"STEP 6: ข้าม AI | {reason}")
            console.print(f"[bold]Step 6:[/bold] [yellow]ข้าม AI[/yellow]")
            console.print(f"  [dim]{reason}[/dim]")
            data.ai_analysis = f"[AI Skipped: {reason}]"
        
        # STEP 7: Display
        logging.info("STEP 7: แสดงผล")
        console.print("[bold]Step 7:[/bold] แสดงผล...")
        display_rich_ui_new(data, SYMBOL, TIMEFRAME, DISPLAY_MODE)
        
    except Exception as e:
        logging.error(f"Error: {e}")
        console.print(f"[red]Error: {e}[/red]")


def main():
    setup_logging()
    logging.info(f"=== MONITOR STARTED | {SYMBOL} {TIMEFRAME} | Mode={TEST_MODE} ===")
    console.print(f"[bold green]=== AI CRYPTO TRADING MONITOR v{VERSION} ===[/bold green]")
    console.print(f"Symbol: {SYMBOL} | Timeframe: {TIMEFRAME}")
    
    # Triggers info
    console.print("[bold]📊 Smart Triggers:[/bold]")
    t = []
    if TRIGGER_RSI_EXTREME: t.append(f"RSI <{RSI_OVERSOLD}/ >{RSI_OVERBOUGHT}")
    if TRIGGER_PATTERN: t.append("Pattern")
    if TRIGGER_MACD_CROSS: t.append("MACD Cross")
    if TRIGGER_NEAR_LEVEL: t.append(f"Near ±{LEVEL_DISTANCE_PCT}%")
    if TRIGGER_HIGH_VOLATILITY: t.append(f"Vol >{ATR_HIGH_PCT}%")
    if TRIGGER_BIG_MOVE: t.append(f"Move >{BIG_MOVE_PCT}%")
    console.print(f"  [cyan]{', '.join(t)}[/cyan]")
    console.print(f"[dim]Cooldown: {AI_COOLDOWN_MAX_PER_HOUR}/hr, min {AI_COOLDOWN_SECONDS}s[/dim]")
    console.print("")
    
    if TEST_MODE:
        run_analysis()
    else:
        scheduler = BlockingScheduler()
        scheduler.add_job(run_analysis, CronTrigger(minute=0))
        console.print("[yellow]Scheduler started[/yellow]")
        try:
            run_analysis()
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            console.print("[yellow]Stopped[/yellow]")


if __name__ == "__main__":
    main()
