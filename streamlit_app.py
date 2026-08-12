# streamlit_app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import logging
from data_engine import DataEngine
from config import (
    INITIAL_CAPITAL, DEFAULT_PARAMS, VERSION,
    PROJECT_NAME, TIMEFRAME, SYMBOLS
)
from signal_engine import Signal, rank_signals

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title=f"{PROJECT_NAME}",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# TÍTULO
# ============================================================
st.title(f"📊 {PROJECT_NAME}")
st.subheader(f"v{VERSION} — Scanner de {len(SYMBOLS)} activos · Timeframe {TIMEFRAME}")
st.markdown("---")

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("⚙️ Configuración")
    st.caption(f"Capital: ${INITIAL_CAPITAL:,.2f}")
    st.caption(f"Timeframe: {TIMEFRAME}")
    st.caption(f"Activos: {len(SYMBOLS)}")

    st.markdown("---")
    st.header("🎯 Parámetros")
    st.caption(f"Score mínimo: {DEFAULT_PARAMS['min_score']}")
    st.caption(f"ADX umbral: {DEFAULT_PARAMS['adx_threshold']}")
    st.caption(f"KER umbral: {DEFAULT_PARAMS['ker_threshold']}")
    st.caption(f"TP múltiplo: {DEFAULT_PARAMS['tp_mult']}× ATR")
    st.caption(f"SL múltiplo: {DEFAULT_PARAMS['sl_mult']}× ATR")
    st.caption(f"Trailing activación: {DEFAULT_PARAMS['trailing_activation']*100:.2f}%")
    st.caption(f"Trailing distancia: {DEFAULT_PARAMS['trailing_distance']*100:.2f}%")

    st.markdown("---")
    st.header("🔄 Acciones")
    refresh_btn = st.button("🔄 Actualizar Ranking", type="primary", use_container_width=True)

    st.markdown("---")
    st.header("📊 Estado")
    st.caption(f"Última actualización: {st.session_state.get('last_refresh', 'Nunca')}")
    st.caption(f"Señales aprobadas: {len(st.session_state.get('valid_signals', []))}")
    st.caption(f"Señales totales: {len(st.session_state.get('ranked_signals', []))}")

# ============================================================
# INICIALIZACIÓN
# ============================================================
if 'data_engine' not in st.session_state:
    with st.spinner("🔌 Inicializando motor de datos..."):
        st.session_state.data_engine = DataEngine()
        st.session_state.symbols = SYMBOLS
        st.session_state.signals = []
        st.session_state.valid_signals = []
        st.session_state.ranked_signals = []
        st.session_state.last_refresh = None
        st.session_state.data_dict = {}

# ============================================================
# FUNCIONES
# ============================================================
def refresh_ranking():
    """Escanea todos los activos y genera el ranking completo."""
    de = st.session_state.data_engine
    symbols = st.session_state.symbols

    signals = []
    data_dict = {}

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, sym in enumerate(symbols):
        status_text.text(f"Escaneando {sym}... ({i+1}/{len(symbols)})")
        df = de.fetch_ohlcv(sym, limit=300)
        if df is not None and not df.empty:
            data_dict[sym] = df
            s = Signal(sym, df, DEFAULT_PARAMS)
            signals.append(s.to_dict())
        progress_bar.progress((i + 1) / len(symbols))

    progress_bar.empty()
    status_text.empty()

    st.session_state.data_dict = data_dict
    st.session_state.signals = signals
    st.session_state.valid_signals = [s for s in signals if s.get('is_valid', False)]
    st.session_state.ranked_signals = rank_signals(signals)
    st.session_state.last_refresh = datetime.now().strftime("%H:%M:%S")

# ============================================================
# EJECUCIÓN
# ============================================================
if refresh_btn or st.session_state.last_refresh is None:
    with st.spinner("🔍 Escaneando activos..."):
        refresh_ranking()
    st.rerun()

# ============================================================
# DASHBOARD PRINCIPAL
# ============================================================
ranked = st.session_state.get('ranked_signals', [])
valid = st.session_state.get('valid_signals', [])

# Métricas rápidas
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📈 Señales aprobadas", len(valid))
with col2:
    st.metric("📊 Señales totales", len(ranked))
with col3:
    aprobados = sum(1 for s in valid if s.get('direction') == 'LONG')
    st.metric("🟢 LONG aprobadas", aprobados)
with col4:
    cortos = sum(1 for s in valid if s.get('direction') == 'SHORT')
    st.metric("🔴 SHORT aprobados", cortos)

st.markdown("---")

# ============================================================
# TABLA DE RANKING COMPLETO
# ============================================================
st.subheader("🏆 Ranking de Señales (Todas)")

if ranked:
    df_rank = pd.DataFrame(ranked)

    # Seleccionar columnas para mostrar
    display_cols = [
        'rank_label', 'symbol', 'direction', 'score', 'adx', 'ker',
        'regime', 'confidence', 'is_valid', 'reason',
        'estimated_time_to_trade', 'tp_pct', 'sl_pct'
    ]

    # Renombrar para visualización
    rename_map = {
        'rank_label': 'Rank',
        'symbol': 'Activo',
        'direction': 'Dir.',
        'score': 'Score',
        'adx': 'ADX',
        'ker': 'KER',
        'regime': 'Régimen',
        'confidence': 'Confianza',
        'is_valid': 'Aprobada',
        'reason': 'Razón',
        'estimated_time_to_trade': '⏱️ Próximo trade (min)',
        'tp_pct': 'TP %',
        'sl_pct': 'SL %'
    }

    df_display = df_rank[display_cols].rename(columns=rename_map)

    # Colorear filas
    def color_rows(row):
        if row['Aprobada']:
            return ['background-color: #1a3a1a; color: #00ff88'] * len(row)
        else:
            return ['background-color: #3a1a1a; color: #ff6666'] * len(row)

    st.dataframe(
        df_display.style.apply(color_rows, axis=1),
        use_container_width=True,
        height=600
    )
else:
    st.info("No hay señales disponibles. Presiona 'Actualizar Ranking'.")

st.markdown("---")

# ============================================================
# SEÑALES APROBADAS (DETALLE)
# ============================================================
st.subheader("✅ Señales Aprobadas (Detalle)")

if valid:
    for s in valid[:10]:  # Mostrar hasta 10
        with st.expander(f"{s['symbol']} — {s['direction']} (Score: {s['score']:.2f})"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("📊 Score", f"{s['score']:.3f}")
                st.metric("📈 ADX", f"{s['adx']:.1f}")
                st.metric("📉 KER", f"{s['ker']:.3f}")
                st.metric("🎯 Régimen", s['regime'])

            with col2:
                st.metric("💹 Confianza", f"{s['confidence']:.1f}%")
                st.metric("📌 Entry", f"${s['entry_price']:.2f}")
                st.metric("🛑 SL", f"${s['sl_price']:.2f} ({s['sl_pct']:.2f}%)")
                st.metric("🎯 TP", f"${s['tp_price']:.2f} ({s['tp_pct']:.2f}%)")

            with col3:
                st.metric("⏱️ Próximo trade", f"{s['estimated_time_to_trade']} min")
                st.metric("📊 Volumen ratio", f"{s['volume_ratio']:.2f}x")
                st.metric("📈 MFE esperado", f"{s['mfe_expected']*100:.2f}%")
                st.metric("🔒 Trailing", f"Act: {s['trailing_activation']*100:.2f}% / Dist: {s['trailing_distance']*100:.2f}%")

            # Gráfico de velas simplificado (usando Plotly)
            if s['symbol'] in st.session_state.data_dict:
                df = st.session_state.data_dict[s['symbol']]
                if df is not None and not df.empty:
                    fig = go.Figure(data=[
                        go.Candlestick(
                            x=df.index[-50:],
                            open=df['open'][-50:],
                            high=df['high'][-50:],
                            low=df['low'][-50:],
                            close=df['close'][-50:]
                        )
                    ])
                    fig.update_layout(
                        height=200,
                        margin=dict(l=0, r=0, t=0, b=0),
                        xaxis_rangeslider_visible=False
                    )
                    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No hay señales aprobadas en este momento.")

# ============================================================
# PIE DE PÁGINA
# ============================================================
st.markdown("---")
st.caption(f"DAPS Ω Scanner v{VERSION} — Última actualización: {st.session_state.get('last_refresh', 'Nunca')}")
