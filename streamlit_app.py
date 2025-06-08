import streamlit as st
from core import (
    taxa_mensal,
    calcular_meses_acc,
    calcular_meses_cons,
    gerar_cotas,
    calcular_aporte,
    bissecao
)

st.set_page_config(page_title="Simulador de Aposentadoria", layout="centered")
st.title("📈 Simulador de Aportes para Aposentadoria")

# Inputs
st.sidebar.header("Parâmetros de Entrada")

idade_atual = st.sidebar.number_input("Idade Atual", min_value=18, max_value=100, value=30)
idade_aposentadoria = st.sidebar.number_input("Idade de Aposentadoria", min_value=idade_atual + 1, max_value=100, value=60)
idade_morte = st.sidebar.number_input("Idade Esperada de Vida", min_value=idade_aposentadoria + 1, max_value=120, value=85)

renda_desejada = st.sidebar.number_input("Renda Mensal Desejada na Aposentadoria (R$)", min_value=0.0, value=8000.0)
valor_inicial = st.sidebar.number_input("Valor Inicial Acumulado (R$)", min_value=0.0, value=0.0)
taxa_juros_anual = st.sidebar.number_input("Rentabilidade Anual Esperada (%)", min_value=0.0, max_value=100.0, value=8.0) / 100
imposto_renda = st.sidebar.number_input("Alíquota de IR sobre rendimentos (%)", min_value=0.0, max_value=100.0, value=10.0) / 100

outras_rendas = st.sidebar.number_input("Outras Rendas na Aposentadoria (R$)", min_value=0.0, value=0.0)
previdencia = st.sidebar.number_input("Renda Prevista de Previdência (R$)", min_value=0.0, value=0.0)

tipo_objetivo = st.sidebar.selectbox("Objetivo Final do Patrimônio", options=["Manter", "Zerar", "Outro valor"])
outro_valor = st.sidebar.number_input("Valor desejado ao final da vida (R$)", min_value=0.0, value=500000.0) if tipo_objetivo == "Outro valor" else None

# Calcular ao clicar
if st.button("Calcular Aporte Ideal"):
    meses_acc = calcular_meses_acc(idade_atual, idade_aposentadoria)
    meses_cons = calcular_meses_cons(idade_aposentadoria, idade_morte)
    taxa = taxa_mensal(taxa_juros_anual)
    cota_bruta, matriz_cotas_liq = gerar_cotas(taxa, meses_acc, meses_cons, valor_inicial, imposto_renda)
    resgate_necessario = renda_desejada - outras_rendas - previdencia

    aporte_ideal = bissecao(tipo_objetivo.lower(), outro_valor, valor_inicial, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario)
    patrimonio = calcular_aporte(aporte_ideal, valor_inicial, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario)[0]

    st.success(f"💰 Aporte ideal: R$ {aporte_ideal:,.2f}/mês")
    st.line_chart(patrimonio)
