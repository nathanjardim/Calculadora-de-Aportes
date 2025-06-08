import streamlit as st
import pandas as pd
from core import (
    taxa_mensal, calcular_meses_acc, calcular_meses_cons,
    gerar_cotas, bissecao, calcular_aporte
)

st.set_page_config(page_title="Wealth Planning", layout="wide")
st.title("💼 Wealth Planning – Simulador de Aposentadoria")

st.markdown("### Legenda:")
st.text_input("Legenda:", label_visibility="collapsed")
st.markdown("")

# BLOCO 1: DADOS INICIAIS
st.markdown("#### 📌 Dados Iniciais")
col1, col2, col3 = st.columns(3)
with col1:
    renda_atual = st.number_input("Renda atual", min_value=0.0, value=70000.0, step=1000.0, format="%.2f")
with col2:
    idade_atual = st.number_input("Idade atual", min_value=0, max_value=100, value=42)
with col3:
    poupanca_atual = st.number_input("Poupança atual", min_value=0.0, value=1_000_000.0, step=10000.0, format="%.2f")

# BLOCO 2: DADOS ECONÔMICOS
st.markdown("#### 📈 Dados Econômicos")
col4, col5 = st.columns(2)
with col4:
    taxa_juros_anual = st.number_input("Taxa de juros real (%aa)", min_value=0.0, max_value=100.0, value=5.0, step=0.5) / 100
with col5:
    imposto_renda = st.number_input("IR (%)", min_value=0.0, max_value=100.0, value=15.0, step=1.0) / 100

# BLOCO 3: APOSENTADORIA
st.markdown("#### 🧓 Aposentadoria")
col6, col7 = st.columns(2)
with col6:
    renda_desejada = st.number_input("Renda mensal desejada", min_value=0.0, value=40000.0, step=500.0)
with col7:
    idade_aposentadoria = st.number_input("Idade aposentadoria", min_value=0, max_value=100, value=65)

idade_fim = st.number_input("Idade fim", min_value=0, max_value=120, value=95)

# BLOCO 4: RENDA
st.markdown("#### 💸 Renda")
col8, col9 = st.columns(2)
with col8:
    previdencia = st.number_input("Previdência", min_value=0.0, value=0.0)
with col9:
    outras_rendas = st.number_input("Aluguel ou outras fontes de rendas", min_value=0.0, value=0.0)

resgate_necessario = renda_desejada - previdencia - outras_rendas

# BLOCO 5: OBJETIVO
st.markdown("#### 🎯 Fim do Patrimônio")
col10, col11 = st.columns([1, 2])
with col10:
    tipo_objetivo = st.selectbox("Patrimônio final", ["manter", "zerar", "outro valor"])
with col11:
    outro_valor = st.number_input("Se outro valor, qual?", min_value=0.0, value=0.0) if tipo_objetivo == "outro valor" else None

# BOTÃO FINAL
st.markdown("### 🚀 Resultado")
if st.button("Calcular Aporte Ideal"):
    try:
        taxa = taxa_mensal(taxa_juros_anual)
        meses_acc = calcular_meses_acc(idade_atual, idade_aposentadoria)
        meses_cons = calcular_meses_cons(idade_aposentadoria, idade_fim)

        cota_bruta, matriz_cotas_liq = gerar_cotas(taxa, meses_acc, meses_cons, poupanca_atual, imposto_renda)

        aporte = bissecao(
            tipo_objetivo.lower(),
            outro_valor,
            poupanca_atual,
            meses_acc,
            taxa,
            cota_bruta,
            matriz_cotas_liq,
            resgate_necessario
        )

        patrimonio, _ = calcular_aporte(
            aporte,
            poupanca_atual,
            meses_acc,
            taxa,
            cota_bruta,
            matriz_cotas_liq,
            resgate_necessario
        )

        st.success(f"Aportes mensais: R$ {aporte:,.2f}")
        st.write(f"Poupança necessária: R$ {patrimonio[meses_acc + 1]:,.2f}")
        st.write(f"Anos de aportes: {round(meses_acc / 12)}")
        st.write(f"Percentual da renda atual: {aporte / renda_atual * 100:.2f}%")

        df = pd.DataFrame({
            "Idade": list(range(idade_atual, idade_atual + len(patrimonio) // 12 + 1)),
            "Patrimônio": [
                sum(patrimonio[i*12:(i+1)*12]) / 12
                for i in range(len(patrimonio) // 12 + 1)
            ]
        })

        st.line_chart(df.set_index("Idade"))
        st.caption("🔵 Projeção anual do patrimônio com base nos aportes definidos.")

    except Exception as e:
        st.error(f"⚠️ Erro: {str(e)}")
