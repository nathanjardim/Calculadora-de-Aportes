import numpy as np


def taxa_mensal(taxa_anual):
    if taxa_anual <= 0 or taxa_anual > 1:
        raise ValueError("A taxa de juros anual deve estar entre 0 e 1 (ex: 0.08 para 8%).")
    return (1 + taxa_anual) ** (1 / 12) - 1


def calcular_meses_acc(idade_atual, idade_aposentadoria):
    if idade_aposentadoria <= idade_atual:
        raise ValueError("A idade de aposentadoria deve ser maior que a idade atual.")
    return (idade_aposentadoria - idade_atual) * 12


def calcular_meses_cons(idade_aposentadoria, idade_morte):
    if idade_morte <= idade_aposentadoria:
        raise ValueError("A expectativa de vida deve ser maior que a idade de aposentadoria.")
    return (idade_morte - idade_aposentadoria) * 12


def gerar_cotas(taxa, meses_acc, meses_cons, poupanca_atual, imposto):
    total_meses = meses_acc + meses_cons
    cota_bruta = np.zeros(total_meses)
    matriz_cotas_liq = np.zeros((meses_cons, total_meses))

    cota_bruta[0] = 1
    for i in range(1, total_meses):
        cota_bruta[i] = cota_bruta[i - 1] * (1 + taxa)

    for i in range(meses_cons):
        for j in range(meses_acc + i, total_meses):
            rendimento = (cota_bruta[j] / cota_bruta[meses_acc + i]) - 1
            fator_ir = 1 - imposto * max(rendimento, 0)
            matriz_cotas_liq[i, j] = cota_bruta[j] * fator_ir

    if poupanca_atual > 0 and np.any(matriz_cotas_liq[0, :] == 0):
        raise ValueError("A matriz de cotas líquidas está incorreta.")

    return cota_bruta, matriz_cotas_liq


def calcular_aporte(
    aporte_mensal,
    poupanca_inicial,
    meses_acc,
    taxa_mensal,
    cota_bruta,
    matriz_cotas_liq,
    saque_mensal
):
    total_meses = len(cota_bruta)
    patrimonio = np.zeros(total_meses)
    patrimonio[0] = poupanca_inicial

    for i in range(1, meses_acc):
        patrimonio[i] = patrimonio[i - 1] * (1 + taxa_mensal) + aporte_mensal

    patrimonio[meses_acc] = patrimonio[meses_acc - 1] * (1 + taxa_mensal) + aporte_mensal

    for i in range(meses_cons):
        idx = meses_acc + i
        if idx >= total_meses:
            break
        valor_cota = matriz_cotas_liq[i, idx]
        if valor_cota == 0:
            raise ValueError("Erro na matriz de cotas líquidas.")
        resgate = saque_mensal / valor_cota
        patrimonio[idx] = patrimonio[idx - 1] * (1 + taxa_mensal) - resgate

    return patrimonio, patrimonio[-1]


def bissecao(
    tipo_objetivo,
    outro_valor,
    poupanca_inicial,
    meses_acc,
    taxa,
    cota_bruta,
    matriz_cotas_liq,
    saque_mensal,
    precisao=0.01,
    max_iter=100
):
    objetivo_final = 0

    if tipo_objetivo == "zerar":
        objetivo_final = 0
    elif tipo_objetivo == "manter":
        objetivo_final = poupanca_inicial
    elif tipo_objetivo == "outro valor":
        if outro_valor is None:
            raise ValueError("É necessário informar o valor final desejado.")
        objetivo_final = outro_valor
    else:
        raise ValueError("Tipo de objetivo inválido.")

    aporte_min = 0
    aporte_max = 1e6
    melhor_aporte = None

    for _ in range(max_iter):
        aporte_medio = (aporte_min + aporte_max) / 2
        _, patrimonio_final = calcular_aporte(
            aporte_medio,
            poupanca_inicial,
            meses_acc,
            taxa,
            cota_bruta,
            matriz_cotas_liq,
            saque_mensal
        )

        diferenca = patrimonio_final - objetivo_final

        if abs(diferenca) <= precisao:
            melhor_aporte = aporte_medio
            break

        if diferenca > 0:
            aporte_max = aporte_medio
        else:
            aporte_min = aporte_medio

    if melhor_aporte is None:
        raise ValueError("Não foi possível encontrar um aporte adequado.")

    return melhor_aporte


def simular(dados):
    taxa = taxa_mensal(dados["taxa_anual"])
    meses_acc = calcular_meses_acc(dados["idade_atual"], dados["idade_aposentadoria"])
    meses_cons = calcular_meses_cons(dados["idade_aposentadoria"], dados["idade_morte"])
    saque_mensal = dados["renda_desejada"] - dados["previdencia"] - dados["outras_rendas"]

    if saque_mensal < 0:
        saque_mensal = 0

    cota_bruta, matriz_cotas_liq = gerar_cotas(
        taxa, meses_acc, meses_cons, dados["poupanca_atual"], dados["imposto"]
    )

    aporte_ideal = bissecao(
        dados["tipo_objetivo"],
        dados.get("outro_valor"),
        dados["poupanca_atual"],
        meses_acc,
        taxa,
        cota_bruta,
        matriz_cotas_liq,
        saque_mensal,
    )

    patrimonio, _ = calcular_aporte(
        aporte_ideal,
        dados["poupanca_atual"],
        meses_acc,
        taxa,
        cota_bruta,
        matriz_cotas_liq,
        saque_mensal,
    )

    return aporte_ideal, patrimonio
