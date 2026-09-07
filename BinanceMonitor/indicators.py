"""
Indicators Module for AI Crypto Trading Monitor
==============================================
รวมฟังก์ชันคำนวณ Indicators, Fibonacci, VPVR ไว้ที่นี่
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional


# ============================================================
# Swing High/Low Detection
# ============================================================
def find_swing_high_low(df: pd.DataFrame, lookback: int = 5) -> Tuple[float, float, int, int]:
    """
    หา Swing High และ Swing Low จาก OHLCV DataFrame
    Returns: (swing_high, swing_low, sh_idx, sl_idx)
    """
    if df is None or len(df) < lookback * 2:
        return 0, 0, 0, 0
    
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    
    # Find Swing High (highest point in lookback window)
    sh_idx = lookback
    for i in range(lookback, n - lookback):
        if high[i] >= max(high[i - lookback:i + lookback + 1]):
            sh_idx = i
    
    # Find Swing Low (lowest point in lookback window)
    sl_idx = lookback
    for i in range(lookback, n - lookback):
        if low[i] <= min(low[i - lookback:i + lookback + 1]):
            sl_idx = i
    
    return high[sh_idx], low[sl_idx], sh_idx, sl_idx


# ============================================================
# Calculate Indicators
# ============================================================
def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    คำนวณ Indicators ทั้งหมด: RSI, MACD, ATR, EMA
    """
    df = df.copy()
    
    # RSI (14 periods)
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD (12, 26, 9)
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd_line'] = ema12 - ema26
    df['macd_signal'] = df['macd_line'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd_line'] - df['macd_signal']
    
    # ATR (14 periods)
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = tr.rolling(window=14).mean()
    
    # EMA 20
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    
    return df


# ============================================================
# Fibonacci Levels
# ============================================================
def calculate_fibonacci_levels(swing_high: float, swing_low: float) -> dict:
    """
    คำนวณ Fibonacci Retracement และ Extension Levels
    """
    if swing_high <= 0 or swing_low <= 0 or swing_high <= swing_low:
        return {}
    
    diff = swing_high - swing_low
    
    fib_levels = {
        'fib_382': swing_high - diff * 0.382,
        'fib_500': swing_high - diff * 0.500,
        'fib_618': swing_high - diff * 0.618,
        'fib_786': swing_high - diff * 0.786,
    }
    
    # Extension levels (สำหรับ TP)
    ext_levels = {
        'ext_1272': swing_high + diff * 1.272,
        'ext_1618': swing_high + diff * 1.618,
    }
    
    return {**fib_levels, **ext_levels}


# ============================================================
# Volume Profile (VPVR)
# ============================================================
def calculate_vpvr(df: pd.DataFrame, bins: int = 50) -> dict:
    """
    คำนวณ Volume Profile Visible Range (VPVR)
    Returns: POC, VAH, VAL
    """
    if df is None or len(df) < 2:
        return {}
    
    try:
        close_prices = df['close'].values
        volumes = df['volume'].values
        
        price_min = close_prices.min()
        price_max = close_prices.max()
        
        if price_max <= price_min:
            return {}
        
        bin_edges = np.linspace(price_min, price_max, bins + 1)
        bin_volumes = np.zeros(bins)
        
        for i in range(len(close_prices)):
            price = close_prices[i]
            vol = volumes[i]
            bin_idx = int((price - price_min) / (price_max - price_min) * bins)
            bin_idx = min(bin_idx, bins - 1)
            bin_volumes[bin_idx] += vol
        
        # POC (Point of Control) - bin ที่มี volume สูงสุด
        poc_idx = np.argmax(bin_volumes)
        poc = (bin_edges[poc_idx] + bin_edges[poc_idx + 1]) / 2
        
        # Value Area (70%)
        total_volume = bin_volumes.sum()
        target_volume = total_volume * 0.70
        
        cumsum = 0
        vah_idx = poc_idx
        val_idx = poc_idx
        
        # Expand outward from POC
        for i in range(bins):
            # Expand up
            if poc_idx + i < bins:
                cumsum += bin_volumes[poc_idx + i]
                if cumsum <= target_volume:
                    vah_idx = poc_idx + i
            
            # Expand down
            if poc_idx - i >= 0:
                cumsum += bin_volumes[poc_idx - i]
                if cumsum <= target_volume:
                    val_idx = poc_idx - i
        
        vah = (bin_edges[vah_idx] + bin_edges[vah_idx + 1]) / 2
        val = (bin_edges[val_idx] + bin_edges[val_idx + 1]) / 2
        
        return {
            'poc': poc,
            'vah': vah,
            'val': val,
        }
    except Exception:
        return {}
