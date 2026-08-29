"""AI Crypto Trading Monitor - Main Entry Point"""
import os, logging
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict
import ccxt, pandas as pd
from rich.console import Console
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from config import (
    TEST_MODE, SYMBOL, TIMEFRAME, CANDLE_LIMIT, SWING_LOOKBACK, VPVR_BINS,
    DISPLAY_MODE, LOG_DIR, LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT,
    AI_COOLDOWN_MAX_PER_HOUR, TRIGGER_RSI_EXTREME, TRIGGER_PATTERN,
    TRIGGER_MACD_CROSS, TRIGGER_NEAR_LEVEL, TRIGGER_HIGH_VOLATILITY,
    TRIGGER_BIG_MOVE, SCHEDULE_INTERVAL_MINUTES, AI_COOLDOWN_SECONDS,
    AI_TRIGGER_MODE, VERSION
)
from indicators import calculate_indicators, calculate_fibonacci_levels, calculate_vpvr, find_swing_high_low
from ai_trigger import CooldownTracker, check_trigger
from ai_client import build_ai_context, call_openrouter_ai
from candlestick_patterns import detect_candlestick_patterns
from display import display_rich_ui as display_rich_ui_new, display_config

console = Console()

class TradingData:
    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.latest_close: float = 0
        self.indicators: Dict = {}
        self.fibonacci: Dict = {}
        self.vpvr: Dict = {}
        self.patterns: Dict = {}
        self.ai_analysis: str = ""

def setup_logging():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    try:
        fh = RotatingFileHandler(LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding='utf-8')
        fh.setLevel(logging.ERROR)
        fh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s'))
        logger.addHandler(fh)
    except Exception:
        pass

_cooldown_tracker = CooldownTracker()

def run_analysis():
    data = TradingData()
    try:
        console.print("[bold]Step 1:[/bold] ดึงข้อมูลตลาด...")
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=CANDLE_LIMIT)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        data.df = df
        data.latest_close = df['close'].iloc[-1]
        console.print(f"  [green]✓[/green] {len(df)} แท่ง, Price: ${data.latest_close:,.2f}")

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

        console.print("[bold]Step 3:[/bold] ตรวจจับ Candlestick Patterns...")
        data.patterns = detect_candlestick_patterns(df)
        bull = sum(1 for k, v in data.patterns.items() if v and 'bull' in k.lower())
        bear = sum(1 for k, v in data.patterns.items() if v and 'bear' in k.lower())
        console.print(f"  [green]✓[/green] Bull: {bull} | Bear: {bear}")

        console.print("[bold]Step 4:[/bold] คำนวณ Fibonacci Levels...")
        sh, sl, _, _ = find_swing_high_low(df, SWING_LOOKBACK)
        data.fibonacci = calculate_fibonacci_levels(sh, sl)
        console.print(f"  [green]✓[/green] Fib 0.618: ${data.fibonacci.get('fib_618', 0):.2f}")

        console.print("[bold]Step 5:[/bold] คำนวณ Volume Profile (VPVR)...")
        data.vpvr = calculate_vpvr(df, VPVR_BINS)
        console.print(f"  [green]✓[/green] POC: ${data.vpvr.get('poc', 0):.2f}")

        should_send, reason, trigger_type = check_trigger(data, df, _cooldown_tracker)
        if should_send:
            console.print(f"[bold]Step 6:[/bold] ส่ง AI... [green]({trigger_type})[/green]")
            data.ai_analysis = call_openrouter_ai(build_ai_context(data))
            _cooldown_tracker.record_send()
            console.print(f"  [green]✓ AI[/green] ({_cooldown_tracker.ai_count_this_hour}/{AI_COOLDOWN_MAX_PER_HOUR})")
        else:
            console.print(f"[bold]Step 6:[/bold] [yellow]ข้าม AI[/yellow] ({reason})")
            data.ai_analysis = f"[AI Skipped: {reason}]"

        console.print("[bold]Step 7:[/bold] แสดงผล...")
        display_rich_ui_new(data, SYMBOL, TIMEFRAME, DISPLAY_MODE)
    except Exception as e:
        logging.error(f"Error: {e}")
        console.print(f"[red]Error: {e}[/red]")

def main():
    setup_logging()
    trigger_settings = {
        'rsi': TRIGGER_RSI_EXTREME, 'pattern': TRIGGER_PATTERN,
        'macd': TRIGGER_MACD_CROSS, 'near_level': TRIGGER_NEAR_LEVEL,
        'high_vol': TRIGGER_HIGH_VOLATILITY, 'big_move': TRIGGER_BIG_MOVE,
        'interval': SCHEDULE_INTERVAL_MINUTES,
    }
    display_config(
        symbol=SYMBOL, timeframe=TIMEFRAME, display_mode=DISPLAY_MODE,
        trigger_mode=AI_TRIGGER_MODE, trigger_settings=trigger_settings,
        cooldown_max=AI_COOLDOWN_MAX_PER_HOUR, cooldown_sec=AI_COOLDOWN_SECONDS,
        version=VERSION
    )
    if TEST_MODE:
        run_analysis()
    else:
        scheduler = BlockingScheduler()
        scheduler.add_job(run_analysis, CronTrigger(minute=0))
        try:
            run_analysis()
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            console.print("[yellow]Stopped[/yellow]")

if __name__ == "__main__":
    main()
