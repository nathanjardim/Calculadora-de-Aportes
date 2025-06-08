import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from core import *

st.set_page_config(page_title="Wealth Planning", layout="centered")

st.title("💰 Wealth Planning - Simulador de Aposentadoria")

col1, col2 = st.columns(2)

with col1:
    idade_atual = st.number_input("Idade Atual", value=30)
    idade_aposentadoria = st.number_input("Idade para Aposentadoria", value=60)
    idade_fim = st.number_input("Expectativa de Vida", value=85)
    valor_inicial = st.number_input("Valor Inicial Acumulado (R$)", value=200000)

with col2:
    renda_desejada = st.number_input("Renda Mensal Desejada na Aposentadoria (R$)", value=6000)
    outras_rendas = st.number_input("Outras Rendas Mensais (R$)", value=1000)
    previdencia = st.number_input("Previdência Mensal Esperada (R$)", value=1500)
    taxa_juros = st.number_input("Taxa de Juros Real Anual (%)", value=8.0) / 100

imposto_renda = st.slider("Alíquota de IR (%)", 0, 30, 15) / 100
tipo_objetivo = st.selectbox("Objetivo no final do período", ["manter", "zerar", "outro valor"])

outro_valor = None
if tipo_objetivo == "outro valor":
    outro_valor = st.number_input("Valor desejado ao final (R$)", value=100000)

if st.button("Calcular Aporte Ideal"):
    try:
        meses_acc = (idade_aposentadoria - idade_atual + 1) * 12
        meses_cons = (idade_fim - idade_aposentadoria) * 12
        meses_totais = meses_acc + meses_cons

        taxa = taxa_mensal(taxa_juros)
        resgate_necessario = renda_desejada - outras_rendas - previdencia

        cota_bruta = calcular_cotas(taxa, meses_totais)
        matriz_cotas_liq = calcular_matriz_cotas_liquidas(cota_bruta, meses_acc, imposto_renda)

        aporte_ideal = bissecao(
            tipo_objetivo,
            outro_valor,
            valor_inicial,
            meses_acc,
            taxa,
            cota_bruta,
            matriz_cotas_liq,
            resgate_necessario
        )

        if aporte_ideal is None:
            st.error("⚠️ O sistema não conseguiu calcular um valor de aporte viável com os dados fornecidos. Tente ajustar os parâmetros.")
        else:
            patrimonio, _ = calcular_aporte(aporte_ideal, valor_inicial, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario)
            anos = [idade_atual + i // 12 for i in range(len(patrimonio))]
            plt.figure(figsize=(10, 4))
            plt.plot(anos, patrimonio, label="Evolução do Patrimônio")
            plt.xlabel("Idade")
            plt.ylabel("Valor (R$)")
            plt.legend()
            st.success(f"✅ Aporte mensal ideal: R$ {aporte_ideal:,.2f}")
            st.pyplot(plt)
    except Exception as e:
        st.error(f"⚠️ Erro inesperado: {e}")
