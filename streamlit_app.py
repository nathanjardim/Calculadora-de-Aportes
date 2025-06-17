
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

import sys
import os
sys.path.append(os.path.dirname(__file__))

from core import calcular_aporte, simular_aposentadoria

import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
import requests

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

# (código segue igual até a função gerar_excel)

def gerar_excel():
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet("Simulação")
        writer.sheets["Simulação"] = worksheet

        bold = workbook.add_format({'bold': True})
        money = workbook.add_format({'num_format': 'R$ #,##0.00'})
        percent = workbook.add_format({'num_format': '0.00%'})
        header_format = workbook.add_format({'bold': True, 'bg_color': '#123934', 'font_color': 'white'})

        worksheet.write("A6", "💰 Aporte mensal", bold)
        worksheet.write("B6", aporte_mensal, money)
        worksheet.write("A7", "🏦 Poupança necessária", bold)
        worksheet.write("B7", patrimonio_final, money)
        worksheet.write("A8", "📆 Anos de aportes", bold)
        worksheet.write("B8", anos_aporte)
        worksheet.write("A9", "📊 % da renda atual", bold)
        worksheet.write("B9", percentual / 100, percent)

        df_export = df_chart[["Idade", "Montante"]]
        df_export.columns = ["Idade", "Patrimônio"]
        df_export.to_excel(writer, index=False, sheet_name="Simulação", startrow=11, header=False)

        for col_num, value in enumerate(df_export.columns.values):
            worksheet.write(10, col_num, value, header_format)

        worksheet.set_column("A:A", 10)
        worksheet.set_column("B:B", 20, money)

    output.seek(0)
    return output
