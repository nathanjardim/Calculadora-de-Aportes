import sys
import os
sys.path.append(os.path.dirname(__file__))

from core import calcular_aporte, simular_aposentadoria

import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO

def verificar_alertas(inputs, aporte_calculado=None):
    erros = []
    alertas = []
    informativos = []

    idade_atual = inputs["idade_atual"]
    idade_aposentadoria = inputs["idade_aposentadoria"]
    expectativa_vida = inputs["expectativa_vida"]
    renda_atual = inputs["renda_atual"]
    renda_desejada = inputs["renda_desejada"]
    poupanca = inputs["poupanca"]
    taxa = inputs["taxa_juros_anual"]
    imposto = inputs["imposto"]

    tempo_aporte = idade_aposentadoria - idade_atual

    if idade_atual >= idade_aposentadoria:
        erros.append("A idade atual deve ser menor que a idade de aposentadoria.")
    if expectativa_vida <= idade_aposentadoria:
        erros.append("A expectativa de vida deve ser maior que a idade de aposentadoria.")
    if renda_atual <= 0:
        erros.append("Renda atual inválida. Verifique o campo preenchido.")
    if taxa < 0 or taxa > 1:
        erros.append("Taxa de juros fora do intervalo permitido. Verifique os parâmetros.")
    if imposto < 0 or imposto > 1:
        erros.append("Alíquota de imposto fora do intervalo permitido. Verifique os parâmetros.")
    if aporte_calculado is not None and aporte_calculado > renda_atual:
        erros.append("Aporte calculado maior que a renda atual. Verifique os parâmetros.")

    if taxa > 0.10:
        alertas.append("Taxa de juros real elevada. Verifique os parâmetros.")
    if tempo_aporte < 5:
        alertas.append("Prazo muito curto até a aposentadoria. Verifique os parâmetros.")
    if tempo_aporte > 50:
        alertas.append("Prazo muito longo até a aposentadoria. Verifique os parâmetros.")
    if renda_desejada > 10 * renda_atual:
        alertas.append("Renda desejada superior à renda atual. Verifique os parâmetros.")
    if aporte_calculado is not None and aporte_calculado > 0.5 * renda_atual:
        alertas.append("Aporte elevado em relação à renda. Verifique os parâmetros.")

    if imposto > 0.275:
        informativos.append("Imposto acima da alíquota padrão. Confirme o valor informado.")
    if aporte_calculado is not None and aporte_calculado < 10:
        informativos.append("Aporte muito baixo detectado. Confirme os parâmetros utilizados.")
    if poupanca > 0 and aporte_calculado is not None and poupanca > aporte_calculado * tempo_aporte * 12:
        informativos.append("Poupança inicial superior ao necessário. Verifique os dados.")
    if renda_desejada == 0:
        informativos.append("Renda desejada igual a zero. Verifique os parâmetros.")

    return erros, alertas, informativos

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

with st.form("formulario"):
    st.markdown("### 📋 Dados Iniciais")
    renda_atual = st.number_input("Renda atual (R$)", min_value=0.0, step=100.0, value=10000.0)
    idade_atual = st.number_input("Idade atual", min_value=18, max_value=100, value=30)
    poupanca = st.number_input("Poupança atual (R$)", min_value=0.0, step=1000.0, value=50000.0)

    st.markdown("### 📊 Dados Econômicos")
    taxa_juros = st.number_input("Taxa de juros real anual (%)", min_value=0.0, max_value=100.0, value=5.0)
    imposto = st.number_input("Alíquota de IR (%)", min_value=0.0, max_value=100.0, value=15.0)

    st.markdown("### 🏁 Aposentadoria")
    renda_desejada = st.number_input("Renda mensal desejada (R$)", min_value=0.0, step=500.0, value=15000.0)
    idade_aposentadoria = st.number_input("Idade para aposentadoria", min_value=idade_atual + 1, max_value=100, value=65)
    expectativa_vida = st.number_input("Expectativa de vida", min_value=idade_aposentadoria + 1, max_value=120, value=90)

    st.markdown("### 🎯 Objetivo Final")
    modo = st.selectbox("Objetivo com o patrimônio", ["manter", "zerar", "atingir"])
    outro_valor = None
    if modo == "atingir":
        outro_valor = st.number_input("Valor alvo (R$)", min_value=0.0, step=10000.0)

    submitted = st.form_submit_button("📈 Calcular")

if submitted:
    dados = {
        "idade_atual": idade_atual,
        "idade_aposentadoria": idade_aposentadoria,
        "expectativa_vida": expectativa_vida,
        "renda_atual": renda_atual,
        "renda_desejada": renda_desejada,
        "poupanca": poupanca,
        "taxa_juros_anual": taxa_juros / 100,
        "imposto": imposto / 100,
    }

    resultado = calcular_aporte(
        idade_atual, idade_aposentadoria, expectativa_vida,
        poupanca, renda_desejada, dados["taxa_juros_anual"],
        dados["imposto"], modo, outro_valor
    )

    aporte = resultado.get("aporte_mensal")

    erros, alertas, informativos = verificar_alertas(dados, aporte)

    for e in erros:
        st.error(e)
    for a in alertas:
        st.warning(a)
    for i in informativos:
        st.info(i)

    if not erros and aporte is not None:
        _, _, patrimonio = simular_aposentadoria(
            idade_atual, idade_aposentadoria, expectativa_vida,
            poupanca, aporte, renda_desejada,
            dados["taxa_juros_anual"], dados["imposto"]
        )

        anos_aporte = idade_aposentadoria - idade_atual
        percentual = aporte / renda_atual * 100
        patrimonio_final = patrimonio[(anos_aporte) * 12]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 💰 Aporte mensal")
            st.markdown(f"<h3 style='margin-top:0'>R$ {aporte:,.2f}</h3>", unsafe_allow_html=True)

            st.markdown("#### 🏦 Poupança necessária")
            st.markdown(f"<h3 style='margin-top:0'>R$ {patrimonio_final:,.2f}</h3>", unsafe_allow_html=True)

        with col2:
            st.markdown("#### 📆 Anos de aportes")
            st.markdown(f"<h3 style='margin-top:0'>{anos_aporte} anos</h3>", unsafe_allow_html=True)

            st.markdown("#### 📊 % da renda atual")
            st.markdown(f"<h3 style='margin-top:0'>{percentual:.2f}%</h3>", unsafe_allow_html=True)

        st.markdown("### 📈 Evolução do Patrimônio")
        df_chart = pd.DataFrame({
            "Idade": [idade_atual + i / 12 for i in range(len(patrimonio))],
            "Montante": patrimonio
        })
        df_chart = df_chart[df_chart["Idade"] % 1 == 0].reset_index(drop=True)
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

        st.markdown("### 📥 Exportar dados")

        def gerar_excel():
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                workbook = writer.book
                worksheet = workbook.add_worksheet("Simulação")
                writer.sheets["Simulação"] = worksheet

                bold = workbook.add_format({'bold': True})
                money = workbook.add_format({'num_format': 'R$ #,##0.00'})
                percent_fmt = workbook.add_format({'num_format': '0.00%'})
                header_format = workbook.add_format({'bold': True, 'bg_color': '#123934', 'font_color': 'white'})

                worksheet.write("A6", "💰 Aporte mensal", bold)
                worksheet.write("B6", aporte, money)
                worksheet.write("A7", "🏦 Poupança necessária", bold)
                worksheet.write("B7", patrimonio_final, money)
                worksheet.write("A8", "📆 Anos de aportes", bold)
                worksheet.write("B8", anos_aporte)
                worksheet.write("A9", "📊 % da renda atual", bold)
                worksheet.write("B9", percentual / 100, percent_fmt)

                df_export = df_chart[["Idade", "Montante"]]
                df_export.columns = ["Idade", "Patrimônio"]
                df_export.to_excel(writer, index=False, sheet_name="Simulação", startrow=11, header=False)

                for col_num, value in enumerate(df_export.columns.values):
                    worksheet.write(10, col_num, value, header_format)

                worksheet.set_column("A:A", 10)
                worksheet.set_column("B:B", 20, money)

            output.seek(0)
            return output

        st.download_button(
            label="📥 Baixar Excel",
            data=gerar_excel(),
            file_name="simulacao_aposentadoria.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
