# core.py

# Converte taxa anual para taxa mensal equivalente
def taxa_mensal(taxa_anual):
    return (1 + taxa_anual) ** (1 / 12) - 1

# IR tabela progressiva mensal de 2024
def ir_progressivo(valor):
    if valor <= 2112:
        return 0
    elif valor <= 2826.65:
        return valor * 0.075 - 158.4
    elif valor <= 3751.05:
        return valor * 0.15 - 370.4
    elif valor <= 4664.68:
        return valor * 0.225 - 651.73
    else:
        return valor * 0.275 - 884.96

# IR tabela regressiva conforme meses desde o aporte
def ir_regressivo(valor, mes):
    anos = mes // 12
    if anos < 2:
        return valor * 0.35
    elif anos < 4:
        return valor * 0.30
    elif anos < 6:
        return valor * 0.25
    elif anos < 8:
        return valor * 0.20
    elif anos < 10:
        return valor * 0.15
    else:
        return valor * 0.10

# Simula a evolução do patrimônio mês a mês até o fim da vida com função de IR customizada
def simular_aposentadoria(
    idade_atual,
    idade_aposentadoria,
    expectativa_vida,
    poupanca_inicial,
    aporte_mensal,
    renda_mensal,
    rentabilidade_anual,
    func_ir  # função que calcula IR a cada mês
):
    meses_total = (expectativa_vida - idade_atual) * 12
    meses_aporte = (idade_aposentadoria - idade_atual) * 12

    saldo = poupanca_inicial
    rentab_mensal = taxa_mensal(rentabilidade_anual)
    patrimonio_no_aposentadoria = None
    historico = []
    total_ir_pago = 0

    for mes in range(meses_total):
        saldo *= (1 + rentab_mensal)

        if mes < meses_aporte:
            saldo += aporte_mensal
        else:
            saque_liquido = renda_mensal
            saque_bruto_estimado = saque_liquido / 0.85  # chute inicial
            ir = func_ir(saque_bruto_estimado, mes - meses_aporte)
            saque_bruto = saque_liquido + ir
            saldo -= saque_bruto
            total_ir_pago += ir

        historico.append(saldo)

        if mes == meses_aporte - 1:
            patrimonio_no_aposentadoria = saldo

    return saldo, patrimonio_no_aposentadoria, historico, total_ir_pago

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

# Função genérica para calcular aporte com uma função de IR específica
def calcular_aporte_com_ir(
    idade_atual,
    idade_aposentadoria,
    expectativa_vida,
    poupanca_inicial,
    renda_mensal,
    rentabilidade_anual,
    modo,
    func_ir,
    valor_final_desejado=None,
    max_aporte=100_000
):
    min_aporte = 0
    tolerancia = 1
    max_iteracoes = 100
    iteracoes = 0

    while max_aporte - min_aporte > tolerancia and iteracoes < max_iteracoes:
        iteracoes += 1
        teste = (min_aporte + max_aporte) / 2

        saldo_final, patrimonio_aposentadoria, _, _ = simular_aposentadoria(
            idade_atual,
            idade_aposentadoria,
            expectativa_vida,
            poupanca_inicial,
            teste,
            renda_mensal,
            rentabilidade_anual,
            func_ir,
        )

        alvo = determinar_alvo(modo, patrimonio_aposentadoria, valor_final_desejado)

        if saldo_final > alvo:
            max_aporte = teste
        else:
            min_aporte = teste

    saldo_final, patrimonio_aposentadoria, _, _ = simular_aposentadoria(
        idade_atual,
        idade_aposentadoria,
        expectativa_vida,
        poupanca_inicial,
        max_aporte,
        renda_mensal,
        rentabilidade_anual,
        func_ir,
    )
    alvo = determinar_alvo(modo, patrimonio_aposentadoria, valor_final_desejado)

    if saldo_final < alvo - tolerancia:
        return None, None

    aporte_final = round((min_aporte + max_aporte) / 2, 2)
    _, _, hist, total_ir = simular_aposentadoria(
        idade_atual,
        idade_aposentadoria,
        expectativa_vida,
        poupanca_inicial,
        aporte_final,
        renda_mensal,
        rentabilidade_anual,
        func_ir,
    )
    return aporte_final, total_ir

# Calcula o aporte comparando os dois regimes e selecionando o mais vantajoso
def calcular_aporte(
    idade_atual,
    idade_aposentadoria,
    expectativa_vida,
    poupanca_inicial,
    renda_mensal,
    rentabilidade_anual,
    imposto,  # ignorado agora, mantido para compatibilidade
    modo,
    valor_final_desejado=None,
    renda_atual=None,
    percentual_de_renda=None,
    max_aporte=100_000
):
    aporte_prog, ir_prog = calcular_aporte_com_ir(
        idade_atual, idade_aposentadoria, expectativa_vida,
        poupanca_inicial, renda_mensal, rentabilidade_anual,
        modo, lambda v, m: ir_progressivo(v),
        valor_final_desejado, max_aporte
    )

    aporte_regr, ir_regr = calcular_aporte_com_ir(
        idade_atual, idade_aposentadoria, expectativa_vida,
        poupanca_inicial, renda_mensal, rentabilidade_anual,
        modo, ir_regressivo,
        valor_final_desejado, max_aporte
    )

    if aporte_prog is None and aporte_regr is None:
        return {"aporte_mensal": None}

    if aporte_prog is None:
        return {"aporte_mensal": aporte_regr, "regime": "regressivo"}

    if aporte_regr is None:
        return {"aporte_mensal": aporte_prog, "regime": "progressivo"}

    if aporte_prog < aporte_regr:
        return {"aporte_mensal": aporte_prog, "regime": "progressivo"}
    else:
        return {"aporte_mensal": aporte_regr, "regime": "regressivo"}
