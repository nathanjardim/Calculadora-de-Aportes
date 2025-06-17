import streamlit as st
import pandas as pd
from core import calcular_aporte
from io import BytesIO
import altair as alt

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

def verificar_alertas(inputs, aporte_calculado=None):
    erros, alertas, informativos = [], [], []

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

def formatar_montante(valor):
    if valor >= 1_000_000:
        return f'R$ {valor / 1_000_000:.2f}M'
    elif valor >= 1_000:
        return f'R$ {valor / 1_000:.2f}K'
    else:
        return f'R$ {valor:.2f}'

st.title("🧮 Simulador de Aposentadoria")

with st.form("formulario"):
    col1, col2, col3 = st.columns(3)
    with col1:
        idade_atual = st.number_input("Idade Atual", value=30, min_value=0)
        expectativa_vida = st.number_input("Expectativa de Vida", value=85, min_value=1)
        poupanca = st.number_input("Poupança Atual (R$)", value=0.0, min_value=0.0)
    with col2:
        idade_aposentadoria = st.number_input("Idade para Aposentadoria", value=60, min_value=1)
        renda_desejada = st.number_input("Renda Desejada na Aposentadoria (R$)", value=3000.0, min_value=0.0)
        taxa_juros_anual = st.number_input("Taxa de Juros Anual (ex: 0.05 para 5%)", value=0.05, min_value=0.0)
    with col3:
        renda_atual = st.number_input("Renda Mensal Atual (R$)", value=5000.0, min_value=0.0)
        imposto = st.number_input("Alíquota de Imposto sobre Resgates (0 a 1)", value=0.15, min_value=0.0, max_value=1.0)

    submit = st.form_submit_button("Calcular Aporte")

if submit:
    dados = {
        "idade_atual": idade_atual,
        "idade_aposentadoria": idade_aposentadoria,
        "expectativa_vida": expectativa_vida,
        "renda_atual": renda_atual,
        "renda_desejada": renda_desejada,
        "poupanca": poupanca,
        "taxa_juros_anual": taxa_juros_anual,
        "imposto": imposto
    }

    aporte_mensal, patrimonio_final, percentual = calcular_aporte(dados)

    # Exibir alertas
    erros, alertas, informativos = verificar_alertas(dados, aporte_mensal)
    for msg in erros:
        st.error(f"❌ {msg}")
    for msg in alertas:
        st.warning(f"⚠️ {msg}")
    for msg in informativos:
        st.info(f"ℹ️ {msg}")

    # Resultados principais
    st.markdown("## 🧾 Resultados")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Aporte Mensal Necessário", formatar_montante(aporte_mensal))
    col2.metric("Poupança Necessária ao Aposentar", formatar_montante(patrimonio_final))
    col3.metric("Poupança Final Total", formatar_montante(patrimonio_final))
    col4.metric("Renda Cobrida por Juros (%)", f"{percentual:.1f}%")

    # Detalhamento do gráfico
    st.markdown("### 📊 Evolução Patrimonial")
    df_resultado = pd.read_csv("output.csv")
    df_resultado = df_resultado[df_resultado["Ano"].apply(lambda x: x % 1 == 0)]

    chart = alt.Chart(df_resultado).mark_line(point=True).encode(
        x=alt.X("Ano:O", axis=alt.Axis(title="Ano")),
        y=alt.Y("Patrimônio (R$)", axis=alt.Axis(title="Patrimônio")),
        tooltip=["Ano", "Patrimônio (R$)"]
    ).properties(width=800, height=400)

    st.altair_chart(chart, use_container_width=True)

    # Exportar resultado
    st.download_button(
        label="📥 Exportar CSV",
        data=df_resultado.to_csv(index=False).encode("utf-8"),
        file_name="simulacao_aposentadoria.csv",
        mime="text/csv"
    )
