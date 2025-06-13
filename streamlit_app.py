import streamlit as st
import pandas as pd
from core import simular_aposentadoria
from io import BytesIO
import altair as alt

st.set_page_config(page_title="Simulador de Aposentadoria", layout="wide")

# Layout
st.markdown("<h1 style='text-align: center;'>Wealth Planning</h1>", unsafe_allow_html=True)

with st.form("form_inputs"):
    renda_atual = st.number_input("Renda atual (R$)", min_value=0, value=70000, step=1000)
    idade_atual = st.number_input("Idade atual", min_value=18, max_value=100, value=42)
    poupanca_atual = st.number_input("Poupança atual (R$)", min_value=0, value=1_000_000)

    taxa_juros = st.number_input("Taxa de juros real anual (%)", min_value=0, max_value=100, value=5) / 100
    ir = st.number_input("IR (%)", min_value=0, max_value=100, value=15) / 100

    renda_desejada = st.number_input("Renda mensal desejada (R$)", min_value=0, value=40000)
    idade_aposentadoria = st.number_input("Idade para aposentadoria", min_value=idade_atual + 1, max_value=100, value=65)
    idade_morte = st.number_input("Idade fim", min_value=idade_aposentadoria + 1, max_value=120, value=95)

    previdencia = st.number_input("Previdência (R$)", min_value=0, value=0)
    outras_rendas = st.number_input("Outras fontes (R$)", min_value=0, value=0)

    objetivo = st.selectbox("Objetivo", options=["manter", "zerar", "outro valor"])
    outro_valor = 0
    if objetivo == "outro valor":
        outro_valor = st.number_input("Se outro valor, qual? (R$)", min_value=0, value=5000000)

    submitted = st.form_submit_button("Calcular")

if submitted:
    dados = {
        "idade_atual": idade_atual,
        "idade_aposentadoria": idade_aposentadoria,
        "idade_morte": idade_morte,
        "valor_inicial": poupanca_atual,
        "renda_desejada": renda_desejada,
        "outras_rendas": outras_rendas,
        "previdencia": previdencia,
        "taxa_juros_anual": taxa_juros,
        "imposto_renda": ir,
        "tipo_objetivo": objetivo,
        "outro_valor": outro_valor
    }

    aporte, patrimonio, meses_acumulacao = simular_aposentadoria(dados)
    poupanca = patrimonio[meses_acumulacao + 1]
    perc = aporte / renda_atual * 100 if renda_atual else 0

    st.metric("Aportes mensais", f"R$ {aporte:,.2f}")
    st.metric("Poupança necessária", f"R$ {poupanca:,.2f}")
    st.metric("Percentual da renda atual", f"{perc:.2f}%")

    df = pd.DataFrame({
        "Idade": [idade_atual + i / 12 for i in range(len(patrimonio))],
        "Montante": patrimonio
    })

    chart = alt.Chart(df).mark_line().encode(
        x="Idade",
        y="Montante",
        tooltip=["Idade", "Montante"]
    ).properties(width=700, height=400)

    st.altair_chart(chart, use_container_width=True)

    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    st.download_button("📥 Baixar Excel", buffer.getvalue(), file_name="simulacao.xlsx")
