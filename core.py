import numpy as np

# Converte taxa anual para taxa mensal equivalente
def taxa_mensal(taxa_anual):
    return (1 + taxa_anual) ** (1 / 12) - 1

# Simula a evolução do patrimônio mês a mês até o fim da vida
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
    meses_total = (expectativa_vida - idade_atual) * 12
    meses_aporte = (idade_aposentadoria - idade_atual) * 12

    saldo = poupanca_inicial
    rentab_mensal = taxa_mensal(rentabilidade_anual)
    patrimonio_no_aposentadoria = None
    historico = []

    for mes in range(meses_total):
        saldo *= (1 + rentab_mensal)

        if mes < meses_aporte:
            saldo += aporte_mensal
        else:
            saque_bruto = renda_mensal / (1 - imposto)
            saldo -= saque_bruto

        historico.append(saldo)

        if mes == meses_aporte - 1:
            patrimonio_no_aposentadoria = saldo

    return saldo, patrimonio_no_aposentadoria, historico

# Define o valor alvo a ser atingido no final da simulação
def determinar_alvo(modo, patrimonio_aposentadoria, valor_final_desejado):
    if modo == "zerar":
        return 0
    elif modo == "manter":
        return patrimonio_aposentadoria
    elif modo == "atingir":
        return valor_final_desejado or 0
    else:
        raise ValueError("Modo inválido. Use 'zerar', 'manter' ou 'atingir'.")

# Calcula o aporte mensal necessário para atingir o objetivo escolhido
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
    max_aporte=100_000
):
    min_aporte = 0
    tolerancia = 1
    max_iteracoes = 100
    iteracoes = 0

    # Busca binária para encontrar o aporte ideal
    while max_aporte - min_aporte > tolerancia and iteracoes < max_iteracoes:
        iteracoes += 1
        teste = (min_aporte + max_aporte) / 2

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

        if saldo_final > alvo:
            max_aporte = teste
        else:
            min_aporte = teste

    # Verifica se o objetivo é possível mesmo com aporte máximo
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
        return {"aporte_mensal": None}

    return {"aporte_mensal": round((min_aporte + max_aporte) / 2, 2)}
