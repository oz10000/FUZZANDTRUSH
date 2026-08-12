# config.py
import os

# ============================================================
# PROYECTO
# ============================================================
PROJECT_NAME = "DAPS Ω — Scanner de Señales"
VERSION = "2.0.0"

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
MAX_HOLD = 60                     # minutos
RISK_PER_TRADE = 0.01
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
# ACTIVOS (52 activos de alta liquidez en Binance/Bybit)
# ============================================================
SYMBOLS = [
    # Top 10 por capitalización
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'ADA/USDT',
    'DOT/USDT', 'LINK/USDT', 'AVAX/USDT', 'UNI/USDT', 'ATOM/USDT',

    # Capa 1 y Capa 2 consolidados
    'BNB/USDT', 'MATIC/USDT', 'LTC/USDT', 'ETC/USDT', 'VET/USDT',
    'ALGO/USDT', 'FTM/USDT', 'NEAR/USDT', 'APT/USDT', 'ARB/USDT',
    'OP/USDT', 'INJ/USDT', 'SEI/USDT', 'SUI/USDT', 'APE/USDT',

    # Meme coins con alta liquidez
    'DOGE/USDT', 'PEPE/USDT', 'WIF/USDT', 'BONK/USDT', 'FLOKI/USDT',

    # DeFi y ecosistemas
    'AAVE/USDT', 'MKR/USDT', 'CRV/USDT', 'LDO/USDT', 'RNDR/USDT',

    # Gaming y metaverso
    'SAND/USDT', 'MANA/USDT', 'GALA/USDT', 'AXS/USDT', 'ILV/USDT',

    # Almacenamiento y computación
    'FIL/USDT', 'AR/USDT', 'ICP/USDT', 'RNDR/USDT',

    # Nuevos listados de Binance (confirmados)
    'COOKIE/USDT', 'ALCH/USDT', 'SWARMS/USDT', 'AERO/USDT',
    'ETHW/USDT', 'PONKE/USDT', 'SLERF/USDT', 'KMNO/USDT',
    '1000X/USDT', 'GRIFFAIN/USDT', 'MORPHO/USDT', '1000000MOG/USDT',
    '1000WHY/USDT', 'SWELL/USDT'
]

# ============================================================
# EXCHANGES
# ============================================================
EXCHANGE_PRIORITY = ['binance', 'okx', 'kucoin', 'mexc', 'kraken', 'bybit']

# ============================================================
# PARÁMETROS DE ESTRATEGIA OPTIMIZADOS (Iteración 7)
# ============================================================
MIN_SCORE = 0.50                  # Score mínimo
ADX_THRESHOLD = 32                # ADX mínimo
KER_THRESHOLD = 0.58              # KER mínimo
SL_MULT = 0.5                     # SL = 0.5 * ATR (~0.19%)
TP_MULT = 1.0                     # TP = 1.0 * ATR (~0.38%)
TP_TREND_BONUS = 1.0              # Sin bonus (para TP fijo)
TRAILING_ACTIVATION = 0.0         # SIN ACTIVACIÓN (trailing desde entrada)
TRAILING_DISTANCE = 0.0010        # 0.10% (distancia fija)
BE_TRIGGER = 0.0015               # 0.15% (break-even)
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
