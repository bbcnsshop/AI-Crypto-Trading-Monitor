#!/usr/bin/env python3
"""AI Crypto Trading Monitor - CLI Interface

ใช้งาน:
    pip install click
    python maincli.py --help
    python maincli.py analyze -s BTC/USDT -t 1h
    python maincli.py monitor -i 60
    python maincli.py backtest
    python maincli.py config
"""
import os, logging, time, warnings
from datetime import datetime
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

# ============================================================
# Suppress SSL/urllib3 warnings (cross-platform safe)
# - macOS (LibreSSL): จับด้วย pattern '.*OpenSSL.*'
# - Windows/Linux: ไม่มี warning นี้ แต่ตัวกรองจะ no-op (ไม่กระทบ)
# - ไม่ปิด warnings ทั้งหมด เพื่อไม่ให้พลาด warning สำคัญอื่นๆ
# ============================================================
warnings.filterwarnings('ignore', message='.*OpenSSL.*')
warnings.filterwarnings('ignore', category=DeprecationWarning, module='urllib3')
logging.getLogger('urllib3').setLevel(logging.CRITICAL)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)

console = Console()

from config import (
    VERSION, SYMBOL, TIMEFRAME, CANDLE_LIMIT, SWING_LOOKBACK, VPVR_BINS,
    DISPLAY_MODE, AI_TRIGGER_MODE, TRIGGER_RSI_EXTREME, TRIGGER_PATTERN,
    TRIGGER_MACD_CROSS, TRIGGER_NEAR_LEVEL, TRIGGER_HIGH_VOLATILITY,
    TRIGGER_BIG_MOVE, AI_COOLDOWN_MAX_PER_HOUR, AI_COOLDOWN_SECONDS,
)
from indicators import calculate_indicators, calculate_fibonacci_levels, calculate_vpvr, find_swing_high_low
from ai_trigger import CooldownTracker, check_trigger
from ai_client import build_ai_context, call_openrouter_ai
from candlestick_patterns import detect_candlestick_patterns
from display import display_rich_ui, display_config


class MarketData:
    def __init__(self):
        self.symbol = self.timeframe = ""
        self.latest_close = 0
        self.indicators = self.patterns = self.fibonacci = self.vpvr = {}
        self.ai_analysis = ""
        self.backtest_result = {}


def fetch_data(symbol, timeframe, limit=100):
    import ccxt, pandas as pd
    try:
        exchange = ccxt.binance({'enableRateLimit': True})
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        console.print(f"[red]Error fetching data: {e}[/red]")
        return None


def run_quick_backtest(symbol, timeframe, candles=100):
    from ta.momentum import RSIIndicator
    from ta.trend import MACD
    from ta.volatility import AverageTrueRange
    df = fetch_data(symbol, timeframe, candles)
    if df is None:
        return {}
    try:
        df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
        macd = MACD(close=df['close'])
        df['macd_hist'] = macd.macd_diff()
        df['atr'] = AverageTrueRange(high=df['high'], low=df['low'], close=df['close']).average_true_range()
        signals = []
        for i in range(20, len(df) - 5):
            rsi = df['rsi'].iloc[i]
            macd_h = df['macd_hist'].iloc[i]
            atr = df['atr'].iloc[i]
            close = df['close'].iloc[i]
            tp = close + (atr * 2)
            sl = close - atr
            won = False
            for j in range(1, 6):
                if df['high'].iloc[i + j] >= tp:
                    won = True
                    break
                if df['low'].iloc[i + j] <= sl:
                    break
            if rsi < 40 and macd_h > 0:
                signals.append({'type': 'LONG', 'won': won})
            elif rsi > 60 and macd_h < 0:
                signals.append({'type': 'SHORT', 'won': won})
        if not signals:
            return {'winrate': 0, 'total_trades': 0, 'profit_factor': 0, 'total_pnl': 0,
                    'period': f"{df['timestamp'].iloc[0].date()} -> {df['timestamp'].iloc[-1].date()}"}
        total = len(signals)
        wins = sum(1 for s in signals if s['won'])
        longs = [s for s in signals if s['type'] == 'LONG']
        shorts = [s for s in signals if s['type'] == 'SHORT']
        wp = sum(2.0 for s in signals if s['won'])
        lp = sum(-1.0 for s in signals if not s['won'])
        return {'winrate': (wins / total * 100), 'total_trades': total,
                'profit_factor': abs(wp / lp) if lp != 0 else 0,
                'total_pnl': (wins * 2.0) - ((total - wins) * 1.0),
                'avg_win': 2.0, 'avg_loss': -1.0,
                'long_winrate': (sum(1 for s in longs if s['won']) / len(longs) * 100) if longs else 0,
                'short_winrate': (sum(1 for s in shorts if s['won']) / len(shorts) * 100) if shorts else 0,
                'period': f"{df['timestamp'].iloc[0].date()} -> {df['timestamp'].iloc[-1].date()}"}
    except Exception as e:
        logging.error(f"Backtest error: {e}")
        return {}


def analyze_market(symbol, timeframe):
    data = MarketData()
    data.symbol = symbol
    data.timeframe = timeframe
    cooldown_tracker = CooldownTracker()
    df = fetch_data(symbol, timeframe, CANDLE_LIMIT)
    if df is None:
        return data
    data.latest_close = df['close'].iloc[-1]
    df = calculate_indicators(df)
    data.indicators = {k: df[k].iloc[-1] if k in df else None
                       for k in ['rsi', 'macd_line', 'macd_signal', 'macd_hist', 'atr', 'ema20']}
    data.patterns = detect_candlestick_patterns(df)
    sh, sl, _, _ = find_swing_high_low(df, SWING_LOOKBACK)
    data.fibonacci = calculate_fibonacci_levels(sh, sl)
    data.vpvr = calculate_vpvr(df, VPVR_BINS)
    should_send, reason, _ = check_trigger(data, df, cooldown_tracker)
    if should_send:
        data.ai_analysis = call_openrouter_ai(build_ai_context(data))
        cooldown_tracker.record_send()
    else:
        data.ai_analysis = f"[AI Skipped: {reason}]"
    data.backtest_result = run_quick_backtest(symbol, timeframe, 100)
    return data


@click.group()
@click.version_option(version=VERSION, prog_name="binance-monitor")
def cli():
    """AI Crypto Trading Monitor - CLI Interface"""
    pass


@cli.command()
@click.option('--symbol', '-s', default='BTC/USDT', help='Symbol เช่น BTC/USDT')
@click.option('--timeframe', '-t', default='1h',
              type=click.Choice(['1m', '5m', '15m', '30m', '1h', '4h', '1d']),
              help='Timeframe')
@click.option('--mode', '-m', default='standard',
              type=click.Choice(['standard', 'compact', 'verbose']),
              help='Display mode')
def analyze(symbol, timeframe, mode):
    """วิเคราะห์ตลาดครั้งเดียว"""
    trigger_settings = {
        'rsi': TRIGGER_RSI_EXTREME, 'pattern': TRIGGER_PATTERN,
        'macd': TRIGGER_MACD_CROSS, 'near_level': TRIGGER_NEAR_LEVEL,
        'high_vol': TRIGGER_HIGH_VOLATILITY, 'big_move': TRIGGER_BIG_MOVE,
        'interval': 60,
    }
    display_config(
        symbol=symbol, timeframe=timeframe, display_mode=mode,
        trigger_mode=AI_TRIGGER_MODE, trigger_settings=trigger_settings,
        cooldown_max=AI_COOLDOWN_MAX_PER_HOUR, cooldown_sec=AI_COOLDOWN_SECONDS,
        version=VERSION
    )
    data = analyze_market(symbol, timeframe)
    if data.latest_close == 0:
        console.print("[red]ไม่สามารถดึงข้อมูลได้[/red]")
        return
    display_rich_ui(data, symbol, timeframe, mode)


@cli.command()
@click.option('--symbol', '-s', default='BTC/USDT', help='Symbol')
@click.option('--timeframe', '-t', default='1h', help='Timeframe')
@click.option('--interval', '-i', default=60, type=int, help='วิเคราะห์ทุกกี่นาที')
@click.option('--mode', '-m', default='standard', help='Display mode')
@click.option('--max-runs', '-n', default=None, type=int, help='จำนวนครั้งสูงสุด')
def monitor(symbol, timeframe, interval, mode, max_runs):
    """วิเคราะห์ต่อเนื่องทุก X นาที"""
    console.print(Panel.fit(
        f"[bold yellow]Monitor Mode[/bold yellow] | {symbol} {timeframe} | ทุก {interval} นาที",
        border_style="yellow"
    ))
    console.print("[dim]กด Ctrl+C เพื่อหยุด[/dim]\n")
    run_count = 0
    try:
        while True:
            run_count += 1
            console.print(f"\n[cyan]รอบที่ {run_count} | {datetime.now().strftime('%H:%M:%S')}[/cyan]")
            data = analyze_market(symbol, timeframe)
            if data.latest_close > 0:
                display_rich_ui(data, symbol, timeframe, mode)
            if max_runs and run_count >= max_runs:
                console.print(f"\n[green]เสร็จสิ้น {max_runs} รอบ[/green]")
                break
            console.print(f"\n[dim]รอ {interval} นาที... (Ctrl+C)[/dim]")
            time.sleep(interval * 60)
    except KeyboardInterrupt:
        console.print(f"\n[yellow]หยุด (รัน {run_count} รอบ)[/yellow]")


@cli.command()
@click.option('--symbol', '-s', default='BTC/USDT', help='Symbol')
@click.option('--timeframe', '-t', default='1h', help='Timeframe')
@click.option('--limit', '-l', default=100, type=int, help='จำนวน candles')
def backtest(symbol, timeframe, limit):
    """Quick Backtest"""
    console.print(Panel.fit(
        f"[bold green]Quick Backtest[/bold green] | {symbol} {timeframe} | {limit} candles",
        border_style="green"
    ))
    result = run_quick_backtest(symbol, timeframe, limit)
    if not result:
        console.print("[red]Backtest ล้มเหลว[/red]")
        return
    data = MarketData()
    data.backtest_result = result
    display_rich_ui(data, symbol, timeframe, 'standard')


@cli.command()
def config_cmd():
    """แสดง Configuration"""
    trigger_settings = {
        'rsi': TRIGGER_RSI_EXTREME, 'pattern': TRIGGER_PATTERN,
        'macd': TRIGGER_MACD_CROSS, 'near_level': TRIGGER_NEAR_LEVEL,
        'high_vol': TRIGGER_HIGH_VOLATILITY, 'big_move': TRIGGER_BIG_MOVE,
        'interval': 60,
    }
    display_config(
        symbol=SYMBOL, timeframe=TIMEFRAME, display_mode=DISPLAY_MODE,
        trigger_mode=AI_TRIGGER_MODE, trigger_settings=trigger_settings,
        cooldown_max=AI_COOLDOWN_MAX_PER_HOUR, cooldown_sec=AI_COOLDOWN_SECONDS,
        version=VERSION
    )


@cli.command()
def symbols():
    """แสดงรายการ Symbols ยอดนิยม"""
    table = Table(title="Symbols ยอดนิยม", box=box.ROUNDED)
    table.add_column("Symbol", style="cyan")
    table.add_column("Name", style="white")
    for sym, name in [("BTC/USDT", "Bitcoin"), ("ETH/USDT", "Ethereum"),
                      ("SOL/USDT", "Solana"), ("BNB/USDT", "Binance Coin"),
                      ("XRP/USDT", "Ripple"), ("ADA/USDT", "Cardano")]:
        table.add_row(sym, name)
    console.print(table)


if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(message)s',
        handlers=[logging.FileHandler('logs/trading_monitor.log'), logging.StreamHandler()]
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    cli()
