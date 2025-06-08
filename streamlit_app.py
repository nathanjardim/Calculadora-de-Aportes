import streamlit as st
from core import (
    taxa_mensal, calcular_meses_acc, calcular_meses_cons,
    gerar_cotas, calcular_aporte, bissecao
)

st.set_page_config(page_title="Calculadora de Aportes para Aposentadoria", layout="centered")
st.title("📈 Calculadora de Aportes para Aposentadoria")

try:
    idade_atual = st.number_input("Idade atual", min_value=0, max_value=120, value=30)
    idade_aposentadoria = st.number_input("Idade de aposentadoria", min_value=idade_atual+1, max_value=120, value=60)
    idade_morte = st.number_input("Expectativa de vida", min_value=idade_aposentadoria+1, max_value=130, value=90)

    renda_desejada = st.number_input("Renda mensal desejada na aposentadoria (R$)", min_value=0.0, value=5000.0)
    outras_rendas = st.number_input("Outras rendas mensais esperadas na aposentadoria (R$)", min_value=0.0, value=0.0)
    previdencia = st.number_input("Valor mensal da previdência esperada (R$)", min_value=0.0, value=0.0)

    valor_inicial = st.number_input("Valor já investido atualmente (R$)", min_value=0.0, value=0.0)
    taxa_anual = st.number_input("Rentabilidade anual esperada (ex: 0.08 = 8%)", min_value=0.0, max_value=1.0, value=0.08)
    imposto = st.number_input("Alíquota de imposto sobre lucro (ex: 0.15 = 15%)", min_value=0.0, max_value=1.0, value=0.15)

    tipo_objetivo = st.selectbox("Objetivo com o patrimônio ao final", ["manter", "zerar", "outro valor"])
    outro_valor = None
    if tipo_objetivo == "outro valor":
        outro_valor = st.number_input("Valor desejado ao final do período (R$)", min_value=0.0, value=100000.0)

    if st.button("Calcular aporte ideal"):
        try:
            taxa = taxa_mensal(taxa_anual)
            meses_acc = calcular_meses_acc(idade_atual, idade_aposentadoria)
            meses_cons = calcular_meses_cons(idade_aposentadoria, idade_morte)
            resgate_necessario = renda_desejada - outras_rendas - previdencia

            cota_bruta, matriz_cotas_liq = gerar_cotas(taxa, meses_acc, meses_cons, valor_inicial, imposto)

            aporte_ideal = bissecao(
                tipo_objetivo.lower(),
                outro_valor,
                valor_inicial,
                meses_acc,
                taxa,
                cota_bruta,
                matriz_cotas_liq,
                resgate_necessario
            )

            st.success(f"Aporte mensal ideal: R$ {aporte_ideal:,.2f}")

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

except Exception as e:
    st.error(f"⚠️ Erro inesperado: {str(e)}")
