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
        raise ValueError("A idade de morte deve ser maior que a idade de aposentadoria.")
    return (idade_morte - idade_aposentadoria) * 12

def gerar_cotas(taxa, meses_acc, meses_cons, valor_inicial, imposto):
    if not (0 <= imposto <= 1):
        raise ValueError("A alíquota de imposto de renda deve estar entre 0 e 1 (ex: 0.15 para 15%).")
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
        raise ValueError("Os valores de aporte, valor inicial e resgate necessário devem ser positivos.")
    if matriz_cotas_liq.shape[0] != meses_acc + 1:
        raise ValueError("A matriz de cotas líquidas está incompatível com o tempo de acumulação.")

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
    patrimonio_mensal = list(patrimonio.copy())  # inclui fase de acumulação

    cotas_vivas = qtd_cotas_aportes.copy()

    for mes_resgate in range(nova_matriz.shape[0]):
        linha_valores = nova_matriz[mes_resgate]
        resgatado = 0
        nova_cotas = cotas_vivas.copy()

        for i in range(len(cotas_vivas)):
            if resgatado >= resgate_necessario:
                break

            valor_cota = linha_valores[i]
            valor_disponivel = nova_cotas[i] * valor_cota
            restante = resgate_necessario - resgatado

            if valor_disponivel >= restante:
                cotas_usadas = restante / valor_cota
                nova_cotas[i] -= cotas_usadas
                resgatado += restante
            else:
                resgatado += valor_disponivel
                nova_cotas[i] = 0

        cotas_vivas = nova_cotas
        patrimonio_mensal.append(np.dot(cotas_vivas, cota_bruta[mes_resgate + n_aportes]))

    return np.array(patrimonio_mensal).flatten().tolist(), None

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
            resultado = calcular_aporte(mid, valor_inicial, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario)[0][-1]
            if abs(resultado - alvo) < tol:
                return round(mid, 2)
            if resultado < alvo:
                x = mid
            else:
                y = mid
            iter_count += 1
        raise ValueError("Não foi possível encontrar um aporte que satisfaça o objetivo dentro do limite de iterações.")
