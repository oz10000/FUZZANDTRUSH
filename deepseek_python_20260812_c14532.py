# signal_engine.py
import pandas as pd
import numpy as np
from core_engine import (
    compute_adx, compute_ker, compute_atr,
    compute_regime, compute_pidelta_score
)
from config import DEFAULT_PARAMS


class Signal:
    """Genera señal para un activo con todos los indicadores y ranking."""

    def __init__(self, symbol: str, df: pd.DataFrame, params: dict = None):
        self.symbol = symbol
        self.params = params or DEFAULT_PARAMS
        self.df = df

        # Campos de la señal
        self.score = 0.0
        self.adx = 0.0
        self.ker = 0.0
        self.atr_pct = 0.0
        self.atr_abs = 0.0
        self.regime = 'Chop'
        self.is_valid = False
        self.reason = "No evaluado"
        self.direction = None
        self.confidence = 0.0
        self.entry_price = 0.0
        self.sl_price = 0.0
        self.tp_price = 0.0
        self.trailing_activation = 0.0
        self.trailing_distance = 0.0
        self.break_even_trigger = 0.0
        self.break_even_buffer = 0.0
        self.max_hold_minutes = 0

        # Indicadores adicionales para visualización
        self.ema15 = 0.0
        self.ema50 = 0.0
        self.volume_ratio = 0.0
        self.mfe_expected = 0.0

        # Tiempo estimado hasta el próximo trade (en minutos)
        self.estimated_time_to_trade = 0

        if not df.empty and len(df) > 30:
            self._compute()

    def _compute(self):
        p = self.params
        close = self.df['close'].iloc[-1]
        volume = self.df['volume'].iloc[-1]

        # Calcular indicadores
        self.score = compute_pidelta_score(self.df)

        adx_series = compute_adx(self.df)
        self.adx = adx_series.iloc[-1] if not adx_series.empty else 0

        ker_series = compute_ker(self.df, 10)
        self.ker = ker_series.iloc[-1] if not ker_series.empty else 0

        atr_series = compute_atr(self.df)
        atr_val = atr_series.iloc[-1] if not atr_series.empty else 0
        self.atr_abs = atr_val
        self.atr_pct = atr_val / close if close > 0 else 0

        self.regime = compute_regime(self.df)

        # EMAs
        self.ema15 = self.df['close'].ewm(span=15).mean().iloc[-1]
        self.ema50 = self.df['close'].ewm(span=50).mean().iloc[-1]

        # Volumen
        avg_volume = self.df['volume'].rolling(20).mean().iloc[-1]
        self.volume_ratio = volume / avg_volume if avg_volume > 0 else 0

        # Dirección
        self.direction = 'LONG' if self.score > 0 else 'SHORT'

        # Verificar validez (filtros)
        self.is_valid = True
        self.reason = "OK"

        if abs(self.score) < p['min_score']:
            self.is_valid = False
            self.reason = f"score {self.score:.2f} < {p['min_score']}"
        elif self.adx < p['adx_threshold']:
            self.is_valid = False
            self.reason = f"ADX {self.adx:.1f} < {p['adx_threshold']}"
        elif self.ker < p['ker_threshold']:
            self.is_valid = False
            self.reason = f"KER {self.ker:.2f} < {p['ker_threshold']}"
        elif self.regime == 'Chop':
            self.is_valid = False
            self.reason = "Régimen Chop"
        else:
            # Filtro EMA15 (alineación con tendencia)
            if self.direction == 'LONG' and close < self.ema15:
                self.is_valid = False
                self.reason = "Precio < EMA15"
            elif self.direction == 'SHORT' and close > self.ema15:
                self.is_valid = False
                self.reason = "Precio > EMA15"

        # Precios de entrada, SL y TP
        self.entry_price = close

        sl_mult = p['sl_mult']
        tp_mult = p['tp_mult']

        if self.regime in ['Tendencia Fuerte', 'Expansión']:
            tp_mult *= p['tp_trend_bonus']

        if self.direction == 'LONG':
            self.sl_price = close * (1 - sl_mult * self.atr_pct)
            self.tp_price = close * (1 + tp_mult * self.atr_pct)
        else:
            self.sl_price = close * (1 + sl_mult * self.atr_pct)
            self.tp_price = close * (1 - tp_mult * self.atr_pct)

        # Trailing Stop
        self.trailing_activation = p['trailing_activation']
        self.trailing_distance = p['trailing_distance']
        self.break_even_trigger = p['be_trigger']
        self.break_even_buffer = p['be_buffer']
        self.max_hold_minutes = p['max_hold']

        # Confianza (0-100)
        self.confidence = (
            30 +
            20 * (self.adx / 40) +
            20 * (self.ker / 0.6) +
            15 * (abs(self.score) / 0.6) +
            15 * min(self.volume_ratio / 1.5, 1)
        )
        self.confidence = min(max(self.confidence, 0), 100)

        # MFE esperado (amplitud)
        self.mfe_expected = self._estimate_mfe()

        # Tiempo estimado hasta el próximo trade (basado en frecuencia histórica)
        self.estimated_time_to_trade = self._estimate_time_to_trade()

    def _estimate_mfe(self) -> float:
        """Estima el MFE esperado basado en ATR y régimen."""
        base = self.atr_pct * 1.5
        regime_factors = {
            'Expansión': 1.5,
            'Tendencia Fuerte': 1.3,
            'Tendencia': 1.1,
            'Chop': 0.5
        }
        factor = regime_factors.get(self.regime, 1.0)
        volume_factor = min(self.volume_ratio / 1.2, 1.5)
        return base * factor * volume_factor

    def _estimate_time_to_trade(self) -> int:
        """Estima el tiempo hasta el próximo trade (minutos) basado en la señal."""
        # Si la señal es válida, el tiempo es corto
        if self.is_valid:
            if self.confidence > 80:
                return 5 + int((100 - self.confidence) / 10)  # 5-7 minutos
            else:
                return 10 + int((80 - self.confidence) / 5)  # 10-26 minutos
        else:
            # Si no es válida, estimar basado en score
            if abs(self.score) > 0.5:
                return 15 + int((1 - abs(self.score)) * 30)
            else:
                return 45 + int((1 - abs(self.score)) * 60)

    def to_dict(self) -> dict:
        """Convierte la señal a diccionario para visualización."""
        return {
            'symbol': self.symbol,
            'score': self.score,
            'adx': self.adx,
            'ker': self.ker,
            'atr_pct': self.atr_pct,
            'atr_abs': self.atr_abs,
            'regime': self.regime,
            'direction': self.direction,
            'is_valid': self.is_valid,
            'reason': self.reason,
            'confidence': self.confidence,
            'entry_price': self.entry_price,
            'sl_price': self.sl_price,
            'tp_price': self.tp_price,
            'trailing_activation': self.trailing_activation,
            'trailing_distance': self.trailing_distance,
            'break_even_trigger': self.break_even_trigger,
            'break_even_buffer': self.break_even_buffer,
            'max_hold_minutes': self.max_hold_minutes,
            'ema15': self.ema15,
            'ema50': self.ema50,
            'volume_ratio': self.volume_ratio,
            'mfe_expected': self.mfe_expected,
            'estimated_time_to_trade': self.estimated_time_to_trade,
            'tp_pct': (self.tp_price / self.entry_price - 1) * 100 if self.entry_price > 0 else 0,
            'sl_pct': (self.sl_price / self.entry_price - 1) * 100 if self.entry_price > 0 else 0,
        }


def rank_signals(signals: list) -> list:
    """
    Rankea las señales por score (absoluto) y confianza.
    Las señales no aprobadas también se incluyen en el ranking.
    """
    # Separar aprobadas y no aprobadas
    valid = [s for s in signals if s['is_valid']]
    invalid = [s for s in signals if not s['is_valid']]

    # Ordenar por score absoluto (descendente)
    valid_sorted = sorted(valid, key=lambda x: abs(x['score']), reverse=True)
    invalid_sorted = sorted(invalid, key=lambda x: abs(x['score']), reverse=True)

    # Asignar ranking
    ranked = []
    for i, s in enumerate(valid_sorted):
        s['rank'] = i + 1
        s['rank_label'] = f"#{i+1} APROBADA"
        ranked.append(s)

    for i, s in enumerate(invalid_sorted):
        s['rank'] = len(valid_sorted) + i + 1
        s['rank_label'] = f"#{len(valid_sorted)+i+1} (no aprobada)"
        ranked.append(s)

    return ranked