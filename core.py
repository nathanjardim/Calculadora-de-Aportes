import numpy as np

def taxa_mensal(taxa_anual):
    if taxa_anual < 0 or taxa_anual > 1:
        raise ValueError("A taxa de juros anual deve estar entre 0 e 1.")
    return (1 + taxa_anual) ** (1 / 12) - 1

def calcular_meses_acc(idade_atual, idade_aposentadoria):
    if idade_aposentadoria <= idade_atual:
        raise ValueError("A idade de aposentadoria deve ser maior do que a sua idade atual.")
    return int((idade_aposentadoria - idade_atual) * 12)

def calcular_meses_cons(idade_aposentadoria, idade_morte):
    if idade_morte <= idade_aposentadoria:
        raise ValueError("A expectativa de vida deve ser maior que a idade de aposentadoria.")
    return int((idade_morte - idade_aposentadoria) * 12)

def gerar_cotas(taxa, meses_acc, meses_cons, poupanca_atual, imposto):
    if taxa <= 0 or taxa > 1:
        raise ValueError("A taxa de juros mensal deve estar entre 0 e 1.")
    if imposto < 0 or imposto > 1:
        raise ValueError("O campo de imposto deve ser preenchido como porcentagem decimal.")

    cota_bruta = np.array([(1 + taxa) ** i for i in range(meses_acc + meses_cons)])
    patrimonio_base = poupanca_atual * cota_bruta[:meses_acc]

    matriz_cotas_liq = np.zeros((meses_cons, meses_acc))
    for t in range(meses_cons):
        for s in range(meses_acc):
            tempo = meses_acc + t - s
            if tempo >= 0:
                rendimento_bruto = (1 + taxa) ** tempo
                rendimento_liq = rendimento_bruto * (1 - imposto)
                matriz_cotas_liq[t, s] = rendimento_liq
    return cota_bruta, matriz_cotas_liq

def calcular_aporte(aporte, poupanca_atual, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario):
    if aporte < 0 or poupanca_atual < 0 or meses_acc < 1 or resgate_necessario < 0:
        raise ValueError("Os valores devem ser positivos.")

    aportes = np.array([aporte * (1 + taxa) ** i for i in range(meses_acc)])
    patrimonio = np.concatenate(([poupanca_atual], aportes)).cumsum()
    patrimonio_bruto = patrimonio[:-1] * cota_bruta[:meses_acc]

    patrimonio_final = np.dot(matriz_cotas_liq, aportes)
    patrimonio_final += poupanca_atual * matriz_cotas_liq[:, 0]

    return patrimonio_bruto.tolist(), patrimonio_final.tolist()

def bissecao(tipo_objetivo, outro_valor, poupanca_atual, meses_acc, taxa, cota_bruta, matriz_cotas_liq, resgate_necessario, max_iter=100, tolerancia=1):
    if tipo_objetivo not in ["manter", "zerar", "outro valor"]:
        raise ValueError("Tipo de objetivo inválido. Use: 'manter', 'zerar' ou 'outro valor'.")
    if tipo_objetivo == "outro valor" and outro_valor is None:
        raise ValueError("É necessário informar o valor final desejado ao escolher 'outro valor'.")

    def objetivo(aporte):
        _, patrimonio_final = calcular_aporte(
            aporte,
            poupanca_atual,
            meses_acc,
            taxa,
            cota_bruta,
            matriz_cotas_liq,
            resgate_necessario
        )
        if tipo_objetivo == "manter":
            return patrimonio_final[-1] - poupanca_atual
        elif tipo_objetivo == "zerar":
            return patrimonio_final[-1]
        elif tipo_objetivo == "outro valor":
            return patrimonio_final[-1] - outro_valor

    limite_inferior = 0
    limite_superior = 1e6
    iteracao = 0

    while iteracao < max_iter:
        aporte_medio = (limite_inferior + limite_superior) / 2
        resultado = objetivo(aporte_medio)

        if abs(resultado) <= tolerancia:
            return aporte_medio
        if (tipo_objetivo == "zerar" and resultado > 0) or resultado > 0:
            limite_superior = aporte_medio
        else:
            limite_inferior = aporte_medio
        iteracao += 1

    raise ValueError("Não foi possível encontrar um aporte viável com os dados fornecidos.")

def simular(dados):
    try:
        taxa = taxa_mensal(dados["taxa_anual"])
        meses_acc = calcular_meses_acc(dados["idade_atual"], dados["idade_aposentadoria"])
        meses_cons = calcular_meses_cons(dados["idade_aposentadoria"], dados["idade_morte"])
        resgate_necessario = dados["renda_desejada"] - dados["outras_rendas"] - dados["previdencia"]

        cota_bruta, matriz_cotas_liq = gerar_cotas(taxa, meses_acc, meses_cons, dados["poupanca_atual"], dados["imposto"])

        aporte_ideal = bissecao(
            dados["tipo_objetivo"],
            dados["outro_valor"],
            dados["poupanca_atual"],
            meses_acc,
            taxa,
            cota_bruta,
            matriz_cotas_liq,
            resgate_necessario
        )

        patrimonio_bruto, _ = calcular_aporte(
            aporte_ideal,
            dados["poupanca_atual"],
            meses_acc,
            taxa,
            cota_bruta,
            matriz_cotas_liq,
            resgate_necessario
        )

        return aporte_ideal, patrimonio_bruto

    except Exception as e:
        raise ValueError(str(e))
