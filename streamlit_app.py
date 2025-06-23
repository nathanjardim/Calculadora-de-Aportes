import sys
import os
sys.path.append(os.path.dirname(__file__))

import streamlit as st
st.set_page_config(page_title="Wealth Planning", layout="wide")

from core import calcular_aporte, simular_aposentadoria
import pandas as pd
import altair as alt
from io import BytesIO

def formatar_moeda(valor, decimais=0):
    return f"R$ {valor:,.{decimais}f}".replace(",", "X").replace(".", ",").replace("X", ".")

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

def verificar_alertas(inputs, aporte_calculado=None):
    # (função inalterada)
    ...

st.markdown("""<style> ... </style>""", unsafe_allow_html=True)

st.title("Wealth Planning")

with st.form("formulario"):
    st.markdown("### 📋 Dados Iniciais")
    renda_atual = st.number_input("Renda atual (R$)", min_value=0.0, step=100.0, value=10000.0, format="%.0f")
    idade_atual = st.number_input("Idade atual", min_value=18.0, max_value=100.0, value=30.0, format="%.0f")
    poupanca = st.number_input("Poupança atual (R$)", min_value=0.0, step=1000.0, value=50000.0, format="%.0f")

    st.markdown("### 📊 Dados Econômicos")
    taxa_juros = st.number_input("Taxa de juros real anual (%)", min_value=0.0, max_value=100.0, value=5.0, format="%.0f")
    imposto = st.number_input("Alíquota de IR (%)", min_value=0.0, max_value=100.0, value=15.0, format="%.0f")

    st.markdown("### 🧾 Renda desejada na aposentadoria")
    renda_desejada = st.number_input("Renda mensal desejada (R$)", min_value=0.0, step=500.0, value=15000.0, format="%.0f")
    plano_saude = st.number_input("Plano de saúde (R$)", min_value=0.0, step=100.0, value=0.0, format="%.0f")
    outras_despesas = st.number_input("Outras despesas planejadas (R$)", min_value=0.0, step=100.0, value=0.0, format="%.0f")

    st.markdown("### 💸 Renda passiva estimada")
    previdencia = st.number_input("Renda com previdência (R$)", min_value=0.0, step=100.0, value=0.0, format="%.0f")
    aluguel_ou_outras = st.number_input("Aluguel ou outras fontes de renda (R$)", min_value=0.0, step=100.0, value=0.0, format="%.0f")

    st.markdown("### 🧓 Dados da aposentadoria")
    idade_aposentadoria = st.number_input("Idade para aposentadoria", min_value=idade_atual + 1, max_value=100.0, value=65.0, format="%.0f")
    expectativa_vida = st.number_input("Expectativa de vida", min_value=idade_aposentadoria + 1, max_value=120.0, value=90.0, format="%.0f")

    st.markdown("### 🎯 Objetivo Final")
    modo = st.selectbox("Objetivo com o patrimônio", ["manter", "zerar", "atingir"])
    outro_valor = None
    if modo == "atingir":
        outro_valor = st.number_input("Valor alvo (R$)", min_value=0.0, step=10000.0, format="%.0f")

    submitted = st.form_submit_button("📈 Calcular")

if submitted:
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
        "imposto": imposto / 100,
    }

    # 🔍 DEBUG AQUI
    st.write("🔍 DEBUG INPUTS:", {
        "idade_atual": dados["idade_atual"],
        "idade_aposentadoria": dados["idade_aposentadoria"],
        "expectativa_vida": dados["expectativa_vida"],
        "poupanca": dados["poupanca"],
        "renda_liquida": renda_liquida,
        "taxa_juros_anual": dados["taxa_juros_anual"],
        "imposto": dados["imposto"],
        "modo": modo,
    })

    resultado = calcular_aporte(
        dados["idade_atual"], dados["idade_aposentadoria"], dados["expectativa_vida"],
        dados["poupanca"], renda_liquida, dados["taxa_juros_anual"],
        dados["imposto"], modo, outro_valor
    )

    # resto inalterado...
