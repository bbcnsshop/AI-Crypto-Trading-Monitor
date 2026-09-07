"""
Candlestick Pattern Library
===========================
Custom library for detecting 11 candlestick patterns (Bullish/Bearish/Neutral)
"""
from typing import Dict, Any, Tuple
import pandas as pd

# Constants
DOJI_BODY = 0.1
PIN_RATIO = 2.0
HAMMER_WICK = 0.5
HAMMER_POS = 0.6
SHOOT_POS = 0.4
UPPER_MAX = 0.15


def _geom(o, c, h, l):
    b = abs(c - o)
    r = max(h - l, 1e-10)
    u = h - max(o, c)
    lo = min(o, c) - l
    return {'body': b, 'range': r, 'uw': u, 'lw': lo, 'pos': (max(o, c) - l) / r}


def _down(df):
    if df is None or len(df) < 2:
        return True
    return float(df['close'].iloc[-1]) < (float(df['open'].iloc[-2]) + float(df['close'].iloc[-2])) / 2


def _up(df):
    if df is None or len(df) < 2:
        return False
    return float(df['close'].iloc[-1]) > (float(df['open'].iloc[-2]) + float(df['close'].iloc[-2])) / 2


def detect_engulfing(df):
    """Bullish/Bearish Engulfing"""
    r = {'bullish_engulfing': False, 'bearish_engulfing': False}
    if df is None or len(df) < 2:
        return r
    co, cc = float(df['open'].iloc[-1]), float(df['close'].iloc[-1])
    po, pc = float(df['open'].iloc[-2]), float(df['close'].iloc[-2])
    if cc > co and pc < po and co <= pc and cc >= po:
        r['bullish_engulfing'] = True
    if cc < co and pc > po and co >= pc and cc <= po:
        r['bearish_engulfing'] = True
    return r


def detect_pin_bar(df):
    """Bullish/Bearish Pin Bar"""
    r = {'bullish_pin_bar': False, 'bearish_pin_bar': False}
    if df is None or len(df) < 1:
        return r
    g = _geom(float(df['open'].iloc[-1]), float(df['close'].iloc[-1]),
              float(df['high'].iloc[-1]), float(df['low'].iloc[-1]))
    if g['body'] <= 0:
        return r
    if g['lw'] > g['body'] * PIN_RATIO and g['uw'] < g['body']:
        r['bullish_pin_bar'] = True
    if g['uw'] > g['body'] * PIN_RATIO and g['lw'] < g['body']:
        r['bearish_pin_bar'] = True
    return r


def detect_doji(df):
    """Doji + ประเภท (Dragonfly/Gravestone/Standard)"""
    if df is None or len(df) < 1:
        return False, None
    g = _geom(float(df['open'].iloc[-1]), float(df['close'].iloc[-1]),
              float(df['high'].iloc[-1]), float(df['low'].iloc[-1]))
    if g['body'] <= g['range'] * DOJI_BODY:
        if g['lw'] > g['uw'] * 1.5:
            return True, 'Dragonfly Doji'
        if g['uw'] > g['lw'] * 1.5:
            return True, 'Gravestone Doji'
        return True, 'Standard Doji'
    return False, None


def detect_hammer(df):
    """Hammer (lower wick ยาว, body อยู่บน, หลังขาลง)"""
    if df is None or len(df) < 1:
        return False
    co, cc = float(df['open'].iloc[-1]), float(df['close'].iloc[-1])
    g = _geom(co, cc, float(df['high'].iloc[-1]), float(df['low'].iloc[-1]))
    if g['body'] <= 0:
        return False
    if (g['lw'] / g['range'] >= HAMMER_WICK and
        g['uw'] / g['range'] <= UPPER_MAX and
        g['pos'] >= HAMMER_POS and _down(df)):
        return True
    return False


def detect_inverted_hammer(df):
    """Inverted Hammer (upper wick ยาว, body อยู่ล่าง, หลังขาลง)"""
    if df is None or len(df) < 1:
        return False
    co, cc = float(df['open'].iloc[-1]), float(df['close'].iloc[-1])
    g = _geom(co, cc, float(df['high'].iloc[-1]), float(df['low'].iloc[-1]))
    if g['body'] <= 0:
        return False
    if (g['uw'] / g['range'] >= HAMMER_WICK and
        g['lw'] / g['range'] <= UPPER_MAX and
        g['pos'] >= 0.5 and _down(df)):
        return True
    return False


def detect_shooting_star(df):
    """Shooting Star (upper wick ยาว, body อยู่ล่าง, หลังขาขึ้น)"""
    if df is None or len(df) < 1:
        return False
    co, cc = float(df['open'].iloc[-1]), float(df['close'].iloc[-1])
    g = _geom(co, cc, float(df['high'].iloc[-1]), float(df['low'].iloc[-1]))
    if g['body'] <= 0:
        return False
    if (g['uw'] / g['range'] >= HAMMER_WICK and
        g['lw'] / g['range'] <= UPPER_MAX and
        g['pos'] <= SHOOT_POS and _up(df)):
        return True
    return False


def detect_hanging_man(df):
    """Hanging Man (lower wick ยาว, body อยู่บน, หลังขาขึ้น)"""
    if df is None or len(df) < 1:
        return False
    co, cc = float(df['open'].iloc[-1]), float(df['close'].iloc[-1])
    g = _geom(co, cc, float(df['high'].iloc[-1]), float(df['low'].iloc[-1]))
    if g['body'] <= 0:
        return False
    if (g['lw'] / g['range'] >= HAMMER_WICK and
        g['uw'] / g['range'] <= UPPER_MAX and
        g['pos'] >= HAMMER_POS and _up(df)):
        return True
    return False


def detect_piercing_line(df):
    """Piercing Line"""
    if df is None or len(df) < 2:
        return False
    co, cc = float(df['open'].iloc[-1]), float(df['close'].iloc[-1])
    po, pc, pl = (float(df['open'].iloc[-2]),
                  float(df['close'].iloc[-2]),
                  float(df['low'].iloc[-2]))
    pm = (po + pc) / 2
    if pc < po and cc > co and co < pl and cc > pm and cc < po:
        return True
    return False


def detect_dark_cloud_cover(df):
    """Dark Cloud Cover"""
    if df is None or len(df) < 2:
        return False
    co, cc = float(df['open'].iloc[-1]), float(df['close'].iloc[-1])
    po, pc, ph = (float(df['open'].iloc[-2]),
                  float(df['close'].iloc[-2]),
                  float(df['high'].iloc[-2]))
    pm = (po + pc) / 2
    if pc > po and cc < co and co > ph and cc < pm and cc > pc:
        return True
    return False


# Pattern Classification
BULLISH = {
    'bullish_engulfing': 'Bullish Engulfing',
    'bullish_pin_bar': 'Bullish Pin Bar',
    'hammer': 'Hammer',
    'inverted_hammer': 'Inverted Hammer',
    'piercing_line': 'Piercing Line',
}
BEARISH = {
    'bearish_engulfing': 'Bearish Engulfing',
    'bearish_pin_bar': 'Bearish Pin Bar',
    'shooting_star': 'Shooting Star',
    'hanging_man': 'Hanging Man',
    'dark_cloud_cover': 'Dark Cloud Cover',
}
NEUTRAL = {'doji': 'Doji'}


def detect_all_patterns(df):
    """Detect all 11 candlestick patterns in one call."""
    r = {
        'bullish_engulfing': False, 'bearish_engulfing': False,
        'bullish_pin_bar': False, 'bearish_pin_bar': False,
        'doji': False, 'hammer': False, 'inverted_hammer': False,
        'shooting_star': False, 'hanging_man': False,
        'piercing_line': False, 'dark_cloud_cover': False,
        'latest_pattern': 'None', 'pattern_candle_num': 0,
        'bullish_signals': [], 'bearish_signals': [],
    }
    if df is None or len(df) < 2:
        return r
    try:
        e = detect_engulfing(df)
        pb = detect_pin_bar(df)
        dj, dj_t = detect_doji(df)
        hm = detect_hammer(df)
        ih = detect_inverted_hammer(df)
        ss = detect_shooting_star(df)
        hg = detect_hanging_man(df)
        pl = detect_piercing_line(df)
        dc = detect_dark_cloud_cover(df)
    except Exception:
        return r
    r.update(e)
    r.update(pb)
    r['doji'] = dj
    r['hammer'] = hm
    r['inverted_hammer'] = ih
    r['shooting_star'] = ss
    r['hanging_man'] = hg
    r['piercing_line'] = pl
    r['dark_cloud_cover'] = dc
    for k, lbl in BULLISH.items():
        if r[k]:
            r['bullish_signals'].append(lbl)
            if r['latest_pattern'] == 'None':
                r['latest_pattern'] = lbl
    for k, lbl in BEARISH.items():
        if r[k]:
            r['bearish_signals'].append(lbl)
            if r['latest_pattern'] == 'None':
                r['latest_pattern'] = lbl
    if r['doji']:
        if r['latest_pattern'] == 'None':
            r['latest_pattern'] = dj_t or 'Doji'
        if dj_t:
            if 'Dragonfly' in dj_t:
                r['bullish_signals'].append('Dragonfly Doji')
            elif 'Gravestone' in dj_t:
                r['bearish_signals'].append('Gravestone Doji')
            else:
                r['bullish_signals'].append('Doji (Neutral)')
    r['pattern_candle_num'] = len(df) - 1
    return r


def detect_candlestick_patterns(df):
    """Alias for detect_all_patterns (backward compatibility)"""
    return detect_all_patterns(df)
