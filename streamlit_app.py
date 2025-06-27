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

def gerar_excel(df_chart, aporte_int, patrimonio_final, anos_aporte, percentual, regime, percentual_ir_efetivo, parametros):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book

        ws1 = workbook.add_worksheet("Simulação")
        writer.sheets["Simulação"] = ws1
        money = workbook.add_format({'num_format': 'R$ #,##0'})
        percent_fmt = workbook.add_format({'num_format': '0%'})
        header_format = workbook.add_format({'bold': True, 'bg_color': '#123934', 'font_color': 'white'})

        ws1.write("B2", "💰 Aporte mensal")
        ws1.write("B3", aporte_int, money)
        ws1.write("C2", "🏦 Poupança necessária")
        ws1.write("C3", patrimonio_final, money)
        ws1.write("D2", "📆 Anos de aportes")
        ws1.write("D3", anos_aporte)
        ws1.write("E2", "📊 % da renda atual")
        ws1.write("E3", percentual / 100, percent_fmt)
        ws1.write("F2", "🧾 Tributação")
        ws1.write("F3", f"Tabela {regime.capitalize()}")
        ws1.write("G2", "📉 Carga efetiva IR")
        ws1.write("G3", percentual_ir_efetivo, percent_fmt)

        ws1.write("A6", "Idade", header_format)
        ws1.write("B6", "Patrimônio", header_format)

        for i, row in df_chart.iterrows():
            ws1.write(i + 6, 0, int(row["Idade"]))
            ws1.write(i + 6, 1, row["Montante"], money)
        ws1.set_column("A:Z", 22)

        ws2 = workbook.add_worksheet("Parametros")
        writer.sheets["Parametros"] = ws2
        for i, (chave, valor) in enumerate(parametros.items()):
            ws2.write(i, 0, chave)
            ws2.write(i, 1, valor)
        ws2.set_column("A:B", 30)

    output.seek(0)
    return output

def verificar_mensagens(idade_atual, idade_aposentadoria, expectativa_vida, renda_atual, taxa_juros, renda_desejada, aporte):
    erros, alertas, informativos = [], [], []
    tempo_aporte = idade_aposentadoria - idade_atual

    if idade_atual >= idade_aposentadoria:
        erros.append("A idade atual deve ser menor que a idade de aposentadoria.")
    if expectativa_vida <= idade_aposentadoria:
        erros.append("A expectativa de vida deve ser maior que a idade de aposentadoria.")
    if renda_atual <= 0:
        erros.append("Renda atual inválida. Verifique o campo preenchido.")
    if taxa_juros < 0 or taxa_juros > 1:
        erros.append("Taxa de juros fora do intervalo permitido. Verifique os parâmetros.")
    if aporte is not None and aporte > renda_atual:
        erros.append("Aporte calculado maior que a renda atual. Verifique os parâmetros.")

    if taxa_juros > 0.10:
        alertas.append("Taxa de juros real elevada. Verifique os parâmetros.")
    if tempo_aporte < 5:
        alertas.append("Prazo muito curto até a aposentadoria. Verifique os parâmetros.")
    if tempo_aporte > 50:
        alertas.append("Prazo muito longo até a aposentadoria. Verifique os parâmetros.")
    if renda_desejada > 10 * renda_atual:
        alertas.append("Renda desejada superior à renda atual. Verifique os parâmetros.")
    if aporte is not None and aporte > 0.5 * renda_atual:
        alertas.append("Aporte elevado em relação à renda. Verifique os parâmetros.")
    if renda_desejada == 0:
        informativos.append("Renda desejada igual a zero. Verifique os parâmetros.")
    if aporte is not None and aporte < 10:
        informativos.append("Aporte muito baixo detectado. Confirme os parâmetros utilizados.")

    return erros, alertas, informativos

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
idade_atual = st.number_input("Idade atual", min_value=18.0, max_value=100.0, value=30.0, format="%.0f")
poupanca = campo_monetario("Poupança atual (R$)", "50.000")

st.divider()

st.markdown("### 📊 Dados Econômicos")
st.markdown(f"🔎 Juros real médio histórico: **{juros_real_medio:.2f}% a.a.**")
taxa_juros = st.number_input("Rentabilidade real esperada (% a.a.)", min_value=0.0, max_value=100.0, value=juros_real_medio, format="%.2f")

st.divider()

st.markdown("### 🧾 Renda desejada na aposentadoria")
renda_desejada = campo_monetario("Renda mensal desejada (R$)", "15.000")
plano_saude = campo_monetario("Plano de saúde (R$)", "0")
outras_despesas = campo_monetario("Outras despesas planejadas (R$)", "0")

st.divider()

st.markdown("### 💸 Renda passiva estimada")
previdencia = campo_monetario("Renda com previdência (R$)", "0")
aluguel_ou_outras = campo_monetario("Aluguel ou outras fontes de renda (R$)", "0")

st.divider()

st.markdown("### 🧓 Dados da aposentadoria")
idade_aposentadoria = st.number_input("Idade para aposentadoria", min_value=idade_atual + 1, max_value=100.0, value=65.0, format="%.0f")
expectativa_vida = st.number_input("Expectativa de vida", min_value=idade_aposentadoria + 1, max_value=120.0, value=90.0, format="%.0f")

st.divider()

st.markdown("### 🎯 Objetivo Final")
modo = st.selectbox("Objetivo com o patrimônio", ["manter", "zerar", "atingir"])
outro_valor = campo_monetario("Valor alvo (R$)", "0") if modo == "atingir" else None

if st.button("📈 Calcular"):
    renda_passiva_total = previdencia + aluguel_ou_outras
    despesas_adicionais = plano_saude + outras_despesas
    renda_liquida = max(renda_desejada + despesas_adicionais - renda_passiva_total, 0)

    erros, alertas, informativos = verificar_mensagens(
        idade_atual=int(idade_atual),
        idade_aposentadoria=int(idade_aposentadoria),
        expectativa_vida=int(expectativa_vida),
        renda_atual=renda_atual,
        taxa_juros=taxa_juros / 100,
        renda_desejada=renda_desejada,
        aporte=None
    )

    for msg in erros:
        st.error(msg)
    for msg in alertas:
        st.warning(msg)
    for msg in informativos:
        st.info(msg)

    if erros:
        st.stop()

    resultado = calcular_aporte(
        int(idade_atual), int(idade_aposentadoria), int(expectativa_vida),
        poupanca, renda_liquida, taxa_juros / 100,
        imposto=None, modo=modo, valor_final_desejado=outro_valor
    )

    aporte = resultado.get("aporte_mensal")
    regime = resultado.get("regime")

    erros, alertas, informativos = verificar_mensagens(
        idade_atual=int(idade_atual),
        idade_aposentadoria=int(idade_aposentadoria),
        expectativa_vida=int(expectativa_vida),
        renda_atual=renda_atual,
        taxa_juros=taxa_juros / 100,
        renda_desejada=renda_desejada,
        aporte=aporte
    )

    for msg in erros:
        st.error(msg)
    for msg in alertas:
        st.warning(msg)
    for msg in informativos:
        st.info(msg)

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

    parametros = {
        "Idade atual": idade_atual,
        "Idade aposentadoria": idade_aposentadoria,
        "Expectativa de vida": expectativa_vida,
        "Renda atual": renda_atual,
        "Renda desejada": renda_desejada,
        "Plano de saúde": plano_saude,
        "Outras despesas": outras_despesas,
        "Renda passiva previdência": previdencia,
        "Renda passiva aluguel": aluguel_ou_outras,
        "Poupança atual": poupanca,
        "Taxa real esperada": taxa_juros,
        "Objetivo": modo,
        "Valor alvo (atingir)": outro_valor or 0,
    }

    st.download_button(
        label="📥 Baixar Excel",
        data=gerar_excel(df_chart, aporte_int, patrimonio_final, anos_aporte, percentual, regime, percentual_ir_efetivo, parametros),
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
