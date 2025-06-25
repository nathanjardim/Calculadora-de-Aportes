import sys
import os
sys.path.append(os.path.dirname(__file__))

import streamlit as st
st.set_page_config(page_title="Wealth Planning", layout="wide")

from core import calcular_aporte, simular_aposentadoria, ir_progressivo, ir_regressivo
import pandas as pd
import altair as alt
from io import BytesIO

def formatar_moeda(valor, decimais=0):
    return f"R$ {valor:,.{decimais}f}".replace(",", "X").replace(".", ",").replace("X", ".")

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

st.title("Wealth Planning")

with st.form("formulario"):
    st.markdown("### 📋 Dados Iniciais")
    renda_atual = st.number_input("Renda atual (R$)", min_value=0.0, step=100.0, value=10000.0, format="%.0f", help="Informe sua renda líquida mensal atual.")
    idade_atual = st.number_input("Idade atual", min_value=18.0, max_value=100.0, value=30.0, format="%.0f", help="Sua idade atual em anos completos.")
    poupanca = st.number_input("Poupança atual (R$)", min_value=0.0, step=1000.0, value=50000.0, format="%.0f", help="Valor disponível atualmente para aposentadoria.")

    st.markdown("### 📊 Dados Econômicos")
    taxa_juros = st.number_input("Taxa de juros real anual (%)", min_value=0.0, max_value=100.0, value=5.0, format="%.0f", help="Rentabilidade real esperada ao ano, já descontada a inflação.")

    st.markdown("### 🧾 Renda desejada na aposentadoria")
    renda_desejada = st.number_input("Renda mensal desejada (R$)", min_value=0.0, step=500.0, value=15000.0, format="%.0f", help="Quanto você gostaria de receber por mês durante a aposentadoria.")
    plano_saude = st.number_input("Plano de saúde (R$)", min_value=0.0, step=100.0, value=0.0, format="%.0f", help="Valor mensal estimado do plano de saúde durante a aposentadoria.")
    outras_despesas = st.number_input("Outras despesas planejadas (R$)", min_value=0.0, step=100.0, value=0.0, format="%.0f", help="Outras despesas fixas mensais que você espera ter na aposentadoria.")

    st.markdown("### 💸 Renda passiva estimada")
    previdencia = st.number_input("Renda com previdência (R$)", min_value=0.0, step=100.0, value=0.0, format="%.0f", help="Valor mensal que você espera receber de previdência privada após a aposentadoria.")
    aluguel_ou_outras = st.number_input("Aluguel ou outras fontes de renda (R$)", min_value=0.0, step=100.0, value=0.0, format="%.0f", help="Renda mensal estimada com aluguel ou outras fontes após a aposentadoria.")

    st.markdown("### 🧓 Dados da aposentadoria")
    idade_aposentadoria = st.number_input("Idade para aposentadoria", min_value=idade_atual + 1, max_value=100.0, value=65.0, format="%.0f", help="Idade em que você pretende parar de trabalhar.")
    expectativa_vida = st.number_input("Expectativa de vida", min_value=idade_aposentadoria + 1, max_value=120.0, value=90.0, format="%.0f", help="Expectativa de vida total, em anos.")

    st.markdown("### 🎯 Objetivo Final")
    modo = st.selectbox("Objetivo com o patrimônio", ["manter", "zerar", "atingir"], help="Escolha o que deseja fazer com seu patrimônio ao final da aposentadoria.")
    outro_valor = None
    if modo == "atingir":
        outro_valor = st.number_input("Valor alvo (R$)", min_value=0.0, step=10000.0, format="%.0f", help="Valor total que você deseja atingir ao final da vida.")

    submitted = st.form_submit_button("📈 Calcular")

if submitted:
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
        st.warning("Com os parâmetros informados, não é possível atingir o objetivo de aposentadoria. Tente ajustar a renda desejada, idade ou outros valores.")
    else:
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

        st.info(f"🧾 Tributação otimizada: **Tabela {regime.capitalize()}**")
        st.info(f"📉 Carga tributária média efetiva: **{percentual_ir_efetivo:.2%}**")

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
