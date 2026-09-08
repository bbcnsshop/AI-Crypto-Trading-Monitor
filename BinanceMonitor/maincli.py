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
from functools import lru_cache

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
    get_exchange,
)
from indicators import calculate_indicators, calculate_fibonacci_levels, calculate_vpvr, find_swing_high_low
from ai_trigger import CooldownTracker, check_trigger
from ai_client import build_ai_context, call_openrouter_ai
from candlestick_patterns import detect_candlestick_patterns
from display import display_rich_ui, display_config


class MarketData:
    def __init__(self, symbol: str = "BTC/USDT", timeframe: str = "1h"):
        self.symbol = symbol
        self.timeframe = timeframe
        self.latest_close = 0
        self.indicators = self.patterns = self.fibonacci = self.vpvr = {}
        self.ai_analysis = ""
        self.backtest_result = {}


def fetch_data(symbol, timeframe, limit=100, max_retries=3, retry_delay=2):
    """Fetch OHLCV data with LRU cache to avoid duplicate API calls.
    Cache key: (symbol, timeframe, limit, minute_bucket)
    """
    import pandas as pd
    ts_bucket = int(time.time() // 60)  # bucket by minute
    return _fetch_data_cached(symbol, timeframe, limit, max_retries, retry_delay, ts_bucket)


def fetch_multiple(symbols, timeframe, limit=100, max_retries=3, retry_delay=2, max_workers=5):
    """Fetch OHLCV data for multiple symbols in parallel using multi-threading.
    
    Args:
        symbols: List of symbol strings (e.g., ['BTC/USDT', 'ETH/USDT'])
        timeframe: Timeframe string (e.g., '1h', '5m')
        limit: Number of candles to fetch
        max_retries: Max retry attempts per symbol
        retry_delay: Delay between retries in seconds
        max_workers: Max number of concurrent threads (default: 5)
    
    Returns:
        Dict mapping symbol -> DataFrame, or None if fetch failed
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    results = {}
    
    def fetch_single(symbol):
        """Internal: fetch data for a single symbol."""
        try:
            return fetch_data(symbol, timeframe, limit, max_retries, retry_delay)
        except Exception as e:
            console.print(f"[yellow]⚠ Error fetching {symbol}: {e}[/yellow]")
            return None
    
    # Use ThreadPoolExecutor to fetch symbols in parallel
    # Limit workers to avoid hitting exchange rate limits
    effective_workers = min(max_workers, len(symbols)) if symbols else max_workers
    
    with ThreadPoolExecutor(max_workers=effective_workers) as executor:
        futures = {executor.submit(fetch_single, symbol): symbol for symbol in symbols}
        
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                results[symbol] = future.result()
                if results[symbol] is not None:
                    console.print(f"[green]✓ Fetched {symbol}: {len(results[symbol])} candles[/green]")
                else:
                    console.print(f"[red]✗ Failed to fetch {symbol}[/red]")
            except Exception as e:
                console.print(f"[red]✗ Error with {symbol}: {e}[/red]")
                results[symbol] = None
    
    return results


@lru_cache(maxsize=32)
def _fetch_data_cached(symbol, timeframe, limit, max_retries, retry_delay, ts_bucket):
    """Cached fetch_data implementation."""
    import pandas as pd
    for attempt in range(1, max_retries + 1):
        try:
            exchange = get_exchange()
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            if attempt < max_retries:
                console.print(f"[yellow]⚠ Fetch attempt {attempt}/{max_retries} failed: {e}. Retrying in {retry_delay}s...[/yellow]")
                time.sleep(retry_delay)
            else:
                console.print(f"[red]Error fetching data after {max_retries} attempts: {e}[/red]")
                return None


def run_quick_backtest(symbol, timeframe, candles=100, df=None):
    """Returns (result_dict, df) tuple or ({}, None) on error.
    If df is provided, use it instead of fetching new data.
    """
    import numpy as np
    from ta.momentum import RSIIndicator
    from ta.trend import MACD, EMAIndicator
    from ta.volatility import AverageTrueRange
    try:
        if df is None:
            df = fetch_data(symbol, timeframe, candles)
        if df is None:
            return {}, None
        # Skip recalculating indicators if already present (analyze_market provides pre-calculated df)
        needs_calc = not all(col in df.columns for col in ['rsi', 'macd_hist', 'atr', 'ema20'])
        if needs_calc:
            df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
            macd = MACD(close=df['close'])
            df['macd_hist'] = macd.macd_diff()
            df['macd_line'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['atr'] = AverageTrueRange(high=df['high'], low=df['low'], close=df['close']).average_true_range()
            df['ema20'] = EMAIndicator(close=df['close'], window=20, fillna=False).ema_indicator()

        # Use numpy arrays for faster loop iteration
        rsi_arr = df['rsi'].values
        macd_arr = df['macd_hist'].values
        atr_arr = df['atr'].values
        close_arr = df['close'].values
        high_arr = df['high'].values
        low_arr = df['low'].values

        n = len(df)
        if n <= 25:
            return ({'winrate': 0, 'total_trades': 0, 'profit_factor': 0, 'total_pnl': 0,
                    'period': f"{df['timestamp'].iloc[0].date()} -> {df['timestamp'].iloc[-1].date()}"}, df)

        # Precompute TP/SL arrays
        tp = close_arr + atr_arr * 2
        sl = close_arr - atr_arr

        signals = []
        for i in range(20, n - 5):
            won = False
            for j in range(1, 6):
                if high_arr[i + j] >= tp[i]:
                    won = True
                    break
                if low_arr[i + j] <= sl[i]:
                    break
            if rsi_arr[i] < 40 and macd_arr[i] > 0:
                signals.append({'type': 'LONG', 'won': won})
            elif rsi_arr[i] > 60 and macd_arr[i] < 0:
                signals.append({'type': 'SHORT', 'won': won})

        if not signals:
            return ({'winrate': 0, 'total_trades': 0, 'profit_factor': 0, 'total_pnl': 0,
                    'period': f"{df['timestamp'].iloc[0].date()} -> {df['timestamp'].iloc[-1].date()}"}, df)
        total = len(signals)
        wins = sum(1 for s in signals if s['won'])
        longs = [s for s in signals if s['type'] == 'LONG']
        shorts = [s for s in signals if s['type'] == 'SHORT']
        wp = sum(2.0 for s in signals if s['won'])
        lp = sum(-1.0 for s in signals if not s['won'])
        result = {'winrate': (wins / total * 100), 'total_trades': total,
                'profit_factor': abs(wp / lp) if lp != 0 else 0,
                'total_pnl': (wins * 2.0) - ((total - wins) * 1.0),
                'avg_win': 2.0, 'avg_loss': -1.0,
                'long_winrate': (sum(1 for s in longs if s['won']) / len(longs) * 100) if longs else 0,
                'short_winrate': (sum(1 for s in shorts if s['won']) / len(shorts) * 100) if shorts else 0,
                'period': f"{df['timestamp'].iloc[0].date()} -> {df['timestamp'].iloc[-1].date()}"}
        return result, df
    except Exception as e:
        logging.error(f"Backtest error: {e}")
        return {}, None


def analyze_market(symbol, timeframe):
    data = MarketData()
    data.symbol = symbol
    data.timeframe = timeframe
    cooldown_tracker = CooldownTracker()
    # Use multi-threaded fetch for parallel API calls
    results = fetch_multiple([symbol], timeframe, CANDLE_LIMIT)
    df = results.get(symbol)
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
    backtest_result, _ = run_quick_backtest(symbol, timeframe, CANDLE_LIMIT, df=df)
    data.backtest_result = backtest_result
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
@click.option('--interval', '-i', default=5, type=int, help='เช็คทุกกี่นาที')
@click.option('--mode', '-m', default='compact', help='Display mode (เมื่อ trigger ทำงาน)')
@click.option('--max-runs', '-n', default=None, type=int, help='จำนวนรอบสูงสุด (None=ไม่จำกัด)')
@click.option('--once', is_flag=True, help='เช็คครั้งเดียวแล้วออก (debug)')
def monitor(symbol, timeframe, interval, mode, max_runs, once):
    """Monitor ตลาด - แสดงสถานะ และวิเคราะห์เฉพาะเมื่อ Smart Trigger ทำงาน"""
    console.print(Panel.fit(
        f"[bold yellow]👁️ Monitor Mode[/bold yellow] | {symbol} {timeframe} | เช็คทุก {interval} นาที",
        border_style="yellow"
    ))
    console.print(f"[dim]Trigger Mode: {AI_TRIGGER_MODE.upper()} | Cooldown: {AI_COOLDOWN_MAX_PER_HOUR}/hr[/dim]")
    console.print("[dim]กด Ctrl+C เพื่อหยุด[/dim]\n")

    cooldown_tracker = CooldownTracker()
    check_count = 0
    trigger_count = 0

    try:
        while True:
            check_count += 1
            now = datetime.now().strftime('%H:%M:%S')
            console.rule(f"[cyan]เช็ครอบที่ {check_count} | {now}[/cyan]")

            # ดึงข้อมูล + คำนวณ indicators (ใช้ multi-threading)
            results = fetch_multiple([symbol], timeframe, CANDLE_LIMIT)
            df = results.get(symbol)
            if df is None:
                console.print(f"[red]❌ ดึงข้อมูลไม่สำเร็จ[/red]")
                if once:
                    break
                time.sleep(interval * 60)
                continue

            # สร้าง data object (ไม่เรียก AI)
            data = MarketData()
            data.symbol = symbol
            data.timeframe = timeframe
            data.latest_close = df['close'].iloc[-1]
            prev_close = df['close'].iloc[-2] if len(df) >= 2 else 0
            if prev_close > 0:
                data.price_change_pct = ((data.latest_close - prev_close) / prev_close) * 100
            else:
                data.price_change_pct = 0.0

            # คำนวณ indicators (ดึงค่า scalar จาก Series)
            indicators = calculate_indicators(df)
            def get_val(key):
                val = indicators.get(key, 0)
                if hasattr(val, 'iloc') and len(val) > 0:
                    return float(val.iloc[-1])
                return float(val) if val != 0 else 0.0
            # เซ็ต data.indicators dict ที่ check_trigger ต้องการ
            data.indicators = {
                'rsi': get_val('rsi'),
                'macd_line': get_val('macd_line'),
                'macd_signal': get_val('macd_signal'),
                'macd_hist': get_val('macd_hist'),
                'atr': get_val('atr'),
                'ema20': get_val('ema20'),
            }
            # เก็บเป็น flat fields เพื่อ monitor display
            data.rsi = data.indicators['rsi']
            data.macd_hist = data.indicators['macd_hist']
            data.atr = data.indicators['atr']
            data.ema_20 = data.indicators['ema20']

            sh, sl, _, _ = find_swing_high_low(df, SWING_LOOKBACK)
            data.fibonacci = calculate_fibonacci_levels(sh, sl)
            data.vpvr = calculate_vpvr(df, VPVR_BINS)

            # ตรวจ patterns (data.patterns dict ที่ check_trigger ต้องการ)
            data.patterns = detect_candlestick_patterns(df)
            bullish_count = sum(1 for k, v in data.patterns.items() if v and 'bull' in k.lower())
            bearish_count = sum(1 for k, v in data.patterns.items() if v and 'bear' in k.lower())
            data.bullish_patterns = bullish_count
            data.bearish_patterns = bearish_count

            # แสดงสถานะ (ไม่เรียก AI)
            price = data.latest_close
            rsi = data.rsi
            rsi_status = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
            macd_status = "Bullish" if data.macd_hist > 0 else "Bearish"

            console.print(f"  💰 Price: [bold]${price:,.2f}[/bold] ({data.price_change_pct:+.2f}%)")
            console.print(f"  📊 RSI: {rsi:.1f} ({rsi_status}) | MACD: {macd_status} | ATR: {data.atr:.2f}")

            # เช็ค Smart Trigger
            should_send, reason, trigger_type = check_trigger(data, df, cooldown_tracker)

            if should_send:
                trigger_count += 1
                console.print(f"\n  [bold green]🚨 TRIGGER! {trigger_type}[/bold green]")
                console.print(f"  [green]เหตุผล: {reason}[/green]")

                # เรียก AI วิเคราะห์
                console.print(f"  [cyan]🤖 กำลังเรียก AI...[/cyan]")
                data.ai_analysis = call_openrouter_ai(build_ai_context(data))
                cooldown_tracker.record_send()

                if data.ai_analysis:
                    # แสดงผลเต็ม
                    display_rich_ui(data, symbol, timeframe, mode)
                else:
                    console.print(f"  [red]❌ AI วิเคราะห์ล้มเหลว[/red]")
            else:
                # ไม่ trigger - แสดงเหตุผล
                console.print(f"  [dim]⏸️  {reason}[/dim]")

            # สรุปสถานะ cooldown
            can_send, cooldown_reason = cooldown_tracker.can_send()
            status = "🟢 พร้อม" if can_send else "🟡 Cooldown"
            console.print(f"  [dim]AI Status: {status} | ส่งไปแล้ว: {trigger_count} ครั้ง[/dim]")

            if max_runs and check_count >= max_runs:
                console.print(f"\n[green]เสร็จสิ้น {max_runs} รอบ (Trigger: {trigger_count} ครั้ง)[/green]")
                break

            if once:
                break

            console.print(f"\n[dim]💤 รอ {interval} นาที... (Ctrl+C หยุด)[/dim]")
            time.sleep(interval * 60)

    except KeyboardInterrupt:
        console.print(f"\n[yellow]หยุด (เช็ค {check_count} รอบ, Trigger {trigger_count} ครั้ง)[/yellow]")


@cli.command()
@click.option('--symbol', '-s', default='BTC/USDT', help='Symbol')
@click.option('--timeframe', '-t', default='1h', help='Timeframe')
@click.option('--limit', '-l', default=500, type=int, help='จำนวน candles (default: 500)')
def backtest(symbol, timeframe, limit):
    """Quick Backtest"""
    console.print(Panel.fit(
        f"[bold green]Quick Backtest[/bold green] | {symbol} {timeframe} | {limit} candles",
        border_style="green"
    ))
    # Use multi-threaded fetch
    results = fetch_multiple([symbol], timeframe, limit)
    df = results.get(symbol)
    result = {}
    if df is not None:
        result, _ = run_quick_backtest(symbol, timeframe, limit, df=df)
    if not result:
        console.print("[yellow]Backtest สำเร็จแต่ไม่มีสัญญาณเทรด (empty data)[/yellow]")
    data = MarketData()
    data.symbol = symbol
    data.timeframe = timeframe
    data.backtest_result = result
    # populate current price + indicators for display (use df from backtest, no extra fetch)
    if df is not None:
        data.latest_close = df['close'].iloc[-1]
        prev_close_bt = df['close'].iloc[-2] if len(df) >= 2 else 0
        if prev_close_bt > 0:
            data.price_change_pct = ((data.latest_close - prev_close_bt) / prev_close_bt) * 100
        else:
            data.price_change_pct = 0.0
        # populate indicators from backtest df (already has rsi, macd_hist, atr, ema20)
        def get_val(key):
            val = df[key].iloc[-1] if key in df else 0
            return float(val) if val and val == val else 0.0  # handle nan
        data.indicators = {
            'rsi': get_val('rsi'),
            'macd_line': get_val('macd_line') if 'macd_line' in df else 0.0,
            'macd_signal': get_val('macd_signal') if 'macd_signal' in df else 0.0,
            'macd_hist': get_val('macd_hist'),
            'atr': get_val('atr'),
            'ema20': get_val('ema20'),
        }
    display_rich_ui(data, symbol, timeframe, 'standard')


@cli.command('config')
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


@cli.command()
@click.option('--symbols', '-s', default='BTC/USDT,ETH/USDT,BNB/USDT,SOL/USDT,XRP/USDT',
              help='Comma-separated symbols (e.g., BTC/USDT,ETH/USDT)')
@click.option('--timeframe', '-t', default='1h',
              type=click.Choice(['1m', '5m', '15m', '30m', '1h', '4h', '1d']),
              help='Timeframe')
@click.option('--limit', '-l', default=500, type=int, help='Number of candles per symbol')
@click.option('--workers', '-w', default=5, type=int, help='Max concurrent threads')
def fetch(symbols, timeframe, limit, workers):
    """Fetch multiple symbols in parallel using multi-threading (Phase 3)"""
    symbol_list = [s.strip() for s in symbols.split(',')]
    console.print(f"\n[bold cyan]⚡ Fetching {len(symbol_list)} symbols in parallel[/bold cyan]")
    console.print(f"[dim]Timeframe: {timeframe} | Limit: {limit} | Workers: {workers}[/dim]\n")
    
    import time
    start = time.time()
    results = fetch_multiple(symbol_list, timeframe, limit, max_workers=workers)
    elapsed = time.time() - start
    
    success_count = sum(1 for v in results.values() if v is not None)
    console.print(f"\n[bold]✅ Fetched {success_count}/{len(symbol_list)} symbols in {elapsed:.2f}s[/bold]")


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
