import numpy as np

def taxa_mensal(taxa_anual):
    return (1 + taxa_anual) ** (1 / 12) - 1

def calcular_meses_acc(dados):
    return (dados['idade_aposentadoria'] - dados['idade_atual'] + 1) * 12

def calcular_meses_cons(dados):
    return (dados['idade_morte'] - dados['idade_aposentadoria']) * 12

def calcular_aporte(valor_aporte, dados, meses_acumulacao, meses_consumo, cota_bruta, matriz_cotas_liq, resgate_necessario, outro_valor=None):
    patrimonio = [dados['valor_inicial']]
    aportes = [dados['valor_inicial']] + [valor_aporte] * meses_acumulacao

    for i in range(1, len(aportes)):
        patrimonio.append(patrimonio[-1] * (1 + dados['taxa_mensal']) + aportes[i])

    if patrimonio[1] == 0:
        patrimonio.pop(0)

    qtd_cotas_total = [p / c if c != 0 else 0 for p, c in zip(patrimonio, cota_bruta)]
    qtd_cotas_aportes = [a / c if c != 0 else 0 for a, c in zip(aportes, cota_bruta)]

    nova_matriz = np.array(matriz_cotas_liq).T
    valor_liquido2 = []
    matriz_resgates = []
    qtd_cotas_tempo = []

    for col in range(nova_matriz.shape[0]):
        linha_liquida = [a * nova_matriz[col, i] for i, a in enumerate(qtd_cotas_aportes)]
        resgate_liquido = 0
        linha_resgates = []

        for i, valor in enumerate(linha_liquida):
            if resgate_liquido >= resgate_necessario:
                linha_resgates.append(0)
            elif valor >= resgate_necessario - resgate_liquido:
                dif = resgate_necessario - resgate_liquido
                linha_liquida[i] -= dif
                qtd_cotas_aportes[i] -= dif / matriz_cotas_liq[i][col]
                linha_resgates.append(dif)
                resgate_liquido = resgate_necessario
            else:
                resgate_liquido += valor
                linha_resgates.append(valor)
                linha_liquida[i] = 0
                qtd_cotas_aportes[i] = 0

        qtd_cotas_tempo.append(qtd_cotas_aportes.copy())
        valor_liquido2.append(linha_liquida)
        matriz_resgates.append(linha_resgates)

    valor_liquido = np.array(valor_liquido2).T
    cotas_sobra = np.array(qtd_cotas_tempo).T
    cotas_durante_resgates = list(np.sum(cotas_sobra, axis=0))
    cotas_no_tempo = qtd_cotas_total + cotas_durante_resgates
    patrimonio_bruto = [a * b for a, b in zip(cota_bruta, cotas_no_tempo)]
    patrimonio_liquido = [sum(valor_liquido[:, i]) for i in range(valor_liquido.shape[1])]

    tipo = dados['tipo_objetivo']
    if tipo == 'manter':
        funcao_objetivo = patrimonio_bruto[-1] - patrimonio_bruto[len(aportes)]
    elif tipo == 'zerar':
        funcao_objetivo = patrimonio_liquido[-2]
    elif tipo == 'outro valor':
        funcao_objetivo = patrimonio_bruto[-1]
    else:
        raise ValueError("tipo_objetivo inválido")

    return funcao_objetivo, patrimonio_bruto

def simular_aposentadoria(dados):
    dados['taxa_mensal'] = taxa_mensal(dados['taxa_juros_anual'])
    meses_acumulacao = calcular_meses_acc(dados)
    meses_consumo = calcular_meses_cons(dados)

    resgate_necessario = dados['renda_desejada'] - dados['outras_rendas'] - dados['previdencia']
    outro_valor = dados.get('outro_valor', None)

    cota_bruta = [1]
    for _ in range(meses_acumulacao + meses_consumo):
        cota_bruta.append(cota_bruta[-1] * (1 + dados['taxa_mensal']))

    if dados['valor_inicial'] == 0:
        cota_bruta.insert(0, 1)
        cota_bruta.pop()

    matriz_cotas_liq = []
    for i, cota2 in enumerate(cota_bruta[:meses_acumulacao + 1]):
        linha = []
        for j, cota3 in enumerate(cota_bruta[meses_acumulacao + 1:]):
            cota_liq = cota3 - (cota3 - cota2) * dados['imposto_renda']
            linha.append(cota_liq)
        matriz_cotas_liq.append(linha)

    def bissecao(x, y):
        valor_inf = x
        valor_sup = y
        while abs(valor_sup - valor_inf) > 0.01:
            novo_valor = (valor_sup + valor_inf) / 2
            resultado = calcular_aporte(
                novo_valor, dados, meses_acumulacao, meses_consumo,
                cota_bruta, matriz_cotas_liq, resgate_necessario, outro_valor
            )[0]

            tipo = dados['tipo_objetivo']
            alvo = {
                'manter': 0,
                'zerar': resgate_necessario,
                'outro valor': outro_valor
            }[tipo]

            if resultado < alvo:
                valor_inf = novo_valor
            else:
                valor_sup = novo_valor

        return (valor_sup + valor_inf) / 2

    aporte_ideal = bissecao(20, 40000)
    _, patrimonio = calcular_aporte(
        aporte_ideal, dados, meses_acumulacao, meses_consumo,
        cota_bruta, matriz_cotas_liq, resgate_necessario, outro_valor
    )

    return round(aporte_ideal, 2), patrimonio, meses_acumulacao
