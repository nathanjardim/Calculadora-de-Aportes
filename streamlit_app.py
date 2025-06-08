import streamlit as st
import matplotlib.pyplot as plt
from core import (
    taxa_mensal,
    calcular_meses_acc,
    calcular_meses_cons,
    gerar_cotas,
    calcular_aporte,
    bissecao
)

st.set_page_config(page_title="Wealth Planning", layout="wide")
st.title("💼 Wealth Planning - Simulador de Aportes para Aposentadoria")
st.markdown("---")

# 📌 Dados Iniciais
st.markdown("### 📌 Dados Iniciais")
col1, col2, col3 = st.columns(3)
with col1:
    renda_atual = st.number_input("Renda atual", min_value=0.0, value=7000.0, step=500.0)
with col2:
    idade_atual = st.number_input("Idade atual", min_value=0, max_value=100, value=30)
with col3:
    poupanca_atual = st.number_input("Poupança atual", min_value=0.0, value=200000.0, step=10000.0)

# 📈 Dados Econômicos
st.markdown("### 📈 Dados Econômicos")
col4, col5 = st.columns(2)
with col4:
    taxa_juros_anual = st.number_input("Taxa de juros real (%aa)", min_value=0.0, max_value=100.0, value=8.0) / 100
with col5:
    imposto_renda = st.number_input("IR (%)", min_value=0.0, max_value=100.0, value=15.0) / 100

# 🧓 Aposentadoria
st.markdown("### 🧓 Aposentadoria")
col6, col7 = st.columns(2)
with col6:
    renda_desejada = st.number_input("Renda mensal desejada", min_value=0.0, value=6000.0, step=500.0)
with col7:
    idade_aposentadoria = st.number_input("Idade aposentadoria", min_value=0, max_value=100, value=60)

idade_fim = st.number_input("Idade fim", min_value=0, max_value=120, value=85)

# 💸 Renda Extra
st.markdown("### 💸 Renda Extra")
col8, col9 = st.columns(2)
with col8:
    previdencia = st.number_input("Previdência", min_value=0.0, value=1500.0)
with col9:
    outras_rendas = st.number_input("Aluguel ou outras fontes de renda", min_value=0.0, value=1000.0)

resgate_necessario = renda_desejada - previdencia - outras_rendas

# 🎯 Objetivo
st.markdown("### 🎯 Objetivo do Patrimônio Final")
col10, col11 = st.columns([1, 2])
with col10:
    tipo_objetivo = st.selectbox("Deseja manter, zerar ou deixar um valor final?", ["manter", "zerar", "outro valor"], index=0)
with col11:
    outro_valor = st.number_input("Se outro valor, qual?", min_value=0.0, value=0.0) if tipo_objetivo == "outro valor" else None

# ▶️ Calcular
if st.button("Calcular aporte ideal"):
    try:
        taxa = taxa_mensal(taxa_juros_anual)
        meses_acc = calcular_meses_acc(idade_atual, idade_aposentadoria)
        meses_cons = calcular_meses_cons(idade_aposentadoria, idade_fim)
        cota_bruta, matriz_cotas_liq = gerar_cotas(taxa, meses_acc, meses_cons, poupanca_atual, imposto_renda)

        aporte_ideal = bissecao(
            tipo_objetivo.lower(),
            outro_valor,
            poupanca_atual,
            meses_acc,
            taxa,
            cota_bruta,
            matriz_cotas_liq,
            resgate_necessario
        )

        patrimonio, _ = calcular_aporte(aporte_ideal, poupanca_atual, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario)

        st.success(f"✅ Aporte mensal ideal: R$ {aporte_ideal:,.2f}")
        st.write(f"📊 Patrimônio ao se aposentar: R$ {patrimonio[meses_acc]:,.2f}")
        st.write(f"📈 Patrimônio final aos {idade_fim} anos: R$ {patrimonio[-1]:,.2f}")

        # 📉 Gráfico
        st.markdown("### 📊 Evolução do Patrimônio")
        anos = list(range(idade_atual, idade_fim + 1))
        patrimonio_anual = [patrimonio[i * 12] for i in range(len(anos))]

        fig, ax = plt.subplots()
        ax.plot(anos, patrimonio_anual, marker="o", linestyle="-", linewidth=2)
        ax.set_xlabel("Idade")
        ax.set_ylabel("Patrimônio (R$)")
        ax.set_title("Projeção do Patrimônio ao Longo do Tempo")
        ax.grid(True)
        ax.legend(["Patrimônio acumulado"])
        st.pyplot(fig)

    except Exception as e:
        st.error(f"⚠️ Erro: {str(e)}")
