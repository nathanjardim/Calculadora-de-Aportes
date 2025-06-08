import numpy as np

def taxa_mensal(taxa_anual):
    if not (0 <= taxa_anual <= 1):
        raise ValueError("A taxa de juros anual deve estar entre 0 e 1 (ex: 0.08 para 8%).")
    if taxa_anual > 0.5:
        raise ValueError("Atenção: taxa de juros anual muito alta (acima de 50%). Revise o input.")
    return (1 + taxa_anual) ** (1 / 12) - 1

def calcular_meses_acc(idade_atual, idade_aposentadoria):
    if idade_aposentadoria <= idade_atual:
        raise ValueError("A idade de aposentadoria deve ser maior que a idade atual.")
    return (idade_aposentadoria - idade_atual + 1) * 12

def calcular_meses_cons(idade_aposentadoria, idade_morte):
    if idade_morte <= idade_aposentadoria:
        raise ValueError("A idade de morte deve ser maior que a de aposentadoria.")
    return (idade_morte - idade_aposentadoria) * 12

def gerar_cotas(taxa, meses_acc, meses_cons, valor_inicial, imposto):
    if not (0 <= imposto <= 1):
        raise ValueError("O imposto deve estar entre 0 e 1 (ex: 0.15 para 15%).")
    if meses_acc == 0:
        raise ValueError("O período de acumulação não pode ser zero.")

    total_meses = meses_acc + meses_cons
    cota_bruta = np.cumprod(np.full(total_meses + 1, 1 + taxa))

    if valor_inicial == 0:
        cota_bruta = np.insert(cota_bruta, 0, 1)[:-1]

    cotas_finais = cota_bruta[meses_acc + 1:]
    cotas_iniciais = cota_bruta[:meses_acc + 1]
    matriz_cotas_liq = cotas_finais - ((cotas_finais[None, :] - cotas_iniciais[:, None]) * imposto)

    return cota_bruta, matriz_cotas_liq

def calcular_aporte(valor_aporte, valor_inicial, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario):
    if valor_aporte < 0 or valor_inicial < 0 or resgate_necessario < 0:
        raise ValueError("Valores monetários não podem ser negativos.")

    n_aportes = meses_acc + 1
    patrimonio = np.zeros(n_aportes)
    aportes = np.full(n_aportes, valor_aporte)

    if valor_inicial > 0:
        patrimonio[0] = valor_inicial
        aportes[0] = valor_inicial

    for i in range(1, n_aportes):
        patrimonio[i] = patrimonio[i - 1] * (1 + taxa) + aportes[i]

    qtd_cotas_total = patrimonio / cota_bruta[:n_aportes]
    qtd_cotas_aportes = aportes / cota_bruta[:n_aportes]

    nova_matriz = matriz_cotas_liq.T
    cotas_restantes = qtd_cotas_aportes.copy()
    patrimonio_bruto = list(patrimonio)  # fase de acumulação
    patrimonio_liquido = []

    for col_index, cotas_liq_coluna in enumerate(nova_matriz):
        resgatado = 0
        valor_mensal = 0
        for i in range(len(cotas_restantes)):
            if resgatado >= resgate_necessario:
                break
            valor_unit = matriz_cotas_liq[i][col_index]
            qtd_disponivel = cotas_restantes[i]
            valor_disponivel = qtd_disponivel * valor_unit

            if valor_disponivel + resgatado <= resgate_necessario:
                resgatado += valor_disponivel
                cotas_restantes[i] = 0
            else:
                needed = resgate_necessario - resgatado
                cotas_restantes[i] -= needed / valor_unit
                resgatado = resgate_necessario

        valor_mensal = sum(cotas_restantes * cota_bruta[meses_acc + 1 + col_index])
        patrimonio_bruto.append(valor_mensal)
        patrimonio_liquido.append(resgatado)

    return np.array(patrimonio_bruto), np.array(patrimonio_liquido)

def bissecao(tipo_objetivo, outro_valor, valor_inicial, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario):
    if tipo_objetivo not in ["manter", "zerar", "outro valor"]:
        raise ValueError("O tipo de objetivo deve ser: 'manter', 'zerar' ou 'outro valor'.")
    if tipo_objetivo == "outro valor" and outro_valor is None:
        raise ValueError("Você deve informar o valor final desejado para o objetivo 'outro valor'.")

    x, y = 20.0, 40000.0
    tol = 0.1
    max_iter = 100
    iter_count = 0

    if tipo_objetivo == 'manter':
        meta = calcular_aporte(0, valor_inicial, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario)[0][meses_acc]
        while iter_count < max_iter:
            mid = (x + y) / 2
            resultado = calcular_aporte(mid, valor_inicial, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario)[0][-1]
            if abs(resultado - meta) < tol:
                return round(mid, 2)
            if resultado < meta:
                x = mid
            else:
                y = mid
            iter_count += 1
        raise ValueError("Não foi possível encontrar um aporte que satisfaça o objetivo dentro do limite de iterações.")
    else:
        alvo = outro_valor if tipo_objetivo == 'outro valor' else resgate_necessario
        while iter_count < max_iter:
            mid = (x + y) / 2
            resultado = calcular_aporte(mid, valor_inicial, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario)[1][-1]
            if abs(resultado - alvo) < tol:
                return round(mid, 2)
            if resultado < alvo:
                x = mid
            else:
                y = mid
            iter_count += 1
        raise ValueError("Não foi possível encontrar um aporte que satisfaça o objetivo dentro do limite de iterações.")
