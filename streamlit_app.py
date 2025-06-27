import sys
import os
sys.path.append(os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from core import calcular_aporte, simular_aposentadoria, ir_progressivo, ir_regressivo
import altair as alt
from io import BytesIO
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="Wealth Planning", layout="wide")

# === ESTILOS ===
st.markdown("""
    <style>
    section.main > div {
        padding-left: 1.25rem !important;
        padding-right: 1.25rem !important;
    }
    .header {
        background-color: #123934;
        padding: 20px 10px;
        text-align: center;
    }
    .header img {
        max-width: 200px;
        height: auto;
    }
    .footer {
        background-color: #123934;
        padding: 10px 0;
        color: white;
        margin-top: 20px;
        font-size: 14.5px;
    }
    .footer-content {
        text-align: center;
        max-width: 1100px;
        margin: auto;
        line-height: 1.5;
    }
    .footer a {
        color: white;
        text-decoration: underline;
    }
    </style>
""", unsafe_allow_html=True)

# === UTILITÁRIOS ===
def formatar_moeda(valor, decimais=0):
    return f"R$ {valor:,.{decimais}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def texto_para_numero(texto):
    try:
        return float(texto.replace(".", "").replace(",", "."))
    except:
        return 0.0

def campo_monetario(label, valor_padrao):
    txt = st.text_input(label, value=valor_padrao, help=f"Insira o valor de {label.lower()}")
    val = texto_para_numero(txt)
    st.caption(f"➡️ Valor inserido: {formatar_moeda(val)}")
    return val

def buscar_serie_bcb(codigo, data_inicial, data_final):
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json&dataInicial={data_inicial}&dataFinal={data_final}"
    r = requests.get(url)
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    df["valor"] = df["valor"].str.replace(",", ".").astype(float)
    df["data"] = pd.to_datetime(df["data"], dayfirst=True)
    return df.set_index("data").sort_index()

def calcular_medias_historicas():
    fim = datetime.today().replace(day=1) - timedelta(days=1)
    inicio = fim.replace(day=1) - relativedelta(years=4)
    try:
        df_ipca = buscar_serie_bcb(433, inicio.strftime("%d/%m/%Y"), fim.strftime("%d/%m/%Y"))
        df_selic = buscar_serie_bcb(4390, inicio.strftime("%d/%m/%Y"), fim.strftime("%d/%m/%Y"))
        df = df_selic.join(df_ipca, lsuffix="_selic", rsuffix="_ipca").dropna()

        ipca_mensal = df["valor_ipca"] / 100
        selic_mensal = df["valor_selic"] / 100
        juros_real_mensal = (1 + selic_mensal) / (1 + ipca_mensal) - 1
        media_juros_real = (1 + juros_real_mensal.mean()) ** 12 - 1

        return round((1 + selic_mensal.mean()) ** 12 - 1 * 100, 2), round((1 + ipca_mensal.mean()) ** 12 - 1 * 100, 2), round(media_juros_real * 100, 2)
    except:
        return 9.5, 5.0, 4.5

def calcular_percentual_ir(total_ir, renda_liquida, expectativa_vida, idade_aposentadoria):
    meses_saque = (expectativa_vida - idade_aposentadoria) * 12
    total_sacado = renda_liquida * meses_saque
    return total_ir / total_sacado if total_sacado > 0 else 0

def gerar_excel(df_chart, aporte_int, patrimonio_final, anos_aporte, percentual, regime, percentual_ir_efetivo):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet("Simulação")
        writer.sheets["Simulação"] = worksheet

        money = workbook.add_format({'num_format': 'R$ #,##0'})
        percent_fmt = workbook.add_format({'num_format': '0%'})
        header_format = workbook.add_format({'bold': True, 'bg_color': '#123934', 'font_color': 'white'})

        worksheet.write("B2", "💰 Aporte mensal")
        worksheet.write("B3", aporte_int, money)
        worksheet.write("C2", "🏦 Poupança necessária")
        worksheet.write("C3", patrimonio_final, money)
        worksheet.write("D2", "📆 Anos de aportes")
        worksheet.write("D3", anos_aporte)
        worksheet.write("E2", "📊 % da renda atual")
        worksheet.write("E3", percentual / 100, percent_fmt)
        worksheet.write("F2", "🧾 Tributação")
        worksheet.write("F3", f"Tabela {regime.capitalize()}")
        worksheet.write("G2", "📉 Carga efetiva IR")
        worksheet.write("G3", percentual_ir_efetivo, percent_fmt)

        worksheet.write("A6", "Idade", header_format)
        worksheet.write("B6", "Patrimônio", header_format)

        for i, row in df_chart.iterrows():
            worksheet.write(i + 6, 0, int(row["Idade"]))
            worksheet.write(i + 6, 1, row["Montante"], money)

        worksheet.set_column("A:Z", 22)
    output.seek(0)
    return output

# === INTERFACE ===

def check_password():
    def password_entered():
        st.session_state["password_correct"] = st.session_state.get("password") == "sow123"
    if not st.session_state.get("password_correct", False):
        st.markdown("## 🔒 Área protegida")
        st.text_input("Digite a senha", type="password", on_change=password_entered, key="password")
        st.stop()

check_password()

st.markdown('<div class="header"><img src="https://i.imgur.com/iCRuacp.png" alt="Logo Sow Capital"></div>', unsafe_allow_html=True)
st.title("Wealth Planning")

selic_media, ipca_media, juros_real_medio = calcular_medias_historicas()

st.markdown("### 📋 Dados Iniciais")
renda_atual = campo_monetario("Renda atual (R$)", "10.000")
idade_atual = st.number_input("Idade atual", min_value=18.0, max_value=100.0, value=30.0, format="%.0f", help="Idade atual da pessoa que está simulando.")
poupanca = campo_monetario("Poupança atual (R$)", "50.000")

st.markdown("### 📊 Dados Econômicos")
st.markdown(f"🔎 Juros real médio histórico: **{juros_real_medio:.2f}% a.a.**")
taxa_juros = st.number_input("Rentabilidade real esperada (% a.a.)", min_value=0.0, max_value=100.0, value=juros_real_medio, format="%.2f", help="Rentabilidade anual real esperada após inflação.")

st.markdown("### 🧾 Renda desejada na aposentadoria")
renda_desejada = campo_monetario("Renda mensal desejada (R$)", "15.000")
plano_saude = campo_monetario("Plano de saúde (R$)", "0")
outras_despesas = campo_monetario("Outras despesas planejadas (R$)", "0")

st.markdown("### 💸 Renda passiva estimada")
previdencia = campo_monetario("Renda com previdência (R$)", "0")
aluguel_ou_outras = campo_monetario("Aluguel ou outras fontes de renda (R$)", "0")

st.markdown("### 🧓 Dados da aposentadoria")
idade_aposentadoria = st.number_input("Idade para aposentadoria", min_value=idade_atual + 1, max_value=100.0, value=65.0, format="%.0f", help="Idade planejada para se aposentar.")
expectativa_vida = st.number_input("Expectativa de vida", min_value=idade_aposentadoria + 1, max_value=120.0, value=90.0, format="%.0f", help="Expectativa de vida da pessoa.")

st.markdown("### 🎯 Objetivo Final")
modo = st.selectbox("Objetivo com o patrimônio", ["manter", "zerar", "atingir"])
outro_valor = campo_monetario("Valor alvo (R$)", "0") if modo == "atingir" else None

# botão de execução
if st.button("📈 Calcular"):
    renda_passiva_total = previdencia + aluguel_ou_outras
    despesas_adicionais = plano_saude + outras_despesas
    renda_liquida = max(renda_desejada + despesas_adicionais - renda_passiva_total, 0)

    resultado = calcular_aporte(
        int(idade_atual), int(idade_aposentadoria), int(expectativa_vida),
        poupanca, renda_liquida, taxa_juros / 100,
        imposto=None, modo=modo, valor_final_desejado=outro_valor
    )

    aporte = resultado.get("aporte_mensal")
    regime = resultado.get("regime")

    if aporte is None:
        st.warning("Com os parâmetros informados, não é possível atingir o objetivo de aposentadoria.")
        st.stop()
    if aporte == 0:
        st.success("🎉 Sua poupança atual já é suficiente. Nenhum aporte mensal é necessário.")
        st.stop()

    func_ir_final = (lambda v, m, a: ir_progressivo(v)) if regime == "progressivo" else ir_regressivo
    _, _, patrimonio, total_ir = simular_aposentadoria(
        int(idade_atual), int(idade_aposentadoria), int(expectativa_vida),
        poupanca, aporte, renda_liquida, taxa_juros / 100, func_ir_final
    )

    anos_aporte = int(idade_aposentadoria - idade_atual)
    percentual_ir_efetivo = calcular_percentual_ir(total_ir, renda_liquida, int(expectativa_vida), int(idade_aposentadoria))
    percentual = int(aporte / renda_atual * 100)
    patrimonio_final = int(patrimonio[anos_aporte * 12])
    aporte_int = int(aporte)

    st.info(f"🧾 Tributação otimizada: **Tabela {regime.capitalize()}** | 📉 Carga tributária média efetiva: **{percentual_ir_efetivo:.2%}**")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 💰 Aporte mensal")
        st.markdown(f"<h3 style='margin-top:0'>{formatar_moeda(aporte_int)}</h3>", unsafe_allow_html=True)
        st.markdown("#### 🏦 Poupança necessária")
        st.markdown(f"<h3 style='margin-top:0'>{formatar_moeda(patrimonio_final)}</h3>", unsafe_allow_html=True)
    with col2:
        st.markdown("#### 📆 Anos de aportes")
        st.markdown(f"<h3 style='margin-top:0'>{anos_aporte} anos</h3>", unsafe_allow_html=True)
        st.markdown("#### 📊 % da renda atual")
        st.markdown(f"<h3 style='margin-top:0'>{percentual}%</h3>", unsafe_allow_html=True)

    df_chart = pd.DataFrame({
        "Idade": [idade_atual + i / 12 for i in range(len(patrimonio))],
        "Montante": patrimonio
    })
    df_chart = df_chart[df_chart["Idade"] % 1 == 0].reset_index(drop=True)
    df_chart["Montante formatado"] = df_chart["Montante"].apply(lambda v: formatar_moeda(v, 0))

    chart = alt.Chart(df_chart).mark_line(interpolate="monotone").encode(
        x=alt.X("Idade", title="Idade", axis=alt.Axis(format=".0f")),
        y=alt.Y("Montante", title="Patrimônio acumulado", axis=alt.Axis(format=".2s")),
        tooltip=[
            alt.Tooltip("Idade", title="Idade", format=".0f"),
            alt.Tooltip("Montante formatado", title="Montante")
        ]
    ).properties(width=700, height=400)
    st.altair_chart(chart, use_container_width=True)

    st.download_button(
        label="📥 Baixar Excel",
        data=gerar_excel(df_chart, aporte_int, patrimonio_final, anos_aporte, percentual, regime, percentual_ir_efetivo),
        file_name="simulacao_aposentadoria.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.markdown("""
    <div class="footer">
        <div class="footer-content">
            <span>
                <strong>Rio de Janeiro</strong> – Av. Ataulfo de Paiva, 341, Sala 303 – Leblon, RJ – CEP: 22440-032
                &nbsp;&nbsp;<span style="color: white;">|</span>&nbsp;&nbsp;
                <strong>Email:</strong> ri@sow.capital
                &nbsp;&nbsp;<span style="color: white;">|</span>&nbsp;&nbsp;
                <strong>Site:</strong> <a href="https://sow.capital/" target="_blank">https://sow.capital/</a>
            </span>
        </div>
    </div>
""", unsafe_allow_html=True)
