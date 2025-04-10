import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from googletrans import Translator

st.set_page_config(page_title="Análisis Financiero de Empresa", layout="centered")

# Agregar CSS para mejor apariencia
st.markdown("""
    <style>
        body { font-family: 'Arial', sans-serif; }
        .reportview-container .main .block-container{
            padding-top: 2rem;
            padding-right: 2rem;
            padding-left: 2rem;
            padding-bottom: 2rem;
        }
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: #2e86de;
        }
        .custom-plot {
            border: 2px solid #2e86de;
            border-radius: 10px;
            padding: 1rem;
            background-color: #f9fbfd;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
    </style>
""", unsafe_allow_html=True)

translator = Translator()

st.title("Análisis Financiero Interactivo de Empresa")
st.markdown("""
Esta aplicación permite analizar el comportamiento financiero de una empresa pública mediante datos reales obtenidos desde Yahoo Finance. 
Por favor, ingresa un **ticker válido** (por ejemplo, `AAPL`, `MSFT`, `TSLA`).
""")

# Entrada de ticker
ticker_input = st.text_input("Ticker de la empresa", value="AAPL")

if ticker_input:
    try:
        ticker = yf.Ticker(ticker_input)
        info = ticker.info

        # Validar existencia del ticker
        if not info or info.get("regularMarketPrice", None) is None:
            st.error("Ticker inválido, por favor verifica el símbolo e intenta de nuevo.")
        else:
            # Mostrar información fundamental
            st.header("Información de la Empresa")
            descripcion_original = info.get('longBusinessSummary', 'No disponible')
            descripcion_corta = descripcion_original[:300] if descripcion_original else 'No disponible'
            descripcion_traducida = translator.translate(descripcion_corta, dest='es').text

            st.markdown(f"**Nombre:** {info.get('shortName', 'N/A')}")
            st.markdown(f"**Sector:** {info.get('sector', 'N/A')}")
            st.markdown(f"**Industria:** {info.get('industry', 'N/A')}")
            st.markdown(f"**Descripción corta:** {descripcion_traducida}")
            st.markdown(f"**Capitalización de mercado:** {info.get('marketCap', 'N/A'):,} USD")
            st.markdown(f"**Beta (de Yahoo Finance):** {info.get('beta', 'N/A')}")
            st.markdown(f"**Precio actual:** {info.get('regularMarketPrice', 'N/A')} USD")
            st.markdown(f"**P/E Ratio (TTM):** {info.get('trailingPE', 'N/A')}")

            # Obtener precios históricos (5 años)
            df = ticker.history(period="5y")
            df = df[['Close']]
            df.rename(columns={"Close": "Precio Cierre"}, inplace=True)

            st.header("Gráfica de Precios Históricos")
            st.markdown('<div class="custom-plot">', unsafe_allow_html=True)
            fig, ax = plt.subplots(figsize=(12, 5))
            sns.set_style("whitegrid")
            sns.lineplot(data=df, x=df.index, y="Precio Cierre", ax=ax, color='#2e86de', linewidth=2.5)
            ax.set_title(f"Precio Histórico de Cierre Ajustado - {ticker_input.upper()}", fontsize=16, color='#2e86de')
            ax.set_xlabel("Fecha", fontsize=12)
            ax.set_ylabel("Precio (USD)", fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            st.pyplot(fig)
            st.markdown('</div>', unsafe_allow_html=True)

            # Cálculo de rendimientos
            st.header("Rendimientos Anualizados")
            precios = df["Precio Cierre"]
            fechas = precios.index
            hoy = fechas[-1]

            def calcular_cagr(precio_inicio, precio_fin, años):
                return (precio_fin / precio_inicio)**(1/años) - 1

            resumen = {}
            for años in [1, 3, 5]:
                fecha_inicio = hoy - pd.DateOffset(years=años)
                precios_filtrados = precios[fechas >= fecha_inicio]
                if len(precios_filtrados) > 0:
                    precio_ini = precios_filtrados.iloc[0]
                    precio_fin = precios_filtrados.iloc[-1]
                    resumen[f"{años} años"] = f"{calcular_cagr(precio_ini, precio_fin, años)*100:.2f}%"
                else:
                    resumen[f"{años} años"] = "N/A"

            st.dataframe(pd.DataFrame.from_dict(resumen, orient="index", columns=["CAGR (anualizado)"], dtype=str))
            st.markdown("""
            #### 📌 Fórmula utilizada:

            El rendimiento anualizado (CAGR) se calcula como:

            $$
            CAGR = \\left(\\frac{Precio\\ final}{Precio\\ inicial}\\right)^{\\frac{1}{Años}} - 1
            $$
            """)

            # Volatilidad (riesgo)
            st.header("Volatilidad Histórica (Riesgo)")
            retornos_diarios = precios.pct_change().dropna()
            volatilidad_anual = np.std(retornos_diarios) * np.sqrt(252)

            st.markdown(f"**Valor de riesgo:** {volatilidad_anual*100:.2f}%")
            st.markdown("""
            #### 📌 Fórmula utilizada:

            La volatilidad anual se calcula como:

            $$
            Volatilidad = \\sigma_{diaria} \\times \\sqrt{252}
            $$

            Donde $\\sigma_{diaria}$ es la desviación estándar de los rendimientos diarios.
            """)

            # Cálculo de Beta contra el S&P 500
            st.header("Beta calculada respecto al S&P 500")
            sp500 = yf.Ticker("^GSPC").history(period="5y")["Close"]
            df["S&P 500"] = sp500.reindex(df.index).ffill().bfill()

            df.dropna(inplace=True)
            df["Rend_Accion"] = df["Precio Cierre"].pct_change()
            df["Rend_SP500"] = df["S&P 500"].pct_change()

            df.dropna(inplace=True)

            covarianza = np.cov(df["Rend_Accion"], df["Rend_SP500"])[0][1]
            var_sp500 = np.var(df["Rend_SP500"])
            beta_calculada = covarianza / var_sp500

            st.markdown(f"**Beta calculada:** {beta_calculada:.4f}")
            st.markdown("""
            #### 📌 Fórmula utilizada:

            $$
            Beta = \\frac{\\text{Cov}(R_{\\text{acción}}, R_{\\text{mercado}})}{\\text{Var}(R_{\\text{mercado}})}
            $$

            La Beta representa la sensibilidad del rendimiento de la acción respecto al mercado.
            """)

    except Exception as e:
        st.error("Ticker inválido o error al cargar datos. Por favor verifica el símbolo e intenta de nuevo.")

with st.sidebar:
    st.image("jose.png", width=150, caption="Desarrollado por: José Andrés Robles Jarero")
    st.markdown("**Estudiante de Ingeniería Financiera**")
    st.markdown("---")
