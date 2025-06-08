import streamlit as st
import pandas as pd
from core import (
    taxa_mensal, calcular_meses_acc, calcular_meses_cons,
    gerar_cotas, calcular_aporte, bissecao
)

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
        taxa = taxa_mensal(taxa_anual)
        meses_acc = calcular_meses_acc(idade_atual, idade_aposentadoria)
        meses_cons = calcular_meses_cons(idade_aposentadoria, idade_morte)
        resgate_necessario = renda_desejada - outras_rendas - previdencia

        cota_bruta, matriz_cotas_liq = gerar_cotas(taxa, meses_acc, meses_cons, poupanca_atual, imposto)

        aporte_ideal = bissecao(
            tipo_objetivo.lower(),
            outro_valor,
            poupanca_atual,
            meses_acc,
            taxa,
            cota_bruta,
            matriz_cotas_liq,
            resgate_necessario
        )

        st.success(f"Aporte mensal ideal: R$ {aporte_ideal:,.2f}")
        total_poupanca = aporte_ideal * meses_acc
        percentual_renda = (aporte_ideal / renda_atual) * 100

        st.subheader("📘 Resumo do planejamento")
        colr1, colr2, colr3 = st.columns(3)
        colr1.metric("Aportes mensais", f"R$ {aporte_ideal:,.2f}")
        colr2.metric("Poupança necessária", f"R$ {total_poupanca:,.2f}")
        colr3.metric("Percentual da renda atual", f"{percentual_renda:.2f}%")

        # 📈 Gráfico de patrimônio mês a mês com suavidade no tempo
        patrimonio, _ = calcular_aporte(
            aporte_ideal, poupanca_atual, meses_acc, taxa,
            cota_bruta, matriz_cotas_liq, resgate_necessario
        )

        total_meses = len(patrimonio)
        anos_meses = [idade_atual + (i / 12) for i in range(total_meses)]

        df = pd.DataFrame({
            "Tempo (anos)": anos_meses,
            "Patrimônio Bruto": patrimonio
        })

        st.subheader("📈 Projeção do Patrimônio ao Longo do Tempo (Mensal)")
        st.line_chart(df.set_index("Tempo (anos)"))
        st.caption(f"🔵 Fase de acumulação: até os {idade_aposentadoria} anos • 🔵 Fase de consumo: até os {idade_morte} anos.")

    except ValueError as e:
        erro = str(e)
        if "idade de aposentadoria" in erro:
            st.error("⚠️ A idade de aposentadoria deve ser maior do que a sua idade atual.")
        elif "idade de morte" in erro:
            st.error("⚠️ A expectativa de vida deve ser maior que a idade de aposentadoria.")
        elif "imposto" in erro:
            st.error("⚠️ O campo de imposto deve ser preenchido como porcentagem decimal. Exemplo: 0.15 para 15%.")
        elif "negativos" in erro:
            st.error("⚠️ Por favor, preencha todos os valores com números positivos ou zero.")
        elif "tipo de objetivo" in erro:
            st.error("⚠️ O objetivo selecionado está inválido. Use: 'manter', 'zerar' ou 'outro valor'.")
        elif "informar o valor final" in erro:
            st.error("⚠️ Informe o valor final desejado ao escolher o objetivo 'outro valor'.")
        elif "matriz de cotas líquidas" in erro:
            st.error("⚠️ O cálculo interno falhou por um erro técnico. Tente ajustar os dados e tente novamente.")
        elif "cotas brutas é menor" in erro:
            st.error("🟥 Os dados informados exigem um valor muito alto ou uma idade de vida muito longa. Tente ajustar a expectativa de vida, renda desejada ou rentabilidade para valores mais realistas.")
        elif "não foi possível encontrar um aporte" in erro.lower():
            st.error("⚠️ O sistema não conseguiu calcular um valor de aporte viável com os dados fornecidos. Tente ajustá-los para objetivos mais alcançáveis.")
        elif "taxa de juros anual" in erro:
            st.error("⚠️ Digite a taxa de rentabilidade como decimal. Exemplo: 0.08 para 8% ao ano.")
        elif "muito alta" in erro:
            st.error("⚠️ A rentabilidade anual está muito alta. Revise esse valor, pois pode não ser realista.")
        elif "período de acumulação" in erro:
            st.error("⚠️ Você precisa ter pelo menos 1 ano antes da aposentadoria para acumular investimentos.")
        else:
            st.error(f"⚠️ Erro: {erro}")
