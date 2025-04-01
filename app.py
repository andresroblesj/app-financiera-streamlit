import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
import plotly.graph_objects as go
from datetime import datetime

# Parámetros de entrada
ticker = 'AAPL'  # Símbolo de la acción
periodo = '5y'   # Últimos 5 años
riesgo_tolerado = 'medio'  # Opciones: bajo, medio, alto
tipo_trading = 'largo plazo'  # Opciones: corto plazo, largo plazo

# Descargar datos financieros y de mercado
empresa = yf.Ticker(ticker)
info = empresa.info
hist = empresa.history(period=periodo)

# 1. Evaluación de la Empresa

# Métricas financieras clave
roe = info.get('returnOnEquity', np.nan)
roa = info.get('returnOnAssets', np.nan)
margen_neto = info.get('profitMargins', np.nan)
ebitda = info.get('ebitda', np.nan)
deuda_total = info.get('totalDebt', np.nan)
ebitda_anual = info.get('ebitda', np.nan)
deuda_ebitda = deuda_total / ebitda_anual if ebitda_anual else np.nan
flujo_caja_libre = info.get('freeCashflow', np.nan)

# Tendencias de ingresos y ganancias en los últimos 5 años
ingresos = []
ganancias = []
for year in range(5):
    try:
        fin_data = empresa.financials.iloc[:, year]
        ingresos.append(fin_data.get('Total Revenue', np.nan))
        ganancias.append(fin_data.get('Gross Profit', np.nan))
    except:
        ingresos.append(np.nan)
        ganancias.append(np.nan)

# Cálculo del Altman Z-Score
try:
    activos_totales = info.get('totalAssets', np.nan)
    pasivos_totales = info.get('totalLiab', np.nan)
    capital_trabajo = info.get('workingCapital', np.nan)
    ventas = info.get('totalRevenue', np.nan)
    utilidad_retenida = info.get('retainedEarnings', np.nan)
    ebit = info.get('ebit', np.nan)
    valor_mercado_equity = info.get('marketCap', np.nan)
    deuda_total = info.get('totalDebt', np.nan)

    x1 = capital_trabajo / activos_totales if activos_totales else np.nan
    x2 = utilidad_retenida / activos_totales if activos_totales else np.nan
    x3 = ebit / activos_totales if activos_totales else np.nan
    x4 = valor_mercado_equity / deuda_total if deuda_total else np.nan
    x5 = ventas / activos_totales if activos_totales else np.nan

    z_score = 1.2*x1 + 1.4*x2 + 3.3*x3 + 0.6*x4 + 1.0*x5
except:
    z_score = np.nan

# 2. Análisis de Riesgos Externos

# Factores macroeconómicos (ejemplo simplificado)
tasas_interes = 0.05  # Suponiendo una tasa de interés del 5%
inflacion = 0.03      # Suponiendo una inflación del 3%
ciclo_economico = 'expansión'  # Opciones: expansión, recesión

# Riesgos geopolíticos y regulatorios (requiere análisis cualitativo externo)

# Volatilidad de la acción y correlación con el mercado
volatilidad = hist['Close'].pct_change().std()
# Correlación con el índice S&P 500
sp500 = yf.Ticker('^GSPC').history(period=periodo)['Close']
correlacion_sp500 = hist['Close'].pct_change().corr(sp500.pct_change())

# 3. Análisis Técnico y Sentimiento del Mercado

# Cálculo de indicadores técnicos
hist['MA50'] = hist['Close'].rolling(window=50).mean()
hist['MA200'] = hist['Close'].rolling(window=200).mean()
hist['RSI'] = 100 - (100 / (1 + hist['Close'].pct_change().rolling(window=14).mean() / hist['Close'].pct_change().rolling(window=14).std()))

# Sentimiento del mercado basado en volumen de negociación
cambio_volumen = hist['Volume'].pct_change().mean()

# 4. Recomendaciones Cuantitativas para Trading

# Probabilidad de crisis financiera interna (simplificado)
prob_crisis = norm.cdf(-z_score) if not np.isnan(z_score) else np.nan

# Estrategia de trading basada en momentum
if hist['MA50'].iloc[-1] > hist['MA200'].iloc[-1]:
    estrategia = 'Comprar'
elif hist['MA50'].iloc[-1] < hist['MA200'].iloc[-1]:
    estrategia = 'Vender'
else:
    estrategia = 'Mantener'

# 5. Visualización de Precios Históricos

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=hist.index,
    y=hist['Close'],
    mode='lines',
    name='Precio de cierre'
))
import streamlit as st

st.set_page_config(layout="wide")
st.title(f"📈 Análisis Financiero de {ticker}")

st.subheader("📊 Recomendación de Trading")
st.write(f"Estrategia sugerida: **{estrategia}**")
st.write(f"Probabilidad de crisis financiera interna (Altman Z): {prob_crisis:.2%}")

st.subheader("📈 Indicadores Técnicos")
st.write(f"Volatilidad histórica: {volatilidad:.2%}")
st.write(f"Correlación con el S&P 500: {correlacion_sp500:.2f}")

st.subheader("💵 Finanzas Clave")
st.write(f"ROE: {roe:.2%} | ROA: {roa:.2%} | Margen Neto: {margen_neto:.2%}")
st.write(f"Deuda/EBITDA: {deuda_ebitda:.2f}")
st.write(f"Flujo de Caja Libre: ${flujo_caja_libre:,}")

st.subheader("📉 Ingresos y Ganancias (últimos 5 años)")
st.write("Ingresos:", ingresos)
st.write("Ganancias Brutas:", ganancias)

st.subheader("📊 Precio Histórico")
st.plotly_chart(fig, use_container_width=True)
