import sys
import os
sys.path.append(os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from core import calcular_aporte, simular_aposentadoria, ir_progressivo, ir_regressivo
import altair as alt
from io import BytesIO

st.set_page_config(page_title="Wealth Planning", layout="wide")

st.markdown("""
    <style>
    @media (min-width: 768px) {
        section.main > div {
            padding-left: 1.25rem !important;
            padding-right: 1.25rem !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

def formatar_moeda(valor, decimais=0):
    return f"R$ {valor:,.{decimais}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def buscar_serie_bcb(codigo, data_inicial, data_final):
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json&dataInicial={data_inicial}&dataFinal={data_final}"
    r = requests.get(url)
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    df["valor"] = df["valor"].str.replace(",", ".").astype(float)
    df["data"] = pd.to_datetime(df["data"], dayfirst=True)
    return df.set_index("data").sort_index()

def calcular_medias_historicas():
    from dateutil.relativedelta import relativedelta
    fim = datetime.today().replace(day=1) - timedelta(days=1)
    inicio = fim.replace(day=1) - relativedelta(years=10)
    inicio_str = inicio.strftime("%d/%m/%Y")
    fim_str = fim.strftime("%d/%m/%Y")

    try:
        df_ipca = buscar_serie_bcb(433, inicio_str, fim_str)
        df_selic = buscar_serie_bcb(4390, inicio_str, fim_str)
        df = df_selic.join(df_ipca, lsuffix="_selic", rsuffix="_ipca").dropna()

        ipca_mensal = df["valor_ipca"] / 100
        selic_mensal = df["valor_selic"] / 100
        juros_real_mensal = (1 + selic_mensal) / (1 + ipca_mensal) - 1
        df["juros_real_mensal"] = juros_real_mensal

        media_ipca = (1 + ipca_mensal.mean()) ** 12 - 1
        media_selic = (1 + selic_mensal.mean()) ** 12 - 1
        media_juros_real = (1 + df["juros_real_mensal"].mean()) ** 12 - 1

        return round(media_selic * 100, 2), round(media_ipca * 100, 2), round(media_juros_real * 100, 2)
    except:
        return 9.5, 5.0, 4.5

def calcular_juros_real_atual(ipca_pct, selic_pct):
    return round(((1 + selic_pct / 100) / (1 + ipca_pct / 100) - 1) * 100, 2)

def check_password():
    def password_entered():
        if st.session_state["password"] == "sow123":
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.markdown("## 🔒 Área protegida")
        st.text_input("Digite a senha", type="password", on_change=password_entered, key="password")
        st.stop()

check_password()

st.markdown("""
    <style>
    .header {
        background-color: #123934;
        padding: 20px 10px;
        text-align: center;
    }
    .header img {
        max-width: 200px;
        height: auto;
    }
    </style>
    <div class="header">
      <img src="https://i.imgur.com/iCRuacp.png" alt="Logo Sow Capital">
    </div>
""", unsafe_allow_html=True)

st.title("Wealth Planning")

selic_media, ipca_media, juros_real_medio = calcular_medias_historicas()

with st.form("formulario"):
    st.markdown("### 📋 Dados Iniciais")
    renda_atual = st.number_input("Renda atual (R$)", min_value=0.0, step=100.0, value=10000.0, format="%.0f")
    idade_atual = st.number_input("Idade atual", min_value=18.0, max_value=100.0, value=30.0, format="%.0f")
    poupanca = st.number_input("Poupança atual (R$)", min_value=0.0, step=1000.0, value=50000.0, format="%.0f")

    st.markdown("### 📊 Dados Econômicos")
    st.markdown(f"🔎 Juros real médio histórico: **{juros_real_medio:.2f}% a.a.**")
    taxa_juros = st.number_input("Rentabilidade real esperada (% a.a.)", min_value=0.0, max_value=100.0, value=juros_real_medio, format="%.2f")

    st.markdown("### 🧾 Renda desejada na aposentadoria")
    renda_desejada = st.number_input("Renda mensal desejada (R$)", min_value=0.0, step=500.0, value=15000.0, format="%.0f")
    plano_saude = st.number_input("Plano de saúde (R$)", min_value=0.0, step=100.0, value=0.0, format="%.0f")
    outras_despesas = st.number_input("Outras despesas planejadas (R$)", min_value=0.0, step=100.0, value=0.0, format="%.0f")

    st.markdown("### 💸 Renda passiva estimada")
    previdencia = st.number_input("Renda com previdência (R$)", min_value=0.0, step=100.0, value=0.0, format="%.0f")
    aluguel_ou_outras = st.number_input("Aluguel ou outras fontes de renda (R$)", min_value=0.0, step=100.0, value=0.0, format="%.0f")

    st.markdown("### 🧓 Dados da aposentadoria")
    idade_aposentadoria = st.number_input("Idade para aposentadoria", min_value=0.0, max_value=100.0, value=65.0, format="%.0f")
    expectativa_vida = st.number_input("Expectativa de vida", min_value=idade_aposentadoria + 1, max_value=120.0, value=90.0, format="%.0f")

    st.markdown("### 🎯 Objetivo Final")
    modo = st.selectbox("Objetivo com o patrimônio", ["manter", "zerar", "atingir"])
    outro_valor = None
    if modo == "atingir":
        outro_valor = st.number_input("Valor alvo (R$)", min_value=0.0, step=10000.0, format="%.0f")

    submitted = st.form_submit_button("📈 Calcular")

if submitted:
    if idade_aposentadoria <= idade_atual:
        st.error("⚠️ A idade para aposentadoria deve ser maior do que a idade atual informada.")
        st.stop()

    renda_passiva_total = previdencia + aluguel_ou_outras
    despesas_adicionais = plano_saude + outras_despesas
    renda_total_desejada = renda_desejada + despesas_adicionais
    renda_liquida = max(renda_total_desejada - renda_passiva_total, 0)

    dados = {
        "idade_atual": int(idade_atual),
        "idade_aposentadoria": int(idade_aposentadoria),
        "expectativa_vida": int(expectativa_vida),
        "renda_atual": int(renda_atual),
        "renda_desejada": int(renda_desejada),
        "poupanca": int(poupanca),
        "taxa_juros_anual": taxa_juros / 100,
    }

    resultado = calcular_aporte(
        dados["idade_atual"], dados["idade_aposentadoria"], dados["expectativa_vida"],
        dados["poupanca"], renda_liquida, dados["taxa_juros_anual"],
        imposto=None, modo=modo, valor_final_desejado=outro_valor
    )

    aporte = resultado.get("aporte_mensal")
    regime = resultado.get("regime")

    if aporte is None:
        st.warning("Com os parâmetros informados, não é possível atingir o objetivo de aposentadoria.")
        st.stop()

    if aporte == 0:
        st.success("🎉 Sua poupança atual já é suficiente para atingir o objetivo de aposentadoria. Nenhum aporte mensal é necessário.")
        st.stop()

    # (continua normalmente com gráficos e Excel export...)
