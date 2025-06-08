import streamlit as st
import matplotlib.pyplot as plt
from core import (
    taxa_mensal, calcular_meses_acc, calcular_meses_cons,
    gerar_cotas, bissecao, calcular_aporte
)

st.set_page_config(page_title="Wealth Planning", layout="wide")

st.title("💼 Wealth Planning – Simulador de Aposentadoria")
st.markdown("Preencha seus dados para descobrir o aporte mensal ideal para atingir seus objetivos.")

# Bloco 1: Dados Iniciais
with st.expander("📌 Dados Iniciais"):
    col1, col2, col3 = st.columns(3)
    idade_atual = col1.number_input("Idade atual", min_value=0, max_value=100, value=30)
    idade_aposentadoria = col2.number_input("Idade para aposentadoria", min_value=0, max_value=100, value=65)
    idade_morte = col3.number_input("Idade esperada ao falecer", min_value=0, max_value=120, value=85)

# Bloco 2: Dados Econômicos
with st.expander("📈 Parâmetros Econômicos"):
    col1, col2 = st.columns(2)
    valor_inicial = col1.number_input("Valor já investido (R$)", min_value=0.0, value=10000.0)
    taxa_juros_anual = col2.number_input("Taxa de juros anual (%)", min_value=0.0, max_value=100.0, value=8.0) / 100
    imposto_renda = col1.number_input("Imposto sobre ganhos (%)", min_value=0.0, max_value=100.0, value=15.0) / 100

# Bloco 3: Objetivo de Aposentadoria
with st.expander("🎯 Objetivo de Aposentadoria"):
    col1, col2, col3 = st.columns(3)
    renda_desejada = col1.number_input("Renda mensal desejada (R$)", min_value=0.0, value=5000.0)
    previdencia = col2.number_input("Previdência esperada (R$)", min_value=0.0, value=1000.0)
    outras_rendas = col3.number_input("Outras rendas mensais (R$)", min_value=0.0, value=500.0)

# Bloco 4: Tipo de objetivo
with st.expander("🧭 Tipo de Objetivo"):
    tipo_objetivo = st.selectbox("Deseja manter, zerar ou alcançar um valor específico?", ["manter", "zerar", "outro valor"])
    if tipo_objetivo == "outro valor":
        outro_valor = st.number_input("Valor final desejado (R$)", min_value=0.0, value=1000000.0)
    else:
        outro_valor = None

# Cálculo e output
if st.button("Calcular Aporte Ideal"):
    try:
        taxa = taxa_mensal(taxa_juros_anual)
        meses_acc = calcular_meses_acc(idade_atual, idade_aposentadoria)
        meses_cons = calcular_meses_cons(idade_aposentadoria, idade_morte)
        resgate_necessario = renda_desejada - previdencia - outras_rendas

        cota_bruta, matriz_cotas_liq = gerar_cotas(taxa, meses_acc, meses_cons, valor_inicial, imposto_renda)
        aporte_ideal = bissecao(
            tipo_objetivo.lower(), outro_valor, valor_inicial,
            meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario
        )

        st.success(f"💰 Aporte mensal necessário: R$ {aporte_ideal:,.2f}")

        patrimonio_mensal, _ = calcular_aporte(
            aporte_ideal, valor_inicial, meses_acc, taxa,
            cota_bruta, matriz_cotas_liq, resgate_necessario
        )

        # Criar lista de anos
        anos = list(range(idade_atual, idade_atual + len(patrimonio_mensal)//12 + 1))
        valores_por_ano = [
            sum(patrimonio_mensal[i*12:(i+1)*12]) / 12
            for i in range(len(anos))
        ]

        # Gráfico
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(anos[:len(valores_por_ano)], valores_por_ano, label="Patrimônio projetado", linewidth=2)
        ax.set_xlabel("Idade")
        ax.set_ylabel("R$ Patrimônio")
        ax.set_title("📊 Evolução do Patrimônio ao Longo do Tempo")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

    except Exception as e:
        st.error(f"⚠️ Erro: {str(e)}")

