
st.set_page_config(page_title="Simulador Sow Capital", layout="wide")

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
      <img src="https://i.imgur.com/xqkwLt8.png" alt="Logo Sow Capital">
    </div>
""", unsafe_allow_html=True)



import streamlit as st
import pandas as pd
from core import simular_aposentadoria
def formatar_montante(valor):
    if valor >= 1_000_000:
        return f'R$ {valor / 1_000_000:.2f}M'
    elif valor >= 1_000:
        return f'R$ {valor / 1_000:.2f}K'
    else:
        return f'R$ {valor:.2f}'
from io import BytesIO
import altair as alt

st.set_page_config(page_title="Simulador de Aposentadoria", layout="centered")
st.title("💼 Simulador de Aposentadoria")

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

    with st.spinner("Calculando aporte ideal..."):
        aporte, patrimonio = simular_aposentadoria(dados)

    if isinstance(aporte, str):
        st.error(aporte)
    else:
        st.success(f"💰 Aporte mensal ideal: R$ {aporte:,.2f}")

        percentual_renda = aporte / renda_atual if renda_atual else 0
        poupanca_necessaria = patrimonio[len(patrimonio) if objetivo == "zerar" else len(range((idade_aposentadoria - idade_atual + 1) * 12))]

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
            y=alt.Y("Montante:Q", title="Montante (R$)", axis=alt.Axis(format=",.0f")),
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
