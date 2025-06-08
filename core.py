import numpy as np

def taxa_mensal(taxa_anual):
    return (1 + taxa_anual) ** (1 / 12) - 1

def calcular_meses_acc(idade_atual, idade_aposentadoria):
    return (idade_aposentadoria - idade_atual + 1) * 12

def calcular_meses_cons(idade_aposentadoria, idade_morte):
    return (idade_morte - idade_aposentadoria) * 12

def gerar_cotas(taxa, meses_acc, meses_cons, valor_inicial, imposto):
    total_meses = meses_acc + meses_cons
    cota_bruta = np.cumprod(np.full(total_meses + 1, 1 + taxa))
    if valor_inicial == 0:
        cota_bruta = np.insert(cota_bruta, 0, 1)[:-1]

    cotas_finais = cota_bruta[meses_acc + 1:]
    cotas_iniciais = cota_bruta[:meses_acc + 1]
    matriz_cotas_liq = cotas_finais - ((cotas_finais[None, :] - cotas_iniciais[:, None]) * imposto)
    return cota_bruta, matriz_cotas_liq

def calcular_aporte(valor_aporte, valor_inicial, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario):
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
    valor_liquido = []
    qtd_cotas_tempo = []

    for col in nova_matriz:
        linha_liquida = qtd_cotas_aportes * col
        resgate_liquido = 0
        linha_resgates = np.zeros_like(qtd_cotas_aportes)
        cotas_temp = qtd_cotas_aportes.copy()

        for i in range(len(linha_liquida)):
            if resgate_liquido >= resgate_necessario:
                break
            restante = resgate_necessario - resgate_liquido
            if linha_liquida[i] >= restante:
                linha_resgates[i] = restante
                cotas_temp[i] -= restante / matriz_cotas_liq[i][np.where(nova_matriz == col)[0][0]]
                linha_liquida[i] -= restante
                resgate_liquido = resgate_necessario
            else:
                linha_resgates[i] = linha_liquida[i]
                resgate_liquido += linha_liquida[i]
                linha_liquida[i] = 0
                cotas_temp[i] = 0

        qtd_cotas_tempo.append(cotas_temp)
        valor_liquido.append(linha_liquida)

    valor_liquido = np.array(valor_liquido).T
    cotas_durante_resgates = np.sum(np.array(qtd_cotas_tempo), axis=0)
    cotas_no_tempo = np.concatenate([qtd_cotas_total, cotas_durante_resgates])
    patrimonio_bruto = cota_bruta[:len(cotas_no_tempo)] * cotas_no_tempo
    patrimonio_liquido = np.sum(valor_liquido, axis=0)
    return patrimonio_bruto, patrimonio_liquido

def bissecao(tipo_objetivo, outro_valor, valor_inicial, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario):
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
        return round(mid, 2)
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
        return round(mid, 2)
