
import streamlit as st
import pandas as pd
from core import simular_aposentadoria
from io import BytesIO

st.set_page_config(page_title="Simulador de Aposentadoria", layout="centered")

st.title("💼 Simulador de Aposentadoria")

with st.form("form_inputs"):
    st.markdown("### 📋 Dados Iniciais")
    col1, col2 = st.columns(2)
    with col1:
        idade_atual = st.number_input("Idade atual", min_value=18, max_value=100, value=42)
        renda_atual = st.number_input("Renda atual (R$)", min_value=0.0, value=70000.0, step=1000.0)
        poupanca_atual = st.number_input("Poupança atual (R$)", min_value=0.0, value=1_000_000.0, step=1000.0)
    with col2:
        idade_aposentadoria = st.number_input("Idade para aposentadoria", min_value=idade_atual+1, max_value=100, value=65)
        idade_morte = st.number_input("Idade esperada de vida", min_value=idade_aposentadoria+1, max_value=120, value=95)

    st.markdown("### 📊 Dados Econômicos")
    col3, col4 = st.columns(2)
    with col3:
        taxa_juros_anual = st.number_input("Taxa real de juros anual (%)", min_value=0.0, max_value=1.0, value=0.05, step=0.005)
    with col4:
        imposto_renda = st.number_input("Imposto sobre rendimento (%)", min_value=0.0, max_value=1.0, value=0.15, step=0.01)

    st.markdown("### 💵 Renda na Aposentadoria")
    col5, col6 = st.columns(2)
    with col5:
        renda_desejada = st.number_input("Renda mensal desejada (R$)", min_value=0.0, value=40000.0)
    with col6:
        previdencia = st.number_input("Previdência (R$)", min_value=0.0, value=0.0)
        outras_rendas = st.number_input("Outras rendas mensais (R$)", min_value=0.0, value=0.0)

    st.markdown("### 🎯 Objetivo Final")
    objetivo = st.selectbox("O que deseja ao final da vida?", options=["manter", "zerar", "outro valor"])
    outro_valor = 0.0
    if objetivo == "outro valor":
        outro_valor = st.number_input("Valor final desejado (R$)", min_value=0.0, value=5_000_000.0)

    submitted = st.form_submit_button("📈 Definir Aportes")

if submitted:
    dados = {
        "idade_atual": idade_atual,
        "idade_aposentadoria": idade_aposentadoria,
        "idade_morte": idade_morte,
        "renda_desejada": renda_desejada,
        "taxa_juros_anual": taxa_juros_anual,
        "imposto_renda": imposto_renda,
        "valor_inicial": poupanca_atual,
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
        st.success(f"💰 Aporte mensal ideal: R$ {aporte:,.2f}")

        poupanca_necessaria = patrimonio[len(patrimonio) if objetivo == "zerar" else len(range((idade_aposentadoria - idade_atual + 1) * 12))]
        percentual_renda = aporte / renda_atual if renda_atual else 0

        st.markdown("### 📊 Resultado Resumido")
        col7, col8, col9 = st.columns(3)
        col7.metric("Aportes mensais", f"R$ {aporte:,.2f}")
        col8.metric("Poupança necessária", f"R$ {poupanca_necessaria:,.2f}")
        col9.metric("Percentual da renda atual", f"{percentual_renda*100:.2f}%")

        st.markdown("### 📈 Evolução do Patrimônio")
        st.line_chart(patrimonio)

        st.markdown("### 📤 Exportar dados")
        df_export = pd.DataFrame({
            "Mês": list(range(len(patrimonio))),
            "Patrimônio": patrimonio
        })

        def gerar_excel():
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Simulação')
            output.seek(0)
            return output

        st.download_button(
            label="📥 Baixar Excel",
            data=gerar_excel(),
            file_name="simulacao_aposentadoria.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
