import sys
import os
sys.path.append(os.path.dirname(__file__))

from core import calcular_aporte, simular_aposentadoria

import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO

# ====== Função de alertas e validações ======
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

# ====== Configuração da página ======
st.set_page_config(page_title="Simulador de Aposentadoria", layout="wide")

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

st.title("Simulador de Aposentadoria")

# ====== Formulário de Entrada ======
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

# ====== Processamento ======
if submitted:
    inputs = {
        "idade_atual": idade_atual,
        "idade_aposentadoria": idade_aposentadoria,
        "expectativa_vida": expectativa_vida,
        "renda_atual": renda_atual,
        "renda_desejada": renda_desejada,
        "poupanca": poupanca_atual,
        "taxa_juros_anual": taxa_juros_anual,
        "imposto": imposto_renda
    }

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

    erros, alertas, informativos = verificar_alertas(inputs, aporte_mensal)

    for erro in erros:
        st.error(erro)
    for alerta in alertas:
        st.warning(alerta)
    for info in informativos:
        st.info(info)

    if erros or aporte_mensal is None:
        st.stop()

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

    # ====== KPIs ======
    anos_aporte = idade_aposentadoria - idade_atual
    percentual = aporte_mensal / renda_atual * 100
    patrimonio_final = patrimonio[(idade_aposentadoria - idade_atual) * 12]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("💰 Aporte mensal", f"R$ {aporte_mensal:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.metric("🏦 Poupança necessária", f"R$ {patrimonio_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    with col2:
        st.metric("📆 Anos de aportes", f"{anos_aporte} anos")
        st.metric("📊 % da renda atual", f"{percentual:.2f}%")

    # ====== Gráfico ======
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

    # ====== Exportar Excel ======
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
            worksheet.write("B6", aporte_mensal, money)
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
