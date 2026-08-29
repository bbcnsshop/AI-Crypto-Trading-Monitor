"""
AI Trigger Module
================
Smart Trigger + Cooldown System
ตรวจสอบว่าควรส่ง AI หรือไม่ (ประหยัด API)
"""

import time as time_module
from config import (
    TRIGGER_RSI_EXTREME, TRIGGER_PATTERN, TRIGGER_MACD_CROSS,
    TRIGGER_NEAR_LEVEL, TRIGGER_HIGH_VOLATILITY, TRIGGER_BIG_MOVE,
    RSI_OVERSOLD, RSI_OVERBOUGHT, ATR_HIGH_PCT,
    LEVEL_DISTANCE_PCT, BIG_MOVE_PCT,
    AI_COOLDOWN_MAX_PER_HOUR, AI_COOLDOWN_SECONDS
)


# ============================================================
# Cooldown Tracker
# ============================================================
class CooldownTracker:
    """Track AI calls for cooldown"""
    
    def __init__(self):
        self.last_ai_time = 0
        self.ai_count_this_hour = 0
        self.hour_start = time_module.time()
    
    def can_send(self) -> tuple:
        current = time_module.time()
        if current - self.hour_start >= 3600:
            self.ai_count_this_hour = 0
            self.hour_start = current
        time_since_last = current - self.last_ai_time
        if self.last_ai_time > 0 and time_since_last < AI_COOLDOWN_SECONDS:
            remaining = int(AI_COOLDOWN_SECONDS - time_since_last)
            return False, f"Cooldown ({remaining}s remaining)"
        if self.ai_count_this_hour >= AI_COOLDOWN_MAX_PER_HOUR:
            return False, f"Hourly limit ({self.ai_count_this_hour}/{AI_COOLDOWN_MAX_PER_HOUR})"
        return True, "OK"
    
    def record_send(self):
        self.last_ai_time = time_module.time()
        self.ai_count_this_hour += 1
    
    def get_status(self) -> str:
        current = time_module.time()
        if current - self.hour_start >= 3600:
            self.ai_count_this_hour = 0
            self.hour_start = current
        if self.last_ai_time > 0:
            time_since_last = current - self.last_ai_time
            if time_since_last < AI_COOLDOWN_SECONDS:
                remaining = int(AI_COOLDOWN_SECONDS - time_since_last)
                return f"Cooldown: {remaining}s | Used: {self.ai_count_this_hour}/{AI_COOLDOWN_MAX_PER_HOUR}"
        return f"OK | Used: {self.ai_count_this_hour}/{AI_COOLDOWN_MAX_PER_HOUR}"


# ============================================================
# Smart Trigger Check
# ============================================================
def check_smart_trigger(data, df) -> tuple:
    reasons = []
    indicators = data.indicators
    close = data.latest_close
    
    # 1. RSI Extreme
    if TRIGGER_RSI_EXTREME:
        rsi = indicators.get('rsi', 50)
        if rsi < RSI_OVERSOLD:
            reasons.append(f"RSI Oversold ({rsi:.1f} < {RSI_OVERSOLD})")
        elif rsi > RSI_OVERBOUGHT:
            reasons.append(f"RSI Overbought ({rsi:.1f} > {RSI_OVERBOUGHT})")
    
    # 2. Pattern Detected
    if TRIGGER_PATTERN and data.patterns:
        bull = sum(1 for k, v in data.patterns.items() if v and 'bull' in k.lower())
        bear = sum(1 for k, v in data.patterns.items() if v and 'bear' in k.lower())
        if bull > 0:
            reasons.append(f"Bullish Pattern ({bull} detected)")
        if bear > 0:
            reasons.append(f"Bearish Pattern ({bear} detected)")
    
    # 3. MACD Crossover
    if TRIGGER_MACD_CROSS:
        macd_line = indicators.get('macd_line', 0)
        macd_signal = indicators.get('macd_signal', 0)
        if len(df) >= 2:
            prev_macd = df['macd_line'].iloc[-2] if 'macd_line' in df else 0
            prev_sig = df['macd_signal'].iloc[-2] if 'macd_signal' in df else 0
            if prev_macd <= prev_sig and macd_line > macd_signal:
                reasons.append("MACD Bullish Crossover")
            elif prev_macd >= prev_sig and macd_line < macd_signal:
                reasons.append("MACD Bearish Crossover")
    
    # 4. Near Key Level
    if TRIGGER_NEAR_LEVEL and close:
        all_levels = []
        if data.fibonacci:
            for k in ['fib_382', 'fib_500', 'fib_618']:
                if k in data.fibonacci:
                    all_levels.append(data.fibonacci[k])
        if data.vpvr:
            for k in ['poc', 'vah', 'val']:
                if k in data.vpvr:
                    all_levels.append(data.vpvr[k])
        for level in all_levels:
            dist = abs(close - level) / close * 100
            if dist < LEVEL_DISTANCE_PCT:
                reasons.append(f"Near Key Level (${level:.0f}, {dist:.2f}%)")
                break
    
    # 5. High Volatility
    if TRIGGER_HIGH_VOLATILITY:
        atr = indicators.get('atr', 0)
        if atr > 0 and close > 0:
            atr_pct = atr / close * 100
            if atr_pct > ATR_HIGH_PCT:
                reasons.append(f"High Volatility (ATR {atr_pct:.2f}% > {ATR_HIGH_PCT}%)")
    
    # 6. Big Move
    if TRIGGER_BIG_MOVE and len(df) >= 2:
        prev_close = df['close'].iloc[-2]
        change = abs(close - prev_close) / prev_close * 100
        if change > BIG_MOVE_PCT:
            reasons.append(f"Big Move ({change:.2f}% change)")
    
    should_trigger = len(reasons) > 0
    reason_str = " | ".join(reasons) if reasons else "No trigger"
    return should_trigger, reason_str


def should_send_ai(data, df, cooldown_tracker: CooldownTracker) -> tuple:
    can_send, cooldown_reason = cooldown_tracker.can_send()
    if not can_send:
        return False, cooldown_reason, "COOLDOWN"
    should_trigger, trigger_reason = check_smart_trigger(data, df)
    if should_trigger:
        return True, trigger_reason, "SMART_TRIGGER"
    return False, "No trigger conditions", "NONE"
