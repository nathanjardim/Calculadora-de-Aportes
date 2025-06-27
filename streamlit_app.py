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

st.set_page_config(page_title="Wealth Planning", layout="wide")

st.markdown("""
    <style>
    @media (min-width: 768px) {
        section.main > div {
            padding-left: 1.25rem !important;
            padding-right: 1.25rem !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

def formatar_moeda(valor, decimais=0):
    return f"R$ {valor:,.{decimais}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def texto_para_numero(texto):
    try:
        return float(texto.replace(".", "").replace(",", "."))
    except:
        return 0.0

def buscar_serie_bcb(codigo, data_inicial, data_final):
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json&dataInicial={data_inicial}&dataFinal={data_final}"
    r = requests.get(url)
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    df["valor"] = df["valor"].str.replace(",", ".").astype(float)
    df["data"] = pd.to_datetime(df["data"], dayfirst=True)
    return df.set_index("data").sort_index()

def calcular_medias_historicas():
    from dateutil.relativedelta import relativedelta
    fim = datetime.today().replace(day=1) - timedelta(days=1)
    inicio = fim.replace(day=1) - relativedelta(years=4)
    inicio_str = inicio.strftime("%d/%m/%Y")
    fim_str = fim.strftime("%d/%m/%Y")

    try:
        df_ipca = buscar_serie_bcb(433, inicio_str, fim_str)
        df_selic = buscar_serie_bcb(4390, inicio_str, fim_str)
        df = df_selic.join(df_ipca, lsuffix="_selic", rsuffix="_ipca").dropna()

        ipca_mensal = df["valor_ipca"] / 100
        selic_mensal = df["valor_selic"] / 100
        juros_real_mensal = (1 + selic_mensal) / (1 + ipca_mensal) - 1
        df["juros_real_mensal"] = juros_real_mensal

        media_ipca = (1 + ipca_mensal.mean()) ** 12 - 1
        media_selic = (1 + selic_mensal.mean()) ** 12 - 1
        media_juros_real = (1 + df["juros_real_mensal"].mean()) ** 12 - 1

        return round(media_selic * 100, 2), round(media_ipca * 100, 2), round(media_juros_real * 100, 2)
    except:
        return 9.5, 5.0, 4.5

def calcular_juros_real_atual(ipca_pct, selic_pct):
    return round(((1 + selic_pct / 100) / (1 + ipca_pct / 100) - 1) * 100, 2)

def check_password():
    def password_entered():
        if st.session_state["password"] == "sow123":
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.markdown("## 🔒 Área protegida")
        st.text_input("Digite a senha", type="password", on_change=password_entered, key="password")
        st.stop()

check_password()

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

selic_media, ipca_media, juros_real_medio = calcular_medias_historicas()

st.markdown("### 📋 Dados Iniciais")
renda_atual_txt = st.text_input("Renda atual (R$)", value="10.000")
renda_atual = texto_para_numero(renda_atual_txt)
st.caption(f"➡️ Valor inserido: {formatar_moeda(renda_atual)}")

idade_atual = st.number_input("Idade atual", min_value=18.0, max_value=100.0, value=30.0, format="%.0f")

poupanca_txt = st.text_input("Poupança atual (R$)", value="50.000")
poupanca = texto_para_numero(poupanca_txt)
st.caption(f"➡️ Valor inserido: {formatar_moeda(poupanca)}")

st.markdown("### 📊 Dados Econômicos")
st.markdown(f"🔎 Juros real médio histórico: **{juros_real_medio:.2f}% a.a.**")
taxa_juros = st.number_input("Rentabilidade real esperada (% a.a.)", min_value=0.0, max_value=100.0, value=juros_real_medio, format="%.2f")

st.markdown("### 🧾 Renda desejada na aposentadoria")
renda_desejada_txt = st.text_input("Renda mensal desejada (R$)", value="15.000")
renda_desejada = texto_para_numero(renda_desejada_txt)
st.caption(f"➡️ Valor inserido: {formatar_moeda(renda_desejada)}")

plano_saude_txt = st.text_input("Plano de saúde (R$)", value="0")
plano_saude = texto_para_numero(plano_saude_txt)
st.caption(f"➡️ Valor inserido: {formatar_moeda(plano_saude)}")

outras_despesas_txt = st.text_input("Outras despesas planejadas (R$)", value="0")
outras_despesas = texto_para_numero(outras_despesas_txt)
st.caption(f"➡️ Valor inserido: {formatar_moeda(outras_despesas)}")

st.markdown("### 💸 Renda passiva estimada")
previdencia_txt = st.text_input("Renda com previdência (R$)", value="0")
previdencia = texto_para_numero(previdencia_txt)
st.caption(f"➡️ Valor inserido: {formatar_moeda(previdencia)}")

aluguel_txt = st.text_input("Aluguel ou outras fontes de renda (R$)", value="0")
aluguel_ou_outras = texto_para_numero(aluguel_txt)
st.caption(f"➡️ Valor inserido: {formatar_moeda(aluguel_ou_outras)}")

st.markdown("### 🧓 Dados da aposentadoria")
idade_aposentadoria = st.number_input("Idade para aposentadoria", min_value=0.0, max_value=100.0, value=65.0, format="%.0f")
expectativa_vida = st.number_input("Expectativa de vida", min_value=idade_aposentadoria + 1, max_value=120.0, value=90.0, format="%.0f")

st.markdown("### 🎯 Objetivo Final")
modo = st.selectbox("Objetivo com o patrimônio", ["manter", "zerar", "atingir"])
outro_valor = None
if modo == "atingir":
    outro_valor_txt = st.text_input("Valor alvo (R$)", value="0")
    outro_valor = texto_para_numero(outro_valor_txt)
    st.caption(f"➡️ Valor inserido: {formatar_moeda(outro_valor)}")

# botão de execução
submitted = st.button("📈 Calcular")

if submitted:
    if idade_aposentadoria <= idade_atual:
        st.error("⚠️ A idade para aposentadoria deve ser maior do que a idade atual informada.")
        st.stop()

    if expectativa_vida <= idade_aposentadoria:
        st.error("⚠️ A expectativa de vida deve ser maior do que a idade de aposentadoria.")
        st.stop()

    renda_passiva_total = previdencia + aluguel_ou_outras
    despesas_adicionais = plano_saude + outras_despesas
    renda_total_desejada = renda_desejada + despesas_adicionais
    renda_liquida = max(renda_total_desejada - renda_passiva_total, 0)

    dados = {
        "idade_atual": int(idade_atual),
        "idade_aposentadoria": int(idade_aposentadoria),
        "expectativa_vida": int(expectativa_vida),
        "renda_atual": int(renda_atual),
        "renda_desejada": int(renda_desejada),
        "poupanca": int(poupanca),
        "taxa_juros_anual": taxa_juros / 100,
    }

    resultado = calcular_aporte(
        dados["idade_atual"], dados["idade_aposentadoria"], dados["expectativa_vida"],
        dados["poupanca"], renda_liquida, dados["taxa_juros_anual"],
        imposto=None, modo=modo, valor_final_desejado=outro_valor
    )

    aporte = resultado.get("aporte_mensal")
    regime = resultado.get("regime")

    if aporte is None:
        st.warning("Com os parâmetros informados, não é possível atingir o objetivo de aposentadoria.")
        st.stop()

    if aporte == 0:
        st.success("🎉 Sua poupança atual já é suficiente para atingir o objetivo de aposentadoria. Nenhum aporte mensal é necessário.")
        st.stop()

    func_ir_final = (lambda v, m, a: ir_progressivo(v)) if regime == "progressivo" else ir_regressivo

    _, _, patrimonio, total_ir = simular_aposentadoria(
        dados["idade_atual"], dados["idade_aposentadoria"], dados["expectativa_vida"],
        dados["poupanca"], aporte, renda_liquida,
        dados["taxa_juros_anual"], func_ir_final
    )

    anos_aporte = dados["idade_aposentadoria"] - dados["idade_atual"]
    meses_saque = (dados["expectativa_vida"] - dados["idade_aposentadoria"]) * 12
    total_sacado = renda_liquida * meses_saque
    percentual_ir_efetivo = total_ir / total_sacado

    st.info(f"🧾 Tributação otimizada: **Tabela {'Regressiva' if regime == 'regressivo' else 'Progressiva'}** | 📉 Carga tributária média efetiva: **{percentual_ir_efetivo:.2%}**")

    percentual = int(aporte / dados["renda_atual"] * 100)
    patrimonio_final = int(patrimonio[(anos_aporte) * 12])
    aporte_int = int(aporte)

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
        "Idade": [dados["idade_atual"] + i / 12 for i in range(len(patrimonio))],
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

    def gerar_excel():
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet("Simulação")
            writer.sheets["Simulação"] = worksheet

            bold = workbook.add_format({'bold': True})
            money = workbook.add_format({'num_format': 'R$ #,##0'})
            percent_fmt = workbook.add_format({'num_format': '0%'})
            header_format = workbook.add_format({'bold': True, 'bg_color': '#123934', 'font_color': 'white'})

            worksheet.write("B2", "💰 Aporte mensal", bold)
            worksheet.write("B3", aporte_int, money)
            worksheet.write("C2", "🏦 Poupança necessária", bold)
            worksheet.write("C3", patrimonio_final, money)
            worksheet.write("D2", "📆 Anos de aportes", bold)
            worksheet.write("D3", anos_aporte)
            worksheet.write("E2", "📊 % da renda atual", bold)
            worksheet.write("E3", percentual / 100, percent_fmt)
            worksheet.write("F2", "🧾 Tributação", bold)
            worksheet.write("F3", f"Tabela {regime.capitalize()}")
            worksheet.write("G2", "📉 Carga efetiva IR", bold)
            worksheet.write("G3", percentual_ir_efetivo, percent_fmt)

            worksheet.write("A6", "Idade", header_format)
            worksheet.write("B6", "Patrimônio", header_format)

            for i, row in df_chart.iterrows():
                worksheet.write(i + 6, 0, int(row["Idade"]))
                worksheet.write(i + 6, 1, row["Montante"], money)

            worksheet.set_column("A:Z", 22)

        output.seek(0)
        return output

    st.download_button(
        label="📥 Baixar Excel",
        data=gerar_excel(),
        file_name="simulacao_aposentadoria.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.markdown("""
    <style>
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

