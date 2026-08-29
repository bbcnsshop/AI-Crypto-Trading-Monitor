"""AI Crypto Trading Monitor - Main Entry Point"""
import os, logging
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict
import ccxt, pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
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


def run_quick_backtest(symbol: str, timeframe: str, candles: int = 500) -> Optional[Dict]:
    """Run quick backtest on historical data and return summary"""
    try:
        from ta.momentum import RSIIndicator
        from ta.trend import MACD
        from ta.volatility import AverageTrueRange

        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=candles)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Calculate indicators
        rsi_ind = RSIIndicator(close=df['close'], window=14)
        df['rsi'] = rsi_ind.rsi()
        macd_ind = MACD(close=df['close'])
        df['macd_hist'] = macd_ind.macd_diff()
        atr_ind = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'])
        df['atr'] = atr_ind.average_true_range()

        # Generate signals
        signals = []
        for i in range(20, len(df) - 5):
            rsi = df['rsi'].iloc[i]
            macd = df['macd_hist'].iloc[i]
            atr = df['atr'].iloc[i]
            close = df['close'].iloc[i]

            tp = close + (atr * 2)
            sl = close - atr

            # Check next 5 bars
            won = False
            for j in range(1, 6):
                high = df['high'].iloc[i + j]
                low = df['low'].iloc[i + j]
                if high >= tp:
                    won = True
                    break
                if low <= sl:
                    break

            if rsi < 40 and macd > 0:
                signals.append({'type': 'LONG', 'won': won, 'pnl': 2.0 if won else -1.0})
            elif rsi > 60 and macd < 0:
                signals.append({'type': 'SHORT', 'won': won, 'pnl': 2.0 if won else -1.0})

        if not signals:
            return {
                'winrate': 0,
                'total_trades': 0,
                'profit_factor': 0,
                'total_pnl': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'long_winrate': 0,
                'short_winrate': 0,
                'period': f"{start_date} → {end_date}"
            }

        total = len(signals)
        wins = sum(1 for s in signals if s['won'])
        winrate = (wins / total) * 100
        longs = [s for s in signals if s['type'] == 'LONG']
        shorts = [s for s in signals if s['type'] == 'SHORT']
        long_wr = (sum(1 for s in longs if s['won']) / len(longs) * 100) if longs else 0
        short_wr = (sum(1 for s in shorts if s['won']) / len(shorts) * 100) if shorts else 0

        total_pnl = sum(s['pnl'] for s in signals)
        wins_pnl = sum(s['pnl'] for s in signals if s['won'])
        losses_pnl = sum(s['pnl'] for s in signals if not s['won'])
        profit_factor = abs(wins_pnl / losses_pnl) if losses_pnl != 0 else 0

        start_date = pd.to_datetime(df['timestamp'].iloc[0], unit='ms').strftime('%Y-%m-%d')
        end_date = pd.to_datetime(df['timestamp'].iloc[-1], unit='ms').strftime('%Y-%m-%d')

        return {
            'winrate': winrate,
            'total_trades': total,
            'profit_factor': profit_factor,
            'total_pnl': total_pnl,
            'avg_win': wins_pnl / wins if wins else 0,
            'avg_loss': losses_pnl / (total - wins) if total > wins else 0,
            'long_winrate': long_wr,
            'short_winrate': short_wr,
            'period': f"{start_date} → {end_date}"
        }
    except Exception as e:
        logging.error(f"Backtest error: {e}")
        return None


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
        self.backtest_result: Optional[Dict] = None  # Quick backtest summary

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
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=20),
            TaskProgressColumn(),
            TextColumn("[cyan]{task.fields[detail]}[/cyan]"),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        ) as progress:
            main_task = progress.add_task("[bold cyan]📊 กำลังวิเคราะห์[/bold cyan]", total=7, detail="เริ่มต้น...")

            exchange = ccxt.binance()
            ohlcv = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=CANDLE_LIMIT)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            data.df = df
            data.latest_close = df['close'].iloc[-1]
            progress.update(main_task, advance=1, detail=f"${data.latest_close:,.0f}")

            df = calculate_indicators(df)
            data.indicators = {
                'rsi': df['rsi'].iloc[-1] if 'rsi' in df else None,
                'macd_line': df['macd_line'].iloc[-1] if 'macd_line' in df else None,
                'macd_signal': df['macd_signal'].iloc[-1] if 'macd_signal' in df else None,
                'macd_hist': df['macd_hist'].iloc[-1] if 'macd_hist' in df else None,
                'atr': df['atr'].iloc[-1] if 'atr' in df else None,
                'ema20': df['ema20'].iloc[-1] if 'ema20' in df else None,
            }
            progress.update(main_task, advance=1, detail=f"RSI {data.indicators['rsi']:.0f}")

            data.patterns = detect_candlestick_patterns(df)
            bull = sum(1 for k, v in data.patterns.items() if v and 'bull' in k.lower())
            bear = sum(1 for k, v in data.patterns.items() if v and 'bear' in k.lower())
            progress.update(main_task, advance=1, detail=f"Bull:{bull} Bear:{bear}")

            sh, sl, _, _ = find_swing_high_low(df, SWING_LOOKBACK)
            data.fibonacci = calculate_fibonacci_levels(sh, sl)
            progress.update(main_task, advance=1, detail="Fib 61.8%")

            data.vpvr = calculate_vpvr(df, VPVR_BINS)
            progress.update(main_task, advance=1, detail=f"POC ${data.vpvr.get('poc', 0):,.0f}")

            should_send, reason, trigger_type = check_trigger(data, df, _cooldown_tracker)
            if should_send:
                data.ai_analysis = call_openrouter_ai(build_ai_context(data))
                _cooldown_tracker.record_send()
                progress.update(main_task, advance=1, detail=f"AI {trigger_type}")
            else:
                data.ai_analysis = f"[AI Skipped: {reason}]"
                progress.update(main_task, advance=1, detail="Skipped")

            progress.update(main_task, advance=1, detail="Rendering...")
            data.backtest_result = run_quick_backtest(SYMBOL, TIMEFRAME, candles=100)
            progress.update(main_task, advance=1, detail="[green]✓ เสร็จสิ้น[/green]")

        # แสดงผลหลัง progress เสร็จ
        console.print("")  # Newline after progress bar
        display_rich_ui_new(data, SYMBOL, TIMEFRAME, DISPLAY_MODE)

    except Exception as e:
        logging.error(f"Error: {e}")
        console.print(f"[red]Error: {e}[/red]")
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
