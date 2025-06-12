import streamlit as st
import plotly.graph_objects as go
from core import simular

st.set_page_config(page_title="Wealth Planning", layout="centered")
st.title("📊 Wealth Planning")

with st.form("formulario"):
    st.header("🔹 Dados Iniciais")
    col1, col2, col3 = st.columns(3)
    with col1:
        renda_atual = st.number_input("Renda atual (R$)", min_value=0.0, value=70000.0)
    with col2:
        idade_atual = st.number_input("Idade atual", min_value=0, max_value=120, value=42)
    with col3:
        poupanca_atual = st.number_input("Poupança atual (R$)", min_value=0.0, value=1000000.0)

    st.header("🔹 Dados Econômicos")
    col4, col5 = st.columns(2)
    with col4:
        taxa_anual = st.number_input("Taxa de juros real (aa)", min_value=0.0, max_value=1.0, value=0.05)
    with col5:
        imposto = st.number_input("IR sobre lucro", min_value=0.0, max_value=1.0, value=0.15)

    st.header("🔹 Aposentadoria")
    col6, col7, col8 = st.columns(3)
    with col6:
        renda_desejada = st.number_input("Renda mensal desejada (R$)", min_value=0.0, value=40000.0)
    with col7:
        idade_aposentadoria = st.number_input("Idade aposentadoria", min_value=idade_atual+1, max_value=120, value=65)
    with col8:
        idade_morte = st.number_input("Idade fim (vida)", min_value=idade_aposentadoria+1, max_value=130, value=95)

    st.header("🔹 Renda")
    col9, col10 = st.columns(2)
    with col9:
        previdencia = st.number_input("Previdência esperada (R$)", min_value=0.0, value=0.0)
    with col10:
        outras_rendas = st.number_input("Outras fontes (aluguel etc) (R$)", min_value=0.0, value=0.0)

    st.header("🔹 Fim do Patrimônio")
    col11, col12 = st.columns([2, 1])
    with col11:
        tipo_objetivo = st.selectbox("Objetivo ao fim do período", ["Manter", "Zerar", "Outro valor"])
    with col12:
        outro_valor = None
        if tipo_objetivo.lower() == "outro valor":
            outro_valor = st.number_input("Valor desejado (R$)", min_value=0.0, value=0.0)

    submit = st.form_submit_button("📤 Definir Aportes")

if submit:
    try:
        dados = {
            "idade_atual": int(idade_atual),
            "idade_aposentadoria": int(idade_aposentadoria),
            "idade_morte": int(idade_morte),
            "renda_desejada": float(renda_desejada),
            "previdencia": float(previdencia),
            "outras_rendas": float(outras_rendas),
            "poupanca_atual": float(poupanca_atual),
            "taxa_anual": float(taxa_anual),  # <- corrigido aqui
            "imposto": float(imposto),
            "tipo_objetivo": tipo_objetivo.lower(),
            "outro_valor": float(outro_valor) if outro_valor is not None else 0.0
        }

        aporte_ideal, patrimonio = simular(dados)

        st.success(f"Aporte mensal ideal: R$ {aporte_ideal:,.2f}")

        total_poupanca = aporte_ideal * ((dados['idade_aposentadoria'] - dados['idade_atual'] + 1) * 12)
        percentual_renda = (aporte_ideal / renda_atual) * 100

        st.subheader("📘 Resumo do planejamento")
        colr1, colr2, colr3 = st.columns(3)
        colr1.metric("Aportes mensais", f"R$ {aporte_ideal:,.2f}")
        colr2.metric("Poupança necessária", f"R$ {total_poupanca:,.2f}")
        colr3.metric("Percentual da renda atual", f"{percentual_renda:.2f}%")

        st.subheader("📈 Evolução do patrimônio no tempo")
        idades_mensais = [dados['idade_atual'] + i / 12 for i in range(len(patrimonio))]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=idades_mensais,
            y=patrimonio,
            mode="lines",
            name="Evolução do patrimônio",
            line=dict(width=3, color="royalblue"),
            hovertemplate="Idade: %{x:.1f} anos<br>Patrimônio: R$ %{y:,.2f}<extra></extra>"
        ))

        fig.update_layout(
            xaxis_title="Idade (anos)",
            yaxis_title="Patrimônio (R$)",
            hovermode="x unified",
            template="plotly_white",
            margin=dict(l=40, r=40, t=30, b=40)
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Erro: {str(e)}")
