# config.py
import os

# ============================================================
# PROYECTO
# ============================================================
PROJECT_NAME = "DAPS Ω — Scanner de Señales"
VERSION = "1.0.0"

# ============================================================
# ZONA HORARIA Y FILTROS
# ============================================================
TIMEZONE = 'America/Argentina/Buenos_Aires'
HOUR_FILTER_START = 9
HOUR_FILTER_END = 18

# ============================================================
# CONSTANTES PRINCIPALES
# ============================================================
TIMEFRAME = '5m'
INITIAL_CAPITAL = 10000.0
MAX_HOLD = 120                    # minutos
RISK_PER_TRADE = 0.02
LEVERAGE = 1

# ============================================================
# DIRECTORIOS
# ============================================================
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(ROOT_DIR, 'cache')
DATA_DIR = os.path.join(ROOT_DIR, 'data')
LOGS_DIR = os.path.join(ROOT_DIR, 'logs')

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# ============================================================
# ACTIVOS (25 activos principales)
# ============================================================
SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'ADA/USDT',
    'DOT/USDT', 'LINK/USDT', 'AVAX/USDT', 'UNI/USDT', 'ATOM/USDT',
    'NEAR/USDT', 'APT/USDT', 'ARB/USDT', 'OP/USDT', 'INJ/USDT',
    'SEI/USDT', 'SUI/USDT', 'APE/USDT', 'FTM/USDT', 'ALGO/USDT',
    'ETC/USDT', 'LTC/USDT', 'DOGE/USDT', 'MATIC/USDT', 'VET/USDT'
]

# ============================================================
# EXCHANGES
# ============================================================
EXCHANGE_PRIORITY = ['binance', 'okx', 'kucoin', 'mexc', 'kraken', 'bybit']

# ============================================================
# PARÁMETROS DE ESTRATEGIA (optimizados para High WR)
# ============================================================
MIN_SCORE = 0.35                  # Score mínimo para señal aprobada
ADX_THRESHOLD = 22                # ADX mínimo
KER_THRESHOLD = 0.42              # KER mínimo
SL_MULT = 0.8                     # SL = SL_MULT * ATR
TP_MULT = 1.8                     # TP = TP_MULT * ATR (~0.7%)
TP_TREND_BONUS = 1.1
TRAILING_ACTIVATION = 0.0010      # 0.10%
TRAILING_DISTANCE = 0.0005        # 0.05%
BE_TRIGGER = 0.0020               # 0.20%
BE_BUFFER = 0.0005                # 0.05%

# ============================================================
# PARÁMETROS POR DEFECTO (para Signal)
# ============================================================
DEFAULT_PARAMS = {
    'min_score': MIN_SCORE,
    'adx_threshold': ADX_THRESHOLD,
    'ker_threshold': KER_THRESHOLD,
    'sl_mult': SL_MULT,
    'tp_mult': TP_MULT,
    'tp_trend_bonus': TP_TREND_BONUS,
    'trailing_activation': TRAILING_ACTIVATION,
    'trailing_distance': TRAILING_DISTANCE,
    'be_trigger': BE_TRIGGER,
    'be_buffer': BE_BUFFER,
    'max_hold': MAX_HOLD,
    'risk_per_trade': RISK_PER_TRADE,
    'leverage': LEVERAGE,
}