import numpy as np

def taxa_mensal(taxa_anual):
    return (1 + taxa_anual)**(1/12) - 1

def calcular_meses_acc(dados):
    return int((dados['idade_aposentadoria'] - dados['idade_atual']) * 12)

def calcular_meses_cons(dados):
    return int((dados['idade_morte'] - dados['idade_aposentadoria']) * 12)

def calcular_aporte(dados, valor_aporte):
    taxa = taxa_mensal(dados['taxa_juros_anual'])
    meses_acumulacao = calcular_meses_acc(dados)
    meses_consumo = calcular_meses_cons(dados)
    resgate_necessario = dados['renda_desejada'] - dados['outras_rendas'] - dados['previdencia']

    cota_bruta = [1]
    for _ in range(meses_acumulacao + meses_consumo):
        cota_bruta.append(cota_bruta[-1] * (1 + taxa))
    if dados['valor_inicial'] == 0:
        cota_bruta.insert(0, 1)
        cota_bruta.pop()

    matriz_cotas_liq = []
    for i in range(meses_acumulacao + 1):
        linha = []
        for j, cota3 in enumerate(cota_bruta[meses_acumulacao+1:]):
            cota2 = cota_bruta[i]
            cota_liq = cota3 - (cota3 - cota2) * dados['imposto_renda']
            linha.append(cota_liq)
        matriz_cotas_liq.append(linha)

    patrimonio = [dados['valor_inicial']] if dados['valor_inicial'] != 0 else [0]
    aportes = [dados['valor_inicial']] + [valor_aporte] * meses_acumulacao
    for i in range(1, len(aportes)):
        patrimonio.append(patrimonio[-1] * (1 + taxa) + aportes[i])
    if patrimonio[1] == 0:
        patrimonio.pop(0)

    qtd_cotas_total = [p / c if c else 0 for p, c in zip(patrimonio, cota_bruta)]
    qtd_cotas_aportes = [a / c if c else 0 for a, c in zip(aportes, cota_bruta)]

    nova_matriz = np.array(matriz_cotas_liq).T
    valor_liquido2 = []
    matriz_resgates = []
    qtd_cotas_tempo = []

    for col in range(nova_matriz.shape[0]):
        linha_liquida = [float(a * nova_matriz[col, i]) for i, a in enumerate(qtd_cotas_aportes)]
        resgate_liquido = 0
        linha_resgates = []

        for i, valor in enumerate(linha_liquida):
            if resgate_necessario == resgate_liquido:
                linha_resgates.append(0)
            elif valor > 0 and valor >= resgate_necessario - resgate_liquido:
                delta = resgate_necessario - resgate_liquido
                linha_liquida[i] -= delta
                qtd_cotas_aportes[i] -= delta / matriz_cotas_liq[i][col]
                linha_resgates.append(delta)
                resgate_liquido += delta
            elif valor > 0:
                resgate_liquido += valor
                linha_resgates.append(valor)
                linha_liquida[i] = 0
                qtd_cotas_aportes[i] = 0
            else:
                linha_resgates.append(0)

        qtd_cotas_tempo.append(qtd_cotas_aportes.copy())
        valor_liquido2.append(linha_liquida)
        matriz_resgates.append(linha_resgates)

    valor_liquido = np.array(valor_liquido2).T
    patrimonio_liquido = [sum(valor_liquido[:, i]) for i in range(valor_liquido.shape[1])]
    cotas_durante_resgates = list(np.sum(np.array(qtd_cotas_tempo).T, axis=0))
    cotas_no_tempo = qtd_cotas_total + cotas_durante_resgates
    patrimonio_bruto = [a * b for a, b in zip(cota_bruta, cotas_no_tempo)]

    if dados['tipo_objetivo'] == 'manter':
        funcao_objetivo = patrimonio_bruto[-1] - patrimonio_bruto[len(aportes)]
    elif dados['tipo_objetivo'] == 'zerar':
        funcao_objetivo = patrimonio_liquido[-2]
    else:
        funcao_objetivo = patrimonio_bruto[-1]

    return funcao_objetivo, patrimonio_bruto

def bissecao(dados, x, y):
    while abs(calcular_aporte(dados, x)[0] - calcular_aporte(dados, y)[0]) > 0.1:
        novo_valor = abs(x + y) / 2
        if calcular_aporte(dados, novo_valor)[0] < 0:
            x = novo_valor
        else:
            y = novo_valor
    return novo_valor

def bissecao2(dados, x, y):
    if dados['tipo_objetivo'] == 'zerar':
        objetivo = dados['renda_desejada'] - dados['outras_rendas'] - dados['previdencia']
    else:
        objetivo = dados['outro_valor']

    while abs(calcular_aporte(dados, x)[0] - objetivo) > 0.01:
        novo_valor = abs(x + y) / 2
        if calcular_aporte(dados, novo_valor)[0] < objetivo:
            x = novo_valor
        else:
            y = novo_valor
    return novo_valor

def simular_aposentadoria(dados):
    if dados['tipo_objetivo'] == 'manter':
        aporte = bissecao(dados, 20, 40000)
    else:
        aporte = bissecao2(dados, 20, 40000)
    if aporte is None:
        return None, []
    if isinstance(aporte, str):
        return aporte, []
    dados['aporte_encontrado'] = round(aporte, 2)
    patrimonio = calcular_aporte(dados, aporte)[1]
    return round(aporte, 2), patrimonio
