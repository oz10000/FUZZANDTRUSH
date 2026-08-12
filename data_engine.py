# data_engine.py
import os
import time
import logging
import pandas as pd
import ccxt
from typing import Optional, List
from config import EXCHANGE_PRIORITY, CACHE_DIR, TIMEFRAME, SYMBOLS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataEngine:
    """Motor de datos con múltiples exchanges, caché y failover."""

    def __init__(self):
        self.cache_dir = CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        self.exchanges = {}
        self.primary = None
        self._connect_exchanges()

    def _connect_exchanges(self):
        """Conecta a los exchanges en orden de prioridad."""
        for ex_id in EXCHANGE_PRIORITY:
            try:
                ex_class = getattr(ccxt, ex_id)
                exchange = ex_class({
                    'enableRateLimit': True,
                    'options': {'defaultType': 'spot'},
                    'rateLimit': 1200,
                })
                exchange.load_markets()
                self.exchanges[ex_id] = exchange
                if self.primary is None:
                    self.primary = ex_id
                logger.info(f"✅ Conectado a {ex_id}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo conectar a {ex_id}: {e}")

        if not self.exchanges:
            raise RuntimeError("No se pudo conectar a ningún exchange")
        logger.info(f"✅ DataEngine listo. Primary: {self.primary}")

    def fetch_ohlcv(self, symbol: str, timeframe: str = None, limit: int = 300,
                    use_cache: bool = True) -> Optional[pd.DataFrame]:
        """Obtiene velas OHLCV con caché y failover."""
        if timeframe is None:
            timeframe = TIMEFRAME

        cache_file = os.path.join(
            self.cache_dir,
            f"{symbol.replace('/', '_')}_{timeframe}_{limit}.parquet"
        )

        # Intentar cargar desde caché
        if use_cache and os.path.exists(cache_file):
            try:
                df = pd.read_parquet(cache_file)
                if (pd.Timestamp.now() - df.index[-1]).total_seconds() < 3600:
                    logger.debug(f"✅ Caché válido para {symbol}")
                    return df
                else:
                    logger.debug(f"⏳ Caché obsoleto para {symbol}, descargando...")
            except Exception as e:
                logger.warning(f"⚠️ Error leyendo caché de {symbol}: {e}")

        # Descargar desde exchanges
        for ex_id, exchange in self.exchanges.items():
            for attempt in range(3):
                try:
                    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                    if not ohlcv:
                        logger.warning(f"⚠️ No se obtuvieron velas para {symbol} desde {ex_id}")
                        continue

                    df = pd.DataFrame(
                        ohlcv,
                        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    )
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    df.sort_index(inplace=True)

                    # Guardar en caché
                    if use_cache:
                        df.to_parquet(cache_file)

                    logger.debug(f"✅ Descargado {symbol} desde {ex_id} ({len(df)} velas)")
                    return df

                except Exception as e:
                    logger.warning(f"Intento {attempt+1}/3 para {symbol} desde {ex_id} falló: {e}")
                    time.sleep(1)

        logger.error(f"❌ No se pudo descargar {symbol} desde ningún exchange")
        return None
