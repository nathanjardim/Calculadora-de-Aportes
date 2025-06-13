
import streamlit as st
from core import simular_aposentadoria

st.set_page_config(page_title="Simulador de Aposentadoria", layout="centered")

st.title("💼 Simulador de Aposentadoria")

with st.form("form_inputs"):
    st.subheader("📥 Dados de entrada")

    col1, col2 = st.columns(2)

    with col1:
        idade_atual = st.number_input("Idade atual", min_value=18, max_value=100, value=42)
        idade_aposentadoria = st.number_input("Idade para aposentadoria", min_value=idade_atual+1, max_value=100, value=65)
        idade_morte = st.number_input("Idade esperada de vida", min_value=idade_aposentadoria+1, max_value=120, value=95)
        valor_inicial = st.number_input("Poupança atual (R$)", min_value=0.0, value=1_000_000.0, step=1000.0)

    with col2:
        renda_desejada = st.number_input("Renda mensal desejada na aposentadoria (R$)", min_value=0.0, value=40000.0)
        taxa_juros_anual = st.number_input("Taxa real de juros anual (%)", min_value=0.0, max_value=1.0, value=0.05, step=0.005)
        imposto_renda = st.number_input("Imposto sobre rendimento (%)", min_value=0.0, max_value=1.0, value=0.15, step=0.01)
        previdencia = st.number_input("Valor mensal recebido de previdência (R$)", min_value=0.0, value=0.0)
        outras_rendas = st.number_input("Outras rendas mensais na aposentadoria (R$)", min_value=0.0, value=0.0)

    objetivo = st.selectbox("Objetivo no fim do período", options=["manter", "zerar", "outro valor"])
    outro_valor = 0.0
    if objetivo == "outro valor":
        outro_valor = st.number_input("Valor final desejado (R$)", min_value=0.0, value=5_000_000.0)

    submitted = st.form_submit_button("Simular")

if submitted:
    dados = {
        "idade_atual": idade_atual,
        "idade_aposentadoria": idade_aposentadoria,
        "idade_morte": idade_morte,
        "renda_desejada": renda_desejada,
        "taxa_juros_anual": taxa_juros_anual,
        "imposto_renda": imposto_renda,
        "valor_inicial": valor_inicial,
        "previdencia": previdencia,
        "outras_rendas": outras_rendas,
        "tipo_objetivo": objetivo,
        "outro_valor": outro_valor,
    }

    with st.spinner("Calculando aporte ideal..."):
        aporte, patrimonio = simular_aposentadoria(dados)

    if isinstance(aporte, str):
        st.error(aporte)
    else:
        st.success(f"Aporte mensal ideal: R$ {aporte:,.2f}")
        st.line_chart(patrimonio)
