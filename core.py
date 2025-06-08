import numpy as np

def taxa_mensal(taxa_anual):
    return (1 + taxa_anual)**(1 / 12) - 1

def calcular_meses_acc(idade_atual, idade_aposentadoria):
    return (idade_aposentadoria - idade_atual + 1) * 12

def calcular_meses_cons(idade_aposentadoria, idade_fim):
    return (idade_fim - idade_aposentadoria) * 12

def gerar_cotas(taxa, meses_acc, meses_cons, valor_inicial, imposto_renda):
    total_meses = meses_acc + meses_cons
    cota_bruta = [1]
    for _ in range(total_meses):
        cota_bruta.append(cota_bruta[-1] * (1 + taxa))
    if valor_inicial == 0:
        cota_bruta = cota_bruta[1:]

    matriz_cotas_liq = []
    for i in range(meses_acc + 1):
        linha = []
        for j in range(meses_cons):
            cota_liq = cota_bruta[meses_acc + 1 + j] - (cota_bruta[meses_acc + 1 + j] - cota_bruta[i]) * imposto_renda
            linha.append(cota_liq)
        matriz_cotas_liq.append(linha)
    return cota_bruta, matriz_cotas_liq

def calcular_aporte(aporte, valor_inicial, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario):
    patrimonio = [valor_inicial]
    aportes = [valor_inicial] + [aporte] * meses_acc

    for i in range(meses_acc):
        patrimonio.append(patrimonio[-1] * (1 + taxa) + aporte)

    if patrimonio[0] == 0:
        patrimonio.pop(0)

    qtd_cotas_total = [p / c if c != 0 else 0 for p, c in zip(patrimonio, cota_bruta[:len(patrimonio)])]
    qtd_cotas_aportes = [a / c if c != 0 else 0 for a, c in zip(aportes, cota_bruta[:len(aportes)])]

    nova_matriz = np.array(matriz_cotas_liq).T
    valor_liquido = []
    cotas_restantes = []

    for col in range(nova_matriz.shape[0]):
        linha_liquida = [qtd_cotas_aportes[i] * nova_matriz[col, i] for i in range(len(qtd_cotas_aportes))]
        resgate = 0
        for i in range(len(linha_liquida)):
            if resgate >= resgate_necessario:
                linha_liquida[i] = 0
                continue
            if linha_liquida[i] >= resgate_necessario - resgate:
                qtd_cotas_aportes[i] -= (resgate_necessario - resgate) / matriz_cotas_liq[i][col]
                linha_liquida[i] = resgate_necessario - resgate
                resgate = resgate_necessario
            else:
                resgate += linha_liquida[i]
                qtd_cotas_aportes[i] = 0

        cotas_restantes.append(sum(qtd_cotas_aportes))
        valor_liquido.append(sum([
            qtd_cotas_aportes[i] * nova_matriz[col, i] for i in range(len(qtd_cotas_aportes))
        ]))

    patrimonio_mensal = patrimonio + [
        cota_bruta[meses_acc + 1 + i] * cotas_restantes[i] for i in range(len(cotas_restantes))
    ]

    patrimonio_mensal = [float(v) for v in patrimonio_mensal]
    return patrimonio_mensal, valor_liquido

def bissecao(tipo_objetivo, outro_valor, valor_inicial, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario):
    limite_iteracoes = 100
    tolerancia = 0.01
    inf, sup = 0, 100000

    try:
        meta = calcular_aporte(0, valor_inicial, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario)[0][meses_acc]
    except:
        raise Exception("Erro ao calcular a meta financeira. Verifique seus dados.")

    for _ in range(limite_iteracoes):
        mid = (inf + sup) / 2
        patrimonio, _ = calcular_aporte(mid, valor_inicial, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario)
        final = patrimonio[-1]

        if tipo_objetivo == "manter":
            alvo = patrimonio[meses_acc]
        elif tipo_objetivo == "zerar":
            alvo = 0
        elif tipo_objetivo == "outro valor" and outro_valor is not None:
            alvo = outro_valor
        else:
            raise Exception("Tipo de objetivo inválido.")

        if abs(final - alvo) < tolerancia:
            return round(mid, 2)
        elif final < alvo:
            inf = mid
        else:
            sup = mid

    raise Exception("⚠️ O sistema não conseguiu calcular um valor de aporte viável com os dados fornecidos. Tente ajustá-los para objetivos mais alcançáveis.")
