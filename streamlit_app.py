import sys
import os
sys.path.append(os.path.dirname(__file__))

from core import calcular_aporte, simular_aposentadoria

import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO

st.set_page_config(page_title="Wealth Planning", layout="wide")

st.markdown("""
    <style>
    .header {
        background-color: #123934;
        padding: 20px 10px;
        text-align: center;
    }
    .header img {
        max-width: 200px;
        height: auto;
    }
    </style>
    <div class="header">
      <img src="https://i.imgur.com/iCRuacp.png" alt="Logo Sow Capital">
    </div>
""", unsafe_allow_html=True)

st.title("Wealth Planning")

with st.form("form_inputs"):
    st.markdown("### 📋 Dados Iniciais")
    renda_atual = st.number_input("Renda atual (R$)", min_value=0, step=1000, value=10000)
    idade_atual = st.number_input("Idade atual", min_value=18, max_value=100, step=1, value=30)
    poupanca_atual = st.number_input("Poupança atual (R$)", min_value=0, step=1000, value=50000)

    st.markdown("### 📊 Dados Econômicos")
    taxa_juros_percentual = st.number_input("Taxa de juros real anual (%)", min_value=0.0, max_value=100.0, value=5.0, step=0.1)
    imposto_renda_percentual = st.number_input("IR sobre resgates (%)", min_value=0.0, max_value=100.0, value=15.0, step=0.1)
    taxa_juros_anual = taxa_juros_percentual / 100
    imposto_renda = imposto_renda_percentual / 100

    st.markdown("### 🏁 Aposentadoria")
    renda_desejada = st.number_input("Renda mensal desejada (R$)", min_value=0, step=1000, value=15000)
    idade_aposentadoria = st.number_input("Idade para aposentadoria", min_value=19, max_value=100, step=1, value=65)
    expectativa_vida = st.number_input("Expectativa de vida", min_value=20, max_value=120, value=90, step=1)

    st.markdown("### 🎯 Fim do Patrimônio")
    modo = st.selectbox("Objetivo", options=["manter", "zerar", "atingir"])
    outro_valor = None
    if modo == "atingir":
        outro_valor = st.number_input("Se outro valor, qual? (R$)", min_value=0, step=10000)

    submitted = st.form_submit_button("📈 Definir Aportes")

if submitted:
    erros = []
    if idade_atual >= idade_aposentadoria:
        erros.append("A idade atual deve ser menor que a idade de aposentadoria.")
    if expectativa_vida <= idade_aposentadoria:
        erros.append("A expectativa de vida deve ser maior que a idade de aposentadoria.")
    if not (0 <= imposto_renda < 1):
        erros.append("Imposto deve estar entre 0% e 100%.")
    if not (0 <= taxa_juros_anual <= 1):
        erros.append("Rentabilidade deve estar entre 0% e 100%.")
    if renda_atual <= 0:
        erros.append("Renda atual deve ser maior que zero.")

    if erros:
        for e in erros:
            st.error(e)
        st.stop()

    resultado = calcular_aporte(
        idade_atual=int(idade_atual),
        idade_aposentadoria=int(idade_aposentadoria),
        expectativa_vida=int(expectativa_vida),
        poupanca_inicial=poupanca_atual,
        renda_mensal=renda_desejada,
        rentabilidade_anual=taxa_juros_anual,
        imposto=imposto_renda,
        modo=modo,
        valor_final_desejado=outro_valor
    )

    aporte_mensal = resultado["aporte_mensal"]

    if aporte_mensal is None:
        st.error("❌ Não é possível atingir o objetivo com os parâmetros fornecidos.")
        st.stop()

    st.success(f"💰 Aporte mensal ideal: R$ {aporte_mensal:.2f}")

    percentual = aporte_mensal / renda_atual
    st.metric("Percentual da renda atual", f"{percentual*100:.1f}%")

    _, _, patrimonio = simular_aposentadoria(
        idade_atual=int(idade_atual),
        idade_aposentadoria=int(idade_aposentadoria),
        expectativa_vida=int(expectativa_vida),
        poupanca_inicial=poupanca_atual,
        aporte_mensal=aporte_mensal,
        renda_mensal=renda_desejada,
        rentabilidade_anual=taxa_juros_anual,
        imposto=imposto_renda
    )

    st.markdown("### 📈 Evolução do Patrimônio")
    df_chart = pd.DataFrame({
        "Idade": [idade_atual + i / 12 for i in range(len(patrimonio))],
        "Montante": patrimonio
    })

    df_chart["Montante formatado"] = df_chart["Montante"].apply(lambda v: f"R$ {v:,.0f}".replace(",", "."))

    chart = alt.Chart(df_chart).mark_line(interpolate="monotone").encode(
        x=alt.X("Idade", title="Idade", axis=alt.Axis(format=".0f")),
        y=alt.Y("Montante", title="Patrimônio acumulado", axis=alt.Axis(format=".2s")),
        tooltip=[
            alt.Tooltip("Idade", title="Idade", format=".1f"),
            alt.Tooltip("Montante formatado", title="Montante")
        ]
    ).properties(width=700, height=400)

    st.altair_chart(chart, use_container_width=True)

    st.markdown("### 📤 Exportar dados")
    df_export = pd.DataFrame({
        "Idade": df_chart["Idade"],
        "Patrimônio": df_chart["Montante"]
    })

    def gerar_excel():
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_export.to_excel(writer, index=False, sheet_name="Simulação")
        output.seek(0)
        return output

    st.download_button(
        label="📥 Baixar Excel",
        data=gerar_excel(),
        file_name="simulacao_aposentadoria.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
