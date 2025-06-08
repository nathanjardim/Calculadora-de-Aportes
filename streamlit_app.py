import streamlit as st
import pandas as pd
from core import (
    taxa_mensal, calcular_meses_acc, calcular_meses_cons,
    gerar_cotas, bissecao, calcular_aporte
)

st.set_page_config(page_title="Wealth Planning", layout="wide")

st.title("💼 Wealth Planning – Simulador de Aposentadoria")
st.markdown("Preencha seus dados abaixo para calcular o aporte mensal ideal.")

col1, col2, col3 = st.columns(3)

with col1:
    renda_desejada = st.number_input("Renda mensal desejada (R$)", min_value=0.0, value=5000.0)
    idade_aposentadoria = st.number_input("Idade aposentadoria", min_value=0, max_value=100, value=65)
    idade_fim = st.number_input("Idade fim", min_value=0, max_value=120, value=85)

with col2:
    idade_atual = st.number_input("Idade atual", min_value=0, max_value=100, value=30)
    valor_inicial = st.number_input("Poupança atual (R$)", min_value=0.0, value=10000.0)

with col3:
    taxa_juros = st.number_input("Taxa de juros real (%aa)", min_value=0.0, max_value=100.0, value=8.0) / 100
    imposto = st.number_input("IR (%)", min_value=0.0, max_value=100.0, value=15.0) / 100
    tipo_objetivo = st.selectbox("Patrimônio final", ["manter", "zerar", "outro valor"])
    outro_valor = st.number_input("Se outro valor, qual?", min_value=0.0, value=1000000.0) if tipo_objetivo == "outro valor" else None

st.markdown("---")
previdencia = st.number_input("Previdência esperada (R$)", min_value=0.0, value=1000.0)
outras_rendas = st.number_input("Aluguel ou outras fontes de renda (R$)", min_value=0.0, value=500.0)

resgate_necessario = renda_desejada - previdencia - outras_rendas

if st.button("Definir Aportes"):
    try:
        taxa = taxa_mensal(taxa_juros)
        meses_acc = calcular_meses_acc(idade_atual, idade_aposentadoria)
        meses_cons = calcular_meses_cons(idade_aposentadoria, idade_fim)

        cota_bruta, matriz_cotas_liq = gerar_cotas(taxa, meses_acc, meses_cons, valor_inicial, imposto)
        aporte = bissecao(tipo_objetivo.lower(), outro_valor, valor_inicial, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario)
        patrimonio, _ = calcular_aporte(aporte, valor_inicial, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario)

        st.success(f"Aportes mensais: R$ {aporte:,.2f}")
        st.write(f"Poupança necessária: R$ {patrimonio[meses_acc + 1]:,.2f}")
        st.write(f"Anos de aportes: {round(meses_acc / 12)}")
        st.write(f"Percentual da renda atual: {aporte / renda_desejada * 100:.2f}%")

        df = pd.DataFrame({
            "Idade": list(range(idade_atual, idade_atual + len(patrimonio) // 12 + 1)),
            "Patrimônio": [
                sum(patrimonio[i*12:(i+1)*12]) / 12
                for i in range(len(patrimonio) // 12 + 1)
            ]
        })
        st.line_chart(df.set_index("Idade"))

    except Exception as e:
        st.error(f"⚠️ Erro: {str(e)}")
