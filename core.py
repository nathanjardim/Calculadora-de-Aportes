import numpy as np

# Converte uma taxa anual em taxa mensal equivalente
def taxa_mensal(taxa_anual):
    return (1 + taxa_anual) ** (1 / 12) - 1

# Simula a evolução do patrimônio até o fim da expectativa de vida
def simular_aposentadoria(
    idade_atual,
    idade_aposentadoria,
    expectativa_vida,
    poupanca_inicial,
    aporte_mensal,
    renda_mensal,
    rentabilidade_anual,
    imposto,
):
    meses_total = (expectativa_vida - idade_atual) * 12  # Total de meses simulados
    meses_aporte = (idade_aposentadoria - idade_atual) * 12  # Período de acumulação (aportes)

    saldo = poupanca_inicial  # Valor inicial investido
    rentab_mensal = taxa_mensal(rentabilidade_anual)  # Rentabilidade mensal equivalente
    patrimonio_no_aposentadoria = None  # Para armazenar o valor acumulado na aposentadoria
    historico = []  # Lista para registrar a evolução mês a mês

    for mes in range(meses_total):
        saldo *= (1 + rentab_mensal)  # Aplicação da rentabilidade mensal

        if mes < meses_aporte:
            saldo += aporte_mensal  # Durante a fase de acumulação, soma os aportes
        else:
            saque_bruto = renda_mensal / (1 - imposto)  # Corrige a renda desejada para o valor bruto antes do imposto
            saldo -= saque_bruto  # Subtrai os saques mensais durante a aposentadoria

        historico.append(saldo)  # Armazena o saldo atual

        if mes == meses_aporte - 1:
            patrimonio_no_aposentadoria = saldo  # Marca o patrimônio acumulado na aposentadoria

    return saldo, patrimonio_no_aposentadoria, historico  # Retorna saldo final, patrimônio na aposentadoria e histórico completo

# Define qual é o valor-alvo de patrimônio no fim da simulação, de acordo com o modo escolhido
def determinar_alvo(modo, patrimonio_aposentadoria, valor_final_desejado):
    if modo == "zerar":
        return 0  # Objetivo é consumir todo o patrimônio
    elif modo == "manter":
        return patrimonio_aposentadoria  # Objetivo é manter o patrimônio acumulado na aposentadoria
    elif modo == "atingir":
        return valor_final_desejado or 0  # Objetivo é atingir um valor específico no final
    else:
        raise ValueError("Modo inválido. Use 'zerar', 'manter' ou 'atingir'.")

# Calcula o aporte necessário para atingir o objetivo de aposentadoria com base em simulações iterativas
def calcular_aporte(
    idade_atual,
    idade_aposentadoria,
    expectativa_vida,
    poupanca_inicial,
    renda_mensal,
    rentabilidade_anual,
    imposto,
    modo,
    valor_final_desejado=None,
    renda_atual=None,
    percentual_de_renda=None,
    max_aporte=100_000  # Valor máximo testado como limite superior de aporte
):
    min_aporte = 0  # Valor mínimo testado como limite inferior de aporte
    tolerancia = 1  # Margem de erro aceitável para convergência
    max_iteracoes = 100  # Limite de iterações para evitar loop infinito
    iteracoes = 0

    # Algoritmo de bisseção para encontrar o aporte necessário
    while max_aporte - min_aporte > tolerancia and iteracoes < max_iteracoes:
        iteracoes += 1
        teste = (min_aporte + max_aporte) / 2  # Valor intermediário entre os limites

        saldo_final, patrimonio_aposentadoria, _ = simular_aposentadoria(
            idade_atual,
            idade_aposentadoria,
            expectativa_vida,
            poupanca_inicial,
            teste,
            renda_mensal,
            rentabilidade_anual,
            imposto,
        )

        alvo = determinar_alvo(modo, patrimonio_aposentadoria, valor_final_desejado)

        # Ajusta os limites com base no resultado
        if saldo_final > alvo:
            max_aporte = teste
        else:
            min_aporte = teste

    # Validação final: verifica se o objetivo é atingível com o aporte máximo
    saldo_final, patrimonio_aposentadoria, _ = simular_aposentadoria(
        idade_atual,
        idade_aposentadoria,
        expectativa_vida,
        poupanca_inicial,
        max_aporte,
        renda_mensal,
        rentabilidade_anual,
        imposto,
    )
    alvo = determinar_alvo(modo, patrimonio_aposentadoria, valor_final_desejado)

    if saldo_final < alvo - tolerancia:
        return {"aporte_mensal": None}  # Objetivo inalcançável mesmo com aporte máximo

    # Retorna o aporte médio entre os limites finais encontrados
    return {"aporte_mensal": round((min_aporte + max_aporte) / 2, 2)}
