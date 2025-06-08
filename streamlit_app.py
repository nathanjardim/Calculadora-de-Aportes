import streamlit as st
import matplotlib.pyplot as plt
from core import *

st.set_page_config(page_title="Wealth Planning", layout="wide")
st.title("💼 Wealth Planning – Simulador de Aposentadoria")

st.markdown("Preencha seus dados para descobrir o aporte mensal ideal para atingir seus objetivos.")
st.markdown("---")

# 📌 Dados Iniciais
with st.expander("📌 Dados Iniciais", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        renda_atual = st.number_input("Renda atual", value=7000.0, step=500.0)
    with col2:
        idade_atual = st.number_input("Idade atual", value=30, step=1)
    with col3:
        poupanca_atual = st.number_input("Poupança atual", value=200000.0, step=10000.0)

# 📈 Parâmetros Econômicos
with st.expander("📈 Parâmetros Econômicos", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        taxa_juros_anual = st.number_input("Taxa de juros real (%aa)", value=8.0) / 100
    with col2:
        imposto_renda = st.number_input("IR (%)", value=15.0) / 100

# 🧓 Aposentadoria
with st.expander("🧓 Aposentadoria", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        renda_desejada = st.number_input("Renda mensal desejada", value=6000.0)
    with col2:
        idade_aposentadoria = st.number_input("Idade aposentadoria", value=60, step=1)

    idade_fim = st.number_input("Idade fim", value=85, step=1)

# 💸 Renda
with st.expander("💸 Renda", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        previdencia = st.number_input("Previdência esperada", value=1500.0)
    with col2:
        outras_rendas = st.number_input("Outras rendas mensais", value=1000.0)

resgate_necessario = renda_desejada - previdencia - outras_rendas

# 🎯 Fim do Patrimônio
with st.expander("🎯 Fim do Patrimônio", expanded=True):
    col1, col2 = st.columns([1, 2])
    with col1:
        tipo_objetivo = st.selectbox("O que deseja ao final?", ["manter", "zerar", "outro valor"], index=0)
    with col2:
        outro_valor = st.number_input("Se outro valor, qual?", value=100000.0) if tipo_objetivo == "outro valor" else None

# ▶️ Resultado
st.markdown("### 🚀 Resultado")
if st.button("Calcular Aporte Ideal"):
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

        if aporte_ideal is None:
            st.error("⚠️ Não foi possível encontrar um aporte que satisfaça o objetivo dentro do limite de iterações.")
        else:
            patrimonio, _ = calcular_aporte(aporte_ideal, poupanca_atual, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario)
            st.success(f"✅ Aporte mensal ideal: R$ {aporte_ideal:,.2f}")
            st.markdown(f"📊 Patrimônio ao se aposentar (idade {idade_aposentadoria}): R$ {patrimonio[meses_acc]:,.2f}")
            st.markdown(f"📈 Patrimônio final aos {idade_fim} anos: R$ {patrimonio[-1]:,.2f}")

            # Gráfico anual suave
            anos = list(range(idade_atual, idade_fim + 1))
            patrimonio_anual = [patrimonio[i * 12] for i in range(len(anos))]

            fig, ax = plt.subplots()
            ax.plot(anos, patrimonio_anual, label="Evolução do Patrimônio", color="orange", linewidth=2)
            ax.set_xlabel("Idade")
            ax.set_ylabel("Valor (R$)")
            ax.set_title("Projeção do Patrimônio ao Longo do Tempo")
            ax.legend()
            ax.grid(True)
            st.pyplot(fig)

    except Exception as e:
        st.error(f"⚠️ Erro: {e}")
