import numpy as np

def taxa_mensal(taxa_anual):
    return (1 + taxa_anual)**(1/12) - 1

def calcular_meses_acc(dados):
    return (dados['idade_aposentadoria'] - dados['idade_atual'] + 1) * 12

def calcular_meses_cons(dados):
    return (dados['idade_morte'] - dados['idade_aposentadoria']) * 12

def calcular_aporte(valor_aporte, dados, cota_bruta, matriz_cotas_liq, meses_acumulacao, resgate_necessario):
    if dados['valor_inicial'] != 0:
        patrimonio = [dados['valor_inicial']]
    else:
        patrimonio = [0]

    aportes = [dados['valor_inicial']]
    for _ in range(1, meses_acumulacao + 1):
        aportes.append(valor_aporte)

    for i in range(1, len(aportes)):
        patrimonio.append(patrimonio[i-1]*(1+dados['taxa_mensal']) + aportes[i])

    if patrimonio[1] == 0:
        patrimonio.pop(0)

    qtd_cotas_total = [p/c if c != 0 else 0 for p, c in zip(patrimonio, cota_bruta)]
    qtd_cotas_aportes = [a/c if c != 0 else 0 for a, c in zip(aportes, cota_bruta)]

    novo_cota_bruta = cota_bruta[len(qtd_cotas_aportes):]
    nova_matriz = np.array(matriz_cotas_liq).T

    valor_liquido2 = []
    matriz_resgates = []
    qtd_cotas_tempo = []

    for col in range(nova_matriz.shape[0]):
        linha_liquida = [float(a * nova_matriz[col, i]) for i, a in enumerate(qtd_cotas_aportes)]
        resgate_liquido = 0
        linha_resgates = []

        for i, valor in enumerate(linha_liquida):
            if resgate_liquido >= resgate_necessario:
                linha_resgates.append(0)
                continue

            if valor >= resgate_necessario - resgate_liquido:
                retirada = resgate_necessario - resgate_liquido
                linha_liquida[i] -= retirada
                qtd_cotas_aportes[i] -= retirada / matriz_cotas_liq[i][col]
                linha_resgates.append(retirada)
                resgate_liquido += retirada
            else:
                resgate_liquido += valor
                linha_resgates.append(valor)
                linha_liquida[i] = 0
                qtd_cotas_aportes[i] = 0

        qtd_cotas_tempo.append(qtd_cotas_aportes.copy())
        valor_liquido2.append(linha_liquida)
        matriz_resgates.append(linha_resgates)

    valor_liquido = np.array(valor_liquido2).T
    cotas_sobrando = np.array(qtd_cotas_tempo).T
    cotas_no_tempo = qtd_cotas_total + list(np.sum(cotas_sobrando, axis=0))
    patrimonio_bruto = [a * b for a, b in zip(cota_bruta, cotas_no_tempo)]

    patrimonio_liquido = [sum(valor_liquido[:, i]) for i in range(valor_liquido.shape[1])]

    if dados['tipo_objetivo'] == 'manter':
        funcao_objetivo = patrimonio_bruto[-1] - patrimonio_bruto[meses_acumulacao]
    elif dados['tipo_objetivo'] == 'zerar':
        funcao_objetivo = patrimonio_liquido[-2]
    elif dados['tipo_objetivo'] == 'outro valor':
        funcao_objetivo = patrimonio_bruto[-1]

    return funcao_objetivo, patrimonio_bruto

def bissecao(dados, cota_bruta, matriz_cotas_liq, meses_acumulacao, resgate_necessario):
    x, y = 20, 40000
    while abs(calcular_aporte(x, dados, cota_bruta, matriz_cotas_liq, meses_acumulacao, resgate_necessario)[0] - 
              calcular_aporte(y, dados, cota_bruta, matriz_cotas_liq, meses_acumulacao, resgate_necessario)[0]) > 0.1:
        novo = (x + y) / 2
        if abs(novo - x) < 0.01:
            return 'Não há necessidade de aportes para seu objetivo'
        if calcular_aporte(novo, dados, cota_bruta, matriz_cotas_liq, meses_acumulacao, resgate_necessario)[0] < 0:
            x = novo
        else:
            y = novo
    return novo

def bissecao2(dados, cota_bruta, matriz_cotas_liq, meses_acumulacao, resgate_necessario, outro_valor):
    x, y = 20, 40000
    alvo = resgate_necessario if dados['tipo_objetivo'] == 'zerar' else outro_valor
    while abs(calcular_aporte(x, dados, cota_bruta, matriz_cotas_liq, meses_acumulacao, resgate_necessario)[0] - alvo) > 0.01:
        novo = (x + y) / 2
        if abs(novo - x) < 0.01:
            return 'Não há necessidade de aportes para seu objetivo'
        if calcular_aporte(novo, dados, cota_bruta, matriz_cotas_liq, meses_acumulacao, resgate_necessario)[0] < alvo:
            x = novo
        else:
            y = novo
    return novo

def simular(dados):
    dados['taxa_mensal'] = taxa_mensal(dados['taxa_juros_anual'])
    meses_acumulacao = calcular_meses_acc(dados)
    meses_consumo = calcular_meses_cons(dados)
    resgate_necessario = dados['renda_desejada'] - dados['outras_rendas'] - dados['previdencia']

    cota_bruta = [1]
    for _ in range(meses_acumulacao + meses_consumo):
        cota_bruta.append(cota_bruta[-1] * (1 + dados['taxa_mensal']))
    if dados['valor_inicial'] == 0:
        cota_bruta.insert(0, 1)
        cota_bruta.pop()

    matriz_cotas_liq = []
    for i, cota2 in enumerate(cota_bruta[:meses_acumulacao+1]):
        linha = []
        for cota3 in cota_bruta[meses_acumulacao+1:]:
            cota_liq = cota3 - (cota3 - cota2) * dados['imposto_renda']
            linha.append(cota_liq)
        matriz_cotas_liq.append(linha)

    if dados['tipo_objetivo'] == 'manter':
        aporte = bissecao(dados, cota_bruta, matriz_cotas_liq, meses_acumulacao, resgate_necessario)
    else:
        aporte = bissecao2(dados, cota_bruta, matriz_cotas_liq, meses_acumulacao, resgate_necessario, dados.get('outro_valor', 0))

    if isinstance(aporte, float):
        _, patrimonio = calcular_aporte(aporte, dados, cota_bruta, matriz_cotas_liq, meses_acumulacao, resgate_necessario)
        patrimonio_aposentadoria = round(patrimonio[meses_acumulacao], 2)
        return {
            "aporte_mensal": round(aporte, 2),
            "patrimonio_aposentadoria": patrimonio_aposentadoria,
            "patrimonio_mensal": patrimonio
        }
    else:
        return {
            "aporte_mensal": aporte,
            "patrimonio_aposentadoria": 0,
            "patrimonio_mensal": []
        }
