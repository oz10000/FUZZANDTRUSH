# core_engine.py
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    ADX (Average Directional Index)
    Fuente: https://www.investopedia.com/terms/a/adx.asp
    """
    if df.empty or len(df) < period:
        return pd.Series(0.0, index=df.index)

    high, low, close = df['high'], df['low'], df['close']

    # True Range
    tr = pd.DataFrame({
        'hl': high - low,
        'hc': (high - close.shift()).abs(),
        'lc': (low - close.shift()).abs()
    }).max(axis=1)

    # Directional Movement
    plus_dm = high.diff()
    minus_dm = low.diff().abs() * -1
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    minus_dm = minus_dm.abs()

    # ATR
    atr = tr.rolling(period).mean()
    atr = atr.replace(0, np.nan)

    # +DI y -DI
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)

    # DX y ADX
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(period).mean()
    adx = adx.fillna(0).replace([np.inf, -np.inf], 0)

    return adx


def compute_ker(df: pd.DataFrame, period: int = 10) -> pd.Series:
    """
    KER (Kaufman Efficiency Ratio)
    Fuente: https://trendspider.com/learning-center/kaufman-efficiency-ratio/
    """
    if df.empty or len(df) < period:
        return pd.Series(0.0, index=df.index)

    close = df['close']
    change = abs(close.diff(period))
    volatility = close.diff().abs().rolling(period).sum()
    ker = change / (volatility + 1e-9)
    ker = ker.fillna(0).replace([np.inf, -np.inf], 0)

    return ker


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    ATR (Average True Range)
    Fuente: https://www.investopedia.com/terms/a/atr.asp
    """
    if df.empty or len(df) < period:
        return pd.Series(0.0, index=df.index)

    high, low, close = df['high'], df['low'], df['close']

    tr = pd.DataFrame({
        'hl': high - low,
        'hc': (high - close.shift()).abs(),
        'lc': (low - close.shift()).abs()
    }).max(axis=1)

    atr = tr.rolling(period).mean()
    atr = atr.fillna(0).replace([np.inf, -np.inf], 0)

    return atr


def compute_regime(df: pd.DataFrame, atr_period: int = 14) -> str:
    """
    Clasifica régimen: 'Expansión', 'Tendencia Fuerte', 'Tendencia', 'Chop'
    """
    if df.empty or len(df) < 30:
        return 'Chop'

    close = df['close']
    adx_series = compute_adx(df)
    atr_series = compute_atr(df, atr_period)

    adx_val = adx_series.iloc[-1] if not adx_series.empty else 0
    atr_pct = atr_series.iloc[-1] / close.iloc[-1] if close.iloc[-1] > 0 else 0

    if adx_val > 40 and atr_pct > 0.02:
        return 'Expansión'
    elif adx_val > 30:
        return 'Tendencia Fuerte'
    elif adx_val > 20:
        return 'Tendencia'
    else:
        return 'Chop'


def compute_pidelta_score(df: pd.DataFrame, ema_period: int = 22,
                          atr_period: int = 14) -> float:
    """
    Score compuesto [-1, 1].
    Pesos: Trend(25%), Strength(ADX/40)(20%), KER(15%),
           ATR rel(10%), Momentum(10%), EMA direction(20%)
    """
    if df.empty or len(df) < 30:
        return 0.0

    close = df['close']
    last_close = close.iloc[-1]

    # 1. Trend (25%) - pendiente de EMA
    ema = close.ewm(span=ema_period).mean()
    ema_slope = (ema.iloc[-1] - ema.iloc[-5]) / ema.iloc[-5] if len(ema) >= 5 else 0
    trend_score = np.clip(ema_slope * 10, -1, 1) * 0.25

    # 2. Strength - ADX/40 (20%)
    adx_series = compute_adx(df)
    adx_val = adx_series.iloc[-1] if not adx_series.empty else 0
    strength_score = np.clip(adx_val / 40, 0, 1) * 0.20

    # 3. KER (15%)
    ker_series = compute_ker(df)
    ker_val = ker_series.iloc[-1] if not ker_series.empty else 0
    ker_score = np.clip(ker_val, 0, 1) * 0.15

    # 4. ATR relativo (10%)
    atr_series = compute_atr(df, atr_period)
    atr_val = atr_series.iloc[-1] if not atr_series.empty else 0
    atr_ma = atr_series.rolling(20).mean().iloc[-1] if len(atr_series) >= 20 else atr_val
    atr_rel = atr_val / atr_ma if atr_ma > 0 else 1
    atr_score = np.clip(atr_rel, 0.5, 2) * 0.10

    # 5. Momentum (10%)
    momentum = (close.iloc[-1] - close.iloc[-5]) / close.iloc[-5] if len(close) >= 5 else 0
    momentum_score = np.clip(momentum * 20, -1, 1) * 0.10

    # 6. Otros componentes (20%) - dirección EMA principal
    ema_50 = close.ewm(span=50).mean()
    ema_direction = 1 if last_close > ema_50.iloc[-1] else -1
    ema_direction_score = ema_direction * 0.20

    # Score total
    score = (trend_score + strength_score + ker_score +
             atr_score + momentum_score + ema_direction_score)

    return np.clip(score, -1, 1)


def estimate_mfe(df: pd.DataFrame, regime: str, atr_pct: float,
                 volume_ratio: float) -> float:
    """
    Estima el MFE (Maximum Favorable Excursion) esperado.
    """
    base = atr_pct * 1.5
    regime_factors = {
        'Expansión': 1.5,
        'Tendencia Fuerte': 1.3,
        'Tendencia': 1.1,
        'Chop': 0.5
    }
    factor = regime_factors.get(regime, 1.0)
    volume_factor = min(volume_ratio / 1.2, 1.5)
    return base * factor * volume_factor
