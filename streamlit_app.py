import streamlit as st
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

import pandas as pd
from core import simular_aposentadoria
from io import BytesIO
import altair as alt


def formatar_montante(valor):
    if valor >= 1_000_000:
        return f'R$ {valor / 1_000_000:.2f}M'
    elif valor >= 1_000:
        return f'R$ {valor / 1_000:.2f}K'
    else:
        return f'R$ {valor:.2f}'


def validar_inputs(dados, renda_atual):
    erros = []

    # Idades
    if dados['idade_aposentadoria'] <= dados['idade_atual']:
        erros.append("Idade para aposentadoria deve ser maior que idade atual.")
    if dados['idade_morte'] <= dados['idade_aposentadoria']:
        erros.append("Idade fim deve ser maior que idade para aposentadoria.")
    if dados['idade_atual'] < 18 or dados['idade_atual'] > 100:
        erros.append("Idade atual fora do intervalo permitido (18 a 100 anos).")
    if dados['idade_aposentadoria'] > 100:
        erros.append("Idade para aposentadoria deve ser até 100 anos.")
    if dados['idade_morte'] > 120:
        erros.append("Idade fim deve ser até 120 anos.")

    # Taxas
    if dados['taxa_juros_anual'] <= 0:
        erros.append("Taxa de juros real anual deve ser maior que zero.")
    if dados['taxa_juros_anual'] > 0.5:
        erros.append("Taxa de juros real anual muito alta (máximo 50%).")
    if dados['imposto_renda'] < 0 or dados['imposto_renda'] > 1:
        erros.append("Imposto de renda deve estar entre 0% e 100%.")

    # Valores financeiros
    if dados['valor_inicial'] < 0:
        erros.append("Poupança atual não pode ser negativa.")
    if dados['renda_desejada'] <= dados['outras_rendas'] + dados['previdencia']:
        erros.append("Renda desejada deve ser maior que soma de outras rendas e previdência.")

    # Objetivo
    if dados['tipo_objetivo'] not in ['manter', 'zerar', 'outro valor']:
        erros.append("Objetivo inválido.")

    # Checagem básica aporte vs renda atual
    if renda_atual > 0:
        aporte_max = renda_atual * 10
        # Podemos aqui sugerir ou validar aporte máximo aceitável se quiser
    else:
        erros.append("Renda atual deve ser maior que zero para validação de aporte.")

    return erros


with st.form("form_inputs"):
    st.markdown("### 📋 Dados Iniciais")
    renda_atual = st.number_input("Renda atual (R$)", min_value=0, value=70000, step=1000)
    idade_atual = st.number_input("Idade atual", min_value=18, max_value=100, value=42, step=1)
    poupanca_atual = st.number_input("Poupança atual (R$)", min_value=0, value=1_000_000, step=1000)

    st.markdown("### 📊 Dados Econômicos")
    taxa_juros_percentual = st.number_input("Taxa de juros real anual (%)", min_value=0, max_value=100, value=5, step=1)
    imposto_renda_percentual = st.number_input("IR (%)", min_value=0, max_value=100, value=15, step=1)
    taxa_juros_anual = taxa_juros_percentual / 100
    imposto_renda = imposto_renda_percentual / 100

    st.markdown("### 🏁 Aposentadoria")
    renda_desejada = st.number_input("Renda mensal desejada (R$)", min_value=0, value=40000, step=1000)
    idade_aposentadoria = st.number_input("Idade para aposentadoria", min_value=idade_atual+1, max_value=100, value=65, step=1)
    idade_morte = st.number_input("Idade fim", min_value=idade_aposentadoria+1, max_value=120, value=95, step=1)

    st.markdown("### 💵 Renda")
    previdencia = st.number_input("Previdência (R$)", min_value=0, value=0, step=100)
    outras_rendas = st.number_input("Aluguel ou outras fontes (R$)", min_value=0, value=0, step=100)

    st.markdown("### 🎯 Fim do Patrimônio")
    objetivo = st.selectbox("Objetivo", options=["manter", "zerar", "outro valor"])
    outro_valor = 0
    if objetivo == "outro valor":
        outro_valor = st.number_input("Se outro valor, qual? (R$)", min_value=0, value=5000000, step=10000)

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

    erros = validar_inputs(dados, renda_atual)

    if erros:
        for e in erros:
            st.error(e)
    else:
        try:
            aporte, patrimonio, meses_acumulacao = simular_aposentadoria(dados)
        except Exception as ex:
            st.error(f"Erro na simulação: {ex}")
        else:
            percentual_renda = aporte / renda_atual if renda_atual else 0
            poupanca_necessaria = patrimonio[meses_acumulacao + 1]

            st.success(f"💰 Aporte mensal ideal: R$ {aporte:,.2f}")

            st.markdown("### 📊 Resultado Resumido")
            st.metric("Aportes mensais", f"R$ {aporte:,.2f}")
            st.metric("Poupança necessária", f"R$ {poupanca_necessaria:,.2f}")
            st.metric("Percentual da renda atual", f"{percentual_renda * 100:.2f}%")

            st.markdown("### 📈 Evolução do Patrimônio")

            df_chart = pd.DataFrame({
                "Anos de vida": [idade_atual + i / 12 for i in range(len(patrimonio))],
                "Montante": patrimonio
            })
            df_chart["Montante formatado"] = df_chart["Montante"].apply(formatar_montante)

            chart = alt.Chart(df_chart).mark_line(interpolate="monotone").encode(
                x=alt.X("Anos de vida:Q", title="Idade", axis=alt.Axis(format=".0f")),
                y=alt.Y("Montante:Q", title=None, axis=alt.Axis(format=".2s")),
                tooltip=[
                    alt.Tooltip("Anos de vida", title="Idade", format=".0f"),
                    alt.Tooltip("Montante formatado", title="Montante")
                ]
            ).properties(width=700, height=400)

            st.altair_chart(chart, use_container_width=True)

            st.markdown("### 📤 Exportar dados")
            df_export = pd.DataFrame({
                "Ano": df_chart["Anos de vida"],
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
