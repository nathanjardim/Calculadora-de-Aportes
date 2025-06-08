import numpy as np

def taxa_mensal(taxa_anual):
    return (1 + taxa_anual) ** (1/12) - 1

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
            bruto = cota_bruta[meses_acc + 1 + j]
            base = cota_bruta[i]
            liquido = bruto - (bruto - base) * imposto_renda
            linha.append(liquido)
        matriz_cotas_liq.append(linha)

    return cota_bruta, matriz_cotas_liq

def calcular_aporte(valor_aporte, valor_inicial, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario):
    patrimonio = [valor_inicial]
    aportes = [valor_inicial] + [valor_aporte] * meses_acc

    for i in range(1, len(aportes)):
        novo_valor = patrimonio[-1] * (1 + taxa) + aportes[i]
        patrimonio.append(novo_valor)

    qtd_cotas_total = [p / c if c != 0 else 0 for p, c in zip(patrimonio, cota_bruta[:len(patrimonio)])]
    qtd_cotas_aportes = [a / c if c != 0 else 0 for a, c in zip(aportes, cota_bruta[:len(aportes)])]

    nova_matriz = np.array(matriz_cotas_liq).T
    valor_liquido2 = []

    for col in range(nova_matriz.shape[0]):
        linha_liquida = [a * nova_matriz[col, i] for i, a in enumerate(qtd_cotas_aportes)]
        valor_liquido2.append(linha_liquida)

    valor_liquido = np.array(valor_liquido2).T
    patrimonio_liquido = [sum(valor_liquido[:, i]) for i in range(valor_liquido.shape[1])]

    return patrimonio + patrimonio_liquido, patrimonio_liquido

def bissecao(tipo_objetivo, outro_valor, valor_inicial, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario):
    inf, sup = 20, 40000
    max_iter = 50

    for _ in range(max_iter):
        mid = (inf + sup) / 2
        patrimonio, patrimonio_liquido = calcular_aporte(mid, valor_inicial, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario)

        if tipo_objetivo == 'manter':
            objetivo = patrimonio[meses_acc]
            final = patrimonio[-1]
            erro = final - objetivo
        elif tipo_objetivo == 'zerar':
            erro = patrimonio_liquido[-2]
        else:
            erro = patrimonio[-1] - outro_valor

        if abs(erro) < 0.01:
            return round(mid, 2)

        if tipo_objetivo in ['manter', 'outro valor']:
            if erro < 0:
                inf = mid
            else:
                sup = mid
        elif tipo_objetivo == 'zerar':
            if erro < resgate_necessario:
                inf = mid
            else:
                sup = mid

    return None
