"""
Backtest & Winrate Testing Module
=================================
ทดสอบ Winrate ของกลยุทธ์ AI Crypto Trading Monitor
โดยย้อนกลับไปดูข้อมูลในอดีต (historical data) แล้วทดสอบว่า
หากใช้ logic เดียวกัน จะชนะกี่ % (Winrate)
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import ccxt
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from dotenv import load_dotenv

from candlestick_patterns import detect_candlestick_patterns
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import AverageTrueRange

console = Console()
load_dotenv()

# ============================================================
# Backtest Configuration
# ============================================================
SYMBOL = os.getenv("SYMBOL", "BTC/USDT")
TIMEFRAME = os.getenv("TIMEFRAME", "1h")
BACKTEST_CANDLES = 1000        # ดึงข้อมูลย้อนหลัง 1000 แท่ง
FORWARD_WINDOW = 10            # ดูผลใน 10 แท่งข้างหน้า
TP_ATR_MULTIPLIER = 2.0        # TP = 2 ATR
SL_ATR_MULTIPLIER = 1.0        # SL = 1 ATR

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")


def fetch_historical_data(symbol: str, timeframe: str, limit: int) -> Optional[pd.DataFrame]:
    """ดึงข้อมูล OHLCV ย้อนหลัง"""
    try:
        if BINANCE_API_KEY and BINANCE_API_SECRET:
            exchange = ccxt.binance({
                'apiKey': BINANCE_API_KEY,
                'secret': BINANCE_API_SECRET,
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'},
            })
        else:
            exchange = ccxt.binance({
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'},
            })
        console.print(f"[dim]กำลังดึงข้อมูลย้อนหลัง {limit} แท่ง ({symbol} {timeframe})...[/dim]")
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        console.print(f"[green]✓ ดึงข้อมูลสำเร็จ: {len(df)} แท่ง[/green]")
        console.print(f"[dim]ช่วงเวลา: {df['timestamp'].iloc[0]} ถึง {df['timestamp'].iloc[-1]}[/dim]")
        return df
    except Exception as e:
        console.print(f"[red]✗ ดึงข้อมูลล้มเหลว: {e}[/red]")
        return None


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """คำนวณ Indicators ทั้งหมด"""
    df = df.copy()
    rsi_ind = RSIIndicator(close=df['close'], window=14, fillna=False)
    df['rsi'] = rsi_ind.rsi()
    macd_ind = MACD(close=df['close'], window_slow=26, window_fast=12, window_sign=9, fillna=False)
    df['macd_line'] = macd_ind.macd()
    df['macd_signal'] = macd_ind.macd_signal()
    df['macd_hist'] = macd_ind.macd_diff()
    atr_ind = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14, fillna=False)
    df['atr'] = atr_ind.average_true_range()
    ema_ind = EMAIndicator(close=df['close'], window=20, fillna=False)
    df['ema20'] = ema_ind.ema_indicator()
    return df

def generate_signal(row, patterns: Dict) -> str:
    """สร้างสัญญาณเทรดจาก indicators + patterns
    Returns: 'LONG', 'SHORT', หรือ 'HOLD'
    """
    rsi = row.get('rsi', 50) or 50
    macd_hist = row.get('macd_hist', 0) or 0
    close = row.get('close', 0) or 0
    ema20 = row.get('ema20', 0) or 0

    bull_count = sum(1 for k, v in patterns.items() if v and 'bull' in k.lower())
    bear_count = sum(1 for k, v in patterns.items() if v and 'bear' in k.lower())

    # Long: RSI oversold + Bullish pattern + MACD positive + ใกล้ EMA20
    if rsi < 35 and (bull_count > 0 or macd_hist > 0) and close > ema20 * 0.98:
        return 'LONG'

    # Short: RSI overbought + Bearish pattern + MACD negative + ใกล้ EMA20
    if rsi > 65 and (bear_count > 0 or macd_hist < 0) and close < ema20 * 1.02:
        return 'SHORT'

    return 'HOLD'


def check_trade_result(
    future_candles: pd.DataFrame,
    entry_price: float,
    direction: str,
    tp: float,
    sl: float,
) -> Tuple[str, float, int]:
    """ตรวจสอบผลลัพธ์ของไม้เทรด
    Returns: ('WIN' | 'LOSS' | 'NEUTRAL', pnl_pct, bars_held)
    """
    for i, (_, candle) in enumerate(future_candles.iterrows()):
        high = candle['high']
        low = candle['low']

        if direction == 'LONG':
            if high >= tp:
                return 'WIN', (tp - entry_price) / entry_price * 100, i + 1
            if low <= sl:
                return 'LOSS', (sl - entry_price) / entry_price * 100, i + 1
        elif direction == 'SHORT':
            if low <= tp:
                return 'WIN', (entry_price - tp) / entry_price * 100, i + 1
            if high >= sl:
                return 'LOSS', (entry_price - sl) / entry_price * 100, i + 1

    # ไม่ถึง TP/SL ใน window
    final_close = future_candles.iloc[-1]['close']
    if direction == 'LONG':
        pnl = (final_close - entry_price) / entry_price * 100
    else:
        pnl = (entry_price - final_close) / entry_price * 100
    return 'NEUTRAL', pnl, len(future_candles)

def run_backtest() -> Dict:
    """รัน Backtest และคำนวณ Winrate"""
    console.print(Panel.fit(
        "[bold cyan]BACKTEST & WINRATE TESTER[/bold cyan]\n"
        f"Symbol: {SYMBOL} | Timeframe: {TIMEFRAME} | "
        f"Period: {BACKTEST_CANDLES} candles | Forward: {FORWARD_WINDOW} bars",
        border_style="cyan"
    ))
    console.print("")

    df = fetch_historical_data(SYMBOL, TIMEFRAME, BACKTEST_CANDLES)
    if df is None or len(df) < 100:
        console.print("[red]ไม่สามารถดึงข้อมูลได้ หรือข้อมูลไม่เพียงพอ[/red]")
        return {}

    console.print("[dim]กำลังคำนวณ Indicators...[/dim]")
    df = calculate_indicators(df)
    console.print(f"[green]✓ คำนวณ Indicators สำเร็จ ({len(df)} แท่ง)[/green]")
    console.print("")

    console.print(f"[dim]กำลัง Backtest... (อาจใช้เวลาสักครู่)[/dim]")
    results = []
    total_bars = len(df) - FORWARD_WINDOW - 50

    for i in range(50, total_bars):
        current = df.iloc[i]
        if pd.isna(current.get('rsi')) or pd.isna(current.get('atr')):
            continue
        if current.get('atr', 0) == 0:
            continue

        try:
            patterns = detect_candlestick_patterns(df.iloc[:i+1].copy())
        except Exception:
            continue

        signal = generate_signal(current, patterns)
        if signal == 'HOLD':
            continue

        entry = current['close']
        atr = current['atr']
        if signal == 'LONG':
            tp = entry + (atr * TP_ATR_MULTIPLIER)
            sl = entry - (atr * SL_ATR_MULTIPLIER)
        else:
            tp = entry - (atr * TP_ATR_MULTIPLIER)
            sl = entry + (atr * SL_ATR_MULTIPLIER)

        future = df.iloc[i+1:i+1+FORWARD_WINDOW]
        if len(future) < FORWARD_WINDOW:
            continue

        result, pnl, bars_held = check_trade_result(future, entry, signal, tp, sl)
        results.append({
            'timestamp': current['timestamp'],
            'signal': signal,
            'entry': entry,
            'tp': tp,
            'sl': sl,
            'result': result,
            'pnl_pct': pnl,
            'bars_held': bars_held,
        })

    if not results:
        console.print("[yellow]ไม่มีสัญญาณเทรดเกิดขึ้นในช่วงเวลาที่ทดสอบ[/yellow]")
        return {}

    df_res = pd.DataFrame(results)
    total_trades = len(df_res)
    wins = len(df_res[df_res['result'] == 'WIN'])
    losses = len(df_res[df_res['result'] == 'LOSS'])
    neutrals = len(df_res[df_res['result'] == 'NEUTRAL'])
    winrate = (wins / total_trades) * 100 if total_trades > 0 else 0

    long_trades = df_res[df_res['signal'] == 'LONG']
    short_trades = df_res[df_res['signal'] == 'SHORT']
    long_winrate = (len(long_trades[long_trades['result'] == 'WIN']) / len(long_trades) * 100) if len(long_trades) > 0 else 0
    short_winrate = (len(short_trades[short_trades['result'] == 'WIN']) / len(short_trades) * 100) if len(short_trades) > 0 else 0

    avg_win = df_res[df_res['result'] == 'WIN']['pnl_pct'].mean() if wins > 0 else 0
    avg_loss = df_res[df_res['result'] == 'LOSS']['pnl_pct'].mean() if losses > 0 else 0
    total_pnl = df_res['pnl_pct'].sum()
    avg_pnl = df_res['pnl_pct'].mean()
    profit_factor = (abs(avg_win * wins) / abs(avg_loss * losses)) if losses > 0 and avg_loss != 0 else 0

    display_results(
        total_trades=total_trades,
        wins=wins,
        losses=losses,
        neutrals=neutrals,
        winrate=winrate,
        long_count=len(long_trades),
        long_winrate=long_winrate,
        short_count=len(short_trades),
        short_winrate=short_winrate,
        avg_win=avg_win,
        avg_loss=avg_loss,
        total_pnl=total_pnl,
        avg_pnl=avg_pnl,
        profit_factor=profit_factor,
        df_res=df_res,
    )

    return {
        'total_trades': total_trades,
        'wins': wins,
        'losses': losses,
        'neutrals': neutrals,
        'winrate': winrate,
        'long_winrate': long_winrate,
        'short_winrate': short_winrate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'total_pnl': total_pnl,
        'profit_factor': profit_factor,
    }

def display_results(
    total_trades, wins, losses, neutrals, winrate,
    long_count, long_winrate, short_count, short_winrate,
    avg_win, avg_loss, total_pnl, avg_pnl, profit_factor,
    df_res,
):
    """แสดงผลลัพธ์ Backtest"""
    console.print("")
    console.print("=" * 60)
    console.print(f"[bold cyan]📊 BACKTEST RESULTS[/bold cyan]")
    console.print("=" * 60)

    # Table 1: Overall
    t1 = Table(title="[bold]Overall Performance[/bold]", box=box.ROUNDED, show_header=True)
    t1.add_column("Metric", style="cyan", width=25)
    t1.add_column("Value", style="white", justify="right", width=20)

    t1.add_row("Total Trades", str(total_trades))
    t1.add_row("Wins", f"[green]{wins}[/green]")
    t1.add_row("Losses", f"[red]{losses}[/red]")
    t1.add_row("Neutral (no TP/SL)", f"[yellow]{neutrals}[/yellow]")
    winrate_color = "green" if winrate >= 50 else "red"
    t1.add_row("Winrate", f"[bold {winrate_color}]{winrate:.2f}%[/bold {winrate_color}]")
    t1.add_row("Profit Factor", f"{profit_factor:.2f}")
    t1.add_row("Avg Win", f"[green]+{avg_win:.2f}%[/green]" if avg_win > 0 else f"{avg_win:.2f}%")
    t1.add_row("Avg Loss", f"[red]{avg_loss:.2f}%[/red]" if avg_loss < 0 else f"+{avg_loss:.2f}%")
    t1.add_row("Total P&L", f"[green]+{total_pnl:.2f}%[/green]" if total_pnl > 0 else f"[red]{total_pnl:.2f}%[/red]")
    t1.add_row("Avg P&L per Trade", f"[green]+{avg_pnl:.2f}%[/green]" if avg_pnl > 0 else f"[red]{avg_pnl:.2f}%[/red]")
    console.print(t1)
    console.print("")

    # Table 2: By Direction
    t2 = Table(title="[bold]Performance by Signal Type[/bold]", box=box.ROUNDED, show_header=True)
    t2.add_column("Signal", style="cyan", width=15)
    t2.add_column("Count", style="white", justify="right", width=10)
    t2.add_column("Winrate", style="white", justify="right", width=15)
    long_wr_color = "green" if long_winrate >= 50 else "red"
    short_wr_color = "green" if short_winrate >= 50 else "red"
    t2.add_row("LONG", str(long_count), f"[bold {long_wr_color}]{long_winrate:.2f}%[/bold {long_wr_color}]")
    t2.add_row("SHORT", str(short_count), f"[bold {short_wr_color}]{short_winrate:.2f}%[/bold {short_wr_color}]")
    console.print(t2)
    console.print("")

    # Table 3: Recent Trades
    t3 = Table(title="[bold]Last 10 Trades[/bold]", box=box.ROUNDED, show_header=True)
    t3.add_column("Time", style="dim", width=20)
    t3.add_column("Signal", style="cyan", width=8)
    t3.add_column("Entry", style="white", justify="right", width=12)
    t3.add_column("TP", style="green", justify="right", width=12)
    t3.add_column("SL", style="red", justify="right", width=12)
    t3.add_column("Result", style="white", width=10)
    t3.add_column("P&L %", style="white", justify="right", width=10)
    t3.add_column("Bars", style="dim", justify="right", width=6)

    for _, row in df_res.tail(10).iterrows():
        result_style = "green" if row['result'] == 'WIN' else "red" if row['result'] == 'LOSS' else "yellow"
        pnl_style = "green" if row['pnl_pct'] > 0 else "red" if row['pnl_pct'] < 0 else "yellow"
        t3.add_row(
            str(row['timestamp']),
            row['signal'],
            f"${row['entry']:.2f}",
            f"${row['tp']:.2f}",
            f"${row['sl']:.2f}",
            f"[{result_style}]{row['result']}[/{result_style}]",
            f"[{pnl_style}]{row['pnl_pct']:+.2f}%[/{pnl_style}]",
            str(row['bars_held']),
        )
    console.print(t3)
    console.print("")

    # Final Verdict
    console.print("=" * 60)
    if winrate >= 50 and profit_factor >= 1.5:
        console.print(f"[bold green]✅ GOOD STRATEGY[/bold green] - Winrate {winrate:.2f}% with PF {profit_factor:.2f}")
    elif winrate >= 40:
        console.print(f"[bold yellow]⚠️  MARGINAL STRATEGY[/bold yellow] - Winrate {winrate:.2f}% (need >50% for profitability with R:R 2:1)")
    else:
        console.print(f"[bold red]❌ POOR STRATEGY[/bold red] - Winrate {winrate:.2f}% is too low")
    console.print("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    try:
        run_backtest()
    except KeyboardInterrupt:
        console.print("\n[yellow]Backtest ถูกยกเลิกโดยผู้ใช้[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
