"""
Display Module for AI Crypto Trading Monitor
============================================
แสดงผลลัพธ์การวิเคราะห์แบบ Rich UI พร้อมคำอธิบายความหมายของแต่ละค่า

3 รูปแบบ:
1. Standard (default) - แบบเดิมที่เป็นอยู่
2. Compact - แบบย่อ เห็นข้อมูลสำคัญเร็วๆ
3. Verbose - แบบเต็ม มีคำอธิบายความหมายใต้ตาราง
"""

from typing import Dict, Optional
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.columns import Columns
from rich.text import Text

console = Console()


# ============================================================
# Knowledge Base - ความหมายของค่าต่างๆ
# ============================================================
INDICATOR_DEFINITIONS = {
    'rsi': {
        'name': 'RSI (Relative Strength Index)',
        'what': 'ดัชนีวัดโมเมนตัม 0-100 บอกว่าราคาขึ้นหรือลงแรงแค่ไหน',
        'how': 'คำนวณจากการเปรียบเทียบการขึ้น/ลงเฉลี่ย 14 แท่ง',
        'ranges': [
            ('0-30', '🟢 Oversold - ขายมากเกินไป แนวโน้มกลับตัวขึ้น', 'bullish'),
            ('30-70', '⚪ Neutral - โมเมนตัมปกติ ไม่มีสัญญาณชัด', 'neutral'),
            ('70-100', '🔴 Overbought - ซื้อมากเกินไป แนวโน้มกลับตัวลง', 'bearish'),
        ],
    },
    'macd': {
        'name': 'MACD (Moving Average Convergence Divergence)',
        'what': 'ดูความสัมพันธ์ของ EMA 12 และ EMA 26 บอกทิศทางและแรงของเทรนด์',
        'how': 'MACD Line = EMA12 - EMA26, Signal Line = EMA9 ของ MACD, Histogram = MACD - Signal',
        'ranges': [
            ('MACD > 0 & Hist > 0', '🟢 Bullish Momentum - แรงซื้อเพิ่ม แนวโน้มขาขึ้น', 'bullish'),
            ('MACD < 0 & Hist < 0', '🔴 Bearish Momentum - แรงขายเพิ่ม แนวโน้มขาลง', 'bearish'),
            ('Histogram ตัด 0 ขึ้น', '🟢 Bullish Crossover - สัญญาณซื้อ', 'bullish'),
            ('Histogram ตัด 0 ลง', '🔴 Bearish Crossover - สัญญาณขาย', 'bearish'),
        ],
    },
    'atr': {
        'name': 'ATR (Average True Range)',
        'what': 'วัดความผันผวนเฉลี่ย ใช้กำหนดขนาด SL/TP ที่เหมาะสม',
        'how': 'คำนวณจากช่วง High-Low เฉลี่ย 14 แท่ง',
        'ranges': [
            ('ATR สูง', '📊 High Volatility - ตลาดผันผวน SL ควรกว้าง', 'info'),
            ('ATR ต่ำ', '📊 Low Volatility - ตลาดนิ่ง SL แคบได้', 'info'),
        ],
    },
    'ema': {
        'name': 'EMA 20 (Exponential Moving Average)',
        'what': 'ค่าเฉลี่ยเคลื่อนที่ถ่วงน้ำหนัก 20 แท่ง ใช้ดูเทรนด์ระยะสั้น',
        'how': 'ให้น้ำหนักราคาล่าสุดมากกว่าราคาเก่า',
        'ranges': [
            ('Price > EMA20', '🟢 Uptrend - ราคาเหนือ EMA ยืนยันเทรนด์ขาขึ้น', 'bullish'),
            ('Price < EMA20', '🔴 Downtrend - ราคาใต้ EMA ยืนยันเทรนด์ขาลง', 'bearish'),
            ('Price ≈ EMA20', '⚪ Sideways - ราคาอยู่ใกล้ EMA ไม่มีเทรนด์ชัด', 'neutral'),
        ],
    },
    'fibonacci': {
        'name': 'Fibonacci Retracement',
        'what': 'ระดับราคาที่คาดว่าจะมีแรงซื้อ/ขายกลับ จากสัดส่วนทองคำ 23.6%, 38.2%, 50%, 61.8%, 78.6%',
        'how': 'คำนวณจาก Swing High - Swing Low แล้วหาระดับย้อนกลับ',
        'ranges': [
            ('Fib 0.382', '🟢 Strong Support/Resistance - แนวรับ/ต้านที่แข็งแรง', 'bullish'),
            ('Fib 0.500', '🟢 Medium Support/Resistance - แนวรับ/ต้านปานกลาง', 'neutral'),
            ('Fib 0.618', '🟢 Golden Ratio - แนวรับ/ต้านทองคำ สำคัญที่สุด', 'bullish'),
        ],
    },
    'vpvr': {
        'name': 'VPVR (Volume Profile Visible Range)',
        'what': 'แสดงปริมาณการซื้อขายในแต่ละระดับราคา หาจุดที่มี Volume สูงสุด',
        'how': 'แบ่งช่วงราคาเป็น 50 bins แล้วนับ Volume ในแต่ละช่วง',
        'ranges': [
            ('POC (Point of Control)', '📊 ราคาที่มี Volume สูงสุด - แนวรับ/ต้านสำคัญ', 'info'),
            ('VAH (Value Area High)', '📊 ขอบบน Value Area 70% - แนวต้าน', 'info'),
            ('VAL (Value Area Low)', '📊 ขอบล่าง Value Area 70% - แนวรับ', 'info'),
        ],
    },
    'patterns': {
        'name': 'Candlestick Patterns',
        'what': 'รูปแบบแท่งเทียนที่บอก sentiment ของตลาด 11 แบบ',
        'how': 'วิเคราะห์จาก Body, Wick, Position ของแท่งเทียนล่าสุด',
        'ranges': [
            ('Bullish (Engulfing, Hammer, Piercing)', '🟢 สัญญาณกลับตัวขึ้น แนวโน้มขาขึ้น', 'bullish'),
            ('Bearish (Engulfing, Shooting Star, Dark Cloud)', '🔴 สัญญาณกลับตัวลง แนวโน้มขาลง', 'bearish'),
            ('Doji', '⚪ Indecision - ตลาดลังเล รอสัญญาณยืนยัน', 'neutral'),
        ],
    },
}


def _get_rsi_signal(rsi: float) -> str:
    if rsi is None: return "N/A"
    if rsi > 70: return "Overbought"
    if rsi < 30: return "Oversold"
    return "Neutral"


def _get_macd_signal(macd_hist: float) -> str:
    if macd_hist is None: return "N/A"
    if macd_hist > 0: return "Bullish"
    if macd_hist < 0: return "Bearish"
    return "Neutral"


def _get_ema_signal(close: float, ema20: float) -> str:
    if close is None or ema20 is None or ema20 == 0: return "N/A"
    diff = (close - ema20) / ema20 * 100
    if diff > 0.5: return "Uptrend"
    if diff < -0.5: return "Downtrend"
    return "Sideways"


def _format_signal(signal: str) -> str:
    if signal in ("Overbought", "Bearish", "Downtrend"):
        return f"[red]{signal}[/red]"
    if signal in ("Oversold", "Bullish", "Uptrend"):
        return f"[green]{signal}[/green]"
    return f"[yellow]{signal}[/yellow]"


def _format_value(key: str, value) -> str:
    if value is None:
        return "N/A"
    if key == 'price':
        return f"${value:,.2f}"
    if key == 'rsi':
        return f"{value:.2f}"
    if key in ('macd_hist', 'atr'):
        return f"{value:.4f}"
    if key == 'ema20':
        return f"${value:,.2f}"
    if key in ('fib', 'poc', 'vah', 'val'):
        return f"${value:,.2f}"
    return str(value)


def display_rich_ui(data, symbol: str, timeframe: str, mode: str = "standard"):
    """แสดงผล Rich UI - mode: 'standard' | 'compact' | 'verbose'"""
    if mode == "compact":
        return _display_compact(data, symbol, timeframe)
    elif mode == "verbose":
        return _display_verbose(data, symbol, timeframe)
    else:
        return _display_standard(data, symbol, timeframe)


def _display_standard(data, symbol: str, timeframe: str):
    """Standard Mode - แบบเดิม (backward compatible)"""
    console.clear()
    console.print(Panel.fit(
        f"[bold cyan]AI CRYPTO TRADING MONITOR[/bold cyan] | {symbol} {timeframe}",
        border_style="cyan"
    ))
    console.print("")

    indicators = data.indicators
    fibonacci = data.fibonacci or {}
    vpvr_data = data.vpvr or {}

    table1 = Table(title="[bold]Market & Indicators[/bold]", box=box.ROUNDED)
    table1.add_column("Metric", style="cyan", width=20)
    table1.add_column("Value", style="white", width=15, justify="right")
    table1.add_column("Signal", style="white", width=15, justify="center")

    rsi = indicators.get('rsi', 0) or 0
    macd_hist = indicators.get('macd_hist', 0) or 0
    close = data.latest_close or 0
    ema20 = indicators.get('ema20', 0) or 0
    rsi_sig = _get_rsi_signal(rsi)
    macd_sig = _get_macd_signal(macd_hist)
    ema_sig = _get_ema_signal(close, ema20)

    table1.add_row("Price", _format_value('price', close), "-")
    table1.add_row("RSI (14)", _format_value('rsi', rsi), _format_signal(rsi_sig))
    table1.add_row("MACD Hist", _format_value('macd_hist', macd_hist), _format_signal(macd_sig))
    table1.add_row("ATR (14)", _format_value('atr', indicators.get('atr')), "-")
    table1.add_row("EMA 20", _format_value('ema20', ema20), _format_signal(ema_sig))
    console.print(table1)
    console.print("")

    table2 = Table(title="[bold]Key Levels (Fibonacci & VPVR)[/bold]", box=box.ROUNDED)
    table2.add_column("Level", style="cyan", width=15)
    table2.add_column("Price", style="white", width=15, justify="right")
    table2.add_column("Distance %", style="yellow", width=15, justify="right")

    if fibonacci:
        for key, label in [('fib_382', 'Fib 0.382'), ('fib_500', 'Fib 0.500'), ('fib_618', 'Fib 0.618')]:
            val = fibonacci.get(key)
            if val and close:
                dist = ((val - close) / close) * 100
                table2.add_row(label, _format_value('fib', val), f"{dist:+.2f}%")
    if vpvr_data:
        for key, label in [('poc', 'POC'), ('vah', 'VAH'), ('val', 'VAL')]:
            val = vpvr_data.get(key)
            if val and close:
                dist = ((val - close) / close) * 100
                table2.add_row(label, _format_value(key, val), f"{dist:+.2f}%")
    console.print(table2)
    console.print("")

    # 11 Candlestick Patterns
    patterns_list = [
        # Bullish (ขาขึ้น)
        ('bullish_engulfing', 'Bullish Engulfing', 'green'),
        ('hammer', 'Hammer', 'green'),
        ('bullish_pin_bar', 'Bullish Pin Bar', 'green'),
        ('piercing_line', 'Piercing Line', 'green'),
        # Bearish (ขาลง)
        ('bearish_engulfing', 'Bearish Engulfing', 'red'),
        ('bearish_pin_bar', 'Bearish Pin Bar', 'red'),
        ('shooting_star', 'Shooting Star', 'red'),
        ('hanging_man', 'Hanging Man', 'red'),
        ('dark_cloud_cover', 'Dark Cloud Cover', 'red'),
        # Neutral
        ('doji', 'Doji', 'yellow'),
        ('inverted_hammer', 'Inverted Hammer', 'yellow'),
    ]

    table3 = Table(title="[bold]Candlestick Patterns (11)[/bold]", box=box.ROUNDED)
    table3.add_column("Pattern", style="cyan", width=25)
    table3.add_column("Status", style="white", width=15, justify="center")
    for k, label, _ in patterns_list:
        if k in data.patterns:
            status = "[green]DETECTED[/green]" if data.patterns[k] else "[dim]None[/dim]"
            table3.add_row(label, status)
    console.print(table3)
    console.print("")

    if data.ai_analysis:
        console.print(Panel.fit(
            data.ai_analysis,
            title="[bold cyan]AI Analysis & Trading Plan[/bold cyan]",
            border_style="green", padding=(1, 2)
        ))
    console.print(f"[dim]Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")


def _display_compact(data, symbol: str, timeframe: str):
    """Compact Mode - แบบย่อ เห็นเร็วๆ"""
    console.clear()
    console.print(Panel.fit(
        f"[bold cyan]AI CRYPTO TRADING MONITOR[/bold cyan] | {symbol} {timeframe} | COMPACT",
        border_style="cyan"
    ))
    indicators = data.indicators
    close = data.latest_close or 0
    rsi = indicators.get('rsi', 0) or 0
    macd_hist = indicators.get('macd_hist', 0) or 0
    ema20 = indicators.get('ema20', 0) or 0

    rsi_sig = _get_rsi_signal(rsi)
    macd_sig = _get_macd_signal(macd_hist)
    ema_sig = _get_ema_signal(close, ema20)
    summary = (
        f"Price: [bold]${close:,.2f}[/bold] | "
        f"RSI: [bold]{rsi:.1f}[/bold] ({_format_signal(rsi_sig)}) | "
        f"MACD: [bold]{macd_hist:+.1f}[/bold] ({_format_signal(macd_sig)}) | "
        f"EMA20: [bold]${ema20:,.0f}[/bold] ({_format_signal(ema_sig)})"
    )
    console.print(Panel(summary, border_style="yellow"))

    fib = data.fibonacci or {}
    vpvr = data.vpvr or {}
    if fib or vpvr:
        parts = []
        for key, label in [('fib_618', 'Fib 0.618'), ('poc', 'POC'), ('vah', 'VAH'), ('val', 'VAL')]:
            val = (fib.get(key) or vpvr.get(key))
            if val:
                parts.append(f"{label}: ${val:,.0f}")
        if parts:
            console.print(Panel(" | ".join(parts), title="[cyan]Key Levels[/cyan]", border_style="blue"))

    if data.patterns:
        bull = sum(1 for k, v in data.patterns.items() if v and 'bull' in k.lower())
        bear = sum(1 for k, v in data.patterns.items() if v and 'bear' in k.lower())
        pat_color = "green" if bull > bear else "red" if bear > bull else "yellow"
        console.print(Panel(
            f"Bullish: [green]{bull}[/green] | Bearish: [red]{bear}[/red]",
            title=f"[{pat_color}]Patterns[/{pat_color}]",
            border_style=pat_color,
        ))

    if data.ai_analysis:
        console.print(Panel.fit(
            data.ai_analysis,
            title="[bold cyan]AI Analysis[/bold cyan]",
            border_style="green", padding=(1, 2)
        ))
    console.print(f"[dim]Updated: {datetime.now().strftime('%H:%M:%S')}[/dim]")


def _print_def_box(name: str, definition: dict, *values):
    """Print definition panel for an indicator"""
    parts = [f"[bold cyan]{name}[/bold cyan]"]
    parts.append(f"[dim]{definition['what']}[/dim]")
    parts.append("")
    parts.append(f"[yellow]วิธีคำนวณ:[/yellow] {definition['how']}")
    parts.append("")
    parts.append("[yellow]ช่วงค่าที่สำคัญ:[/yellow]")

    for range_val, meaning, _ in definition.get('ranges', []):
        parts.append(f"  • {range_val}: {meaning}")

    console.print(Panel("\n".join(parts), title=f"[dim]💡 {name} คืออะไร?[/dim]", border_style="dim"))


def display_rich_ui_original(data, symbol: str, timeframe: str):
    """Wrapper for backward compatibility"""
    return _display_standard(data, symbol, timeframe)


def _display_verbose(data, symbol: str, timeframe: str):
    """Verbose Mode - แบบเต็ม มีคำอธิบายใต้ตาราง"""
    console.clear()
    console.print(Panel.fit(
        f"[bold cyan]AI CRYPTO TRADING MONITOR[/bold cyan] | {symbol} {timeframe} | VERBOSE",
        border_style="cyan"
    ))
    console.print("")

    indicators = data.indicators
    fibonacci = data.fibonacci or {}
    vpvr_data = data.vpvr or {}
    close = data.latest_close or 0
    rsi = indicators.get('rsi', 0) or 0
    macd_hist = indicators.get('macd_hist', 0) or 0
    ema20 = indicators.get('ema20', 0) or 0
    atr = indicators.get('atr', 0) or 0

    # Table 1: Indicators
    table1 = Table(title="[bold cyan]📊 Market & Indicators[/bold cyan]", box=box.ROUNDED)
    table1.add_column("Metric", style="cyan", width=18)
    table1.add_column("Value", style="white", width=12, justify="right")
    table1.add_column("Signal", style="white", width=15, justify="center")
    table1.add_column("สถานะ", style="yellow", width=15)

    rsi_sig = _get_rsi_signal(rsi)
    macd_sig = _get_macd_signal(macd_hist)
    ema_sig = _get_ema_signal(close, ema20)
    rsi_status = "💪 แรงซื้อมาก" if rsi < 30 else "💪 แรงขายมาก" if rsi > 70 else "⚖️ สมดุล"
    macd_status = "📈 Momentum ขึ้น" if macd_hist > 0 else "📉 Momentum ลง"
    ema_status = "เหนือเส้น" if close > ema20 else "ใต้เส้น"
    atr_pct_str = f"{atr/close*100:.1f}% ความผันผวน" if close and close > 0 else "-"

    table1.add_row("💰 Price", _format_value('price', close), "-", "-")
    table1.add_row("📈 RSI (14)", _format_value('rsi', rsi), _format_signal(rsi_sig), rsi_status)
    table1.add_row("📉 MACD Hist", _format_value('macd_hist', macd_hist), _format_signal(macd_sig), macd_status)
    table1.add_row("📊 ATR (14)", _format_value('atr', atr), "-", atr_pct_str)
    table1.add_row("📍 EMA 20", _format_value('ema20', ema20), _format_signal(ema_sig), ema_status)
    console.print(table1)

    # Definition boxes for indicators
    console.print("")
    _print_def_box("RSI", INDICATOR_DEFINITIONS['rsi'], rsi)
    _print_def_box("MACD", INDICATOR_DEFINITIONS['macd'], macd_hist)
    _print_def_box("ATR", INDICATOR_DEFINITIONS['atr'], atr)
    _print_def_box("EMA", INDICATOR_DEFINITIONS['ema'], close, ema20)
    console.print("")

    # Table 2: Key Levels
    table2 = Table(title="[bold cyan]🎯 Key Levels (Fibonacci & VPVR)[/bold cyan]", box=box.ROUNDED)
    table2.add_column("Level", style="cyan", width=15)
    table2.add_column("Price", style="white", width=15, justify="right")
    table2.add_column("Distance %", style="yellow", width=12, justify="right")
    table2.add_column("ความหมาย", style="dim", width=20)

    level_defs = {
        'fib_382': ('Fib 0.382', 'แนวรับ/ต้านแรง'),
        'fib_500': ('Fib 0.500', 'แนวรับ/ต้านกลาง'),
        'fib_618': ('Fib 0.618', 'แนวรับ/ต้านทองคำ'),
        'poc': ('POC', 'จุดควบคุมราคา'),
        'vah': ('VAH', 'ขอบบน Value Area'),
        'val': ('VAL', 'ขอบล่าง Value Area'),
    }

    all_levels = {}
    if fibonacci:
        all_levels.update(fibonacci)
    if vpvr_data:
        all_levels.update(vpvr_data)

    for key in ['fib_382', 'fib_500', 'fib_618', 'poc', 'vah', 'val']:
        val = all_levels.get(key)
        label, meaning = level_defs.get(key, (key, ''))
        if val and close:
            dist = ((val - close) / close) * 100
            dist_str = f"{dist:+.2f}%" if dist >= 0 else f"{dist:.2f}%"
            above = "[green]▲ เหนือราคา[/green]" if dist > 0 else "[red]▼ ใต้ราคา[/red]"
            table2.add_row(label, _format_value('fib', val), dist_str, f"{meaning} | {above}")
    console.print(table2)

    # Definition boxes for levels
    console.print("")
    _print_def_box("Fibonacci", INDICATOR_DEFINITIONS['fibonacci'])
    _print_def_box("VPVR", INDICATOR_DEFINITIONS['vpvr'])
    console.print("")

    # Table 3: Patterns
    table3 = Table(title="[bold cyan]🕯️ Candlestick Patterns[/bold cyan]", box=box.ROUNDED)
    table3.add_column("Pattern", style="cyan", width=25)
    table3.add_column("Status", style="white", width=12, justify="center")
    table3.add_column("ความหมาย", style="dim", width=30)

    pattern_meanings = {
        'bullish_engulfing': 'กลืนขาขึ้น - แรงซื้อเหนือแรงขาย',
        'bearish_engulfing': 'กลืนขาลง - แรงขายเหนือแรงซื้อ',
        'bullish_pin_bar': 'Pin Bar ขาขึ้น - ราคากลับตัวขึ้น',
        'bearish_pin_bar': 'Pin Bar ขาลง - ราคากลับตัวลง',
        'doji': 'Doji - ตลาดลังเล ไม่แน่ใจ',
        'hammer': 'Hammer - สัญญาณกลับตัวขึ้น',
        'inverted_hammer': 'Inverted Hammer - อาจกลับตัวขึ้น',
        'shooting_star': 'Shooting Star - สัญญาณกลับตัวลง',
        'hanging_man': 'Hanging Man - สัญญาณเตือนขาลง',
        'piercing_line': 'Piercing Line - การกลับตัวขึ้น',
        'dark_cloud_cover': 'Dark Cloud Cover - การกลับตัวลง',
    }

    for k, meaning in pattern_meanings.items():
        if k in data.patterns:
            status = "[green]✅ DETECTED[/green]" if data.patterns[k] else "[dim]⬜ None[/dim]"
            table3.add_row(k.replace('_', ' ').title(), status, meaning)
    console.print(table3)

    # Definition box for patterns
    console.print("")
    _print_def_box("Patterns", INDICATOR_DEFINITIONS['patterns'])
    console.print("")

    # AI Analysis
    if data.ai_analysis:
        console.print(Panel.fit(
            data.ai_analysis,
            title="[bold cyan]🤖 AI Analysis & Trading Plan[/bold cyan]",
            border_style="green", padding=(1, 2)
        ))

    console.print(f"[dim]Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")


# ============================================================
# Backward Compatibility
# ============================================================
def display_rich_ui_original(data, symbol: str, timeframe: str):
    """Wrapper สำหรับ backward compatibility - เรียกใช้แบบเดิมได้"""
    return _display_standard(data, symbol, timeframe)

    console.print(f"[dim]Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
