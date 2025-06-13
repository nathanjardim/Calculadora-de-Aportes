import numpy as np

def taxa_mensal(taxa_anual: float) -> float:
    if taxa_anual <= 0 or taxa_anual > 1:
        raise ValueError("Taxa de juros anual inválida. Digite como decimal, ex: 0.05 para 5%.")
    return (1 + taxa_anual) ** (1 / 12) - 1

def calcular_meses_acc(idade_atual: int, idade_aposentadoria: int) -> int:
    if idade_aposentadoria <= idade_atual:
        raise ValueError("A idade de aposentadoria deve ser maior que a idade atual.")
    return (idade_aposentadoria - idade_atual) * 12

def calcular_meses_cons(idade_aposentadoria: int, idade_fim: int) -> int:
    if idade_fim <= idade_aposentadoria:
        raise ValueError("A expectativa de vida deve ser maior que a idade de aposentadoria.")
    return (idade_fim - idade_aposentadoria) * 12

def gerar_cotas(taxa_mensal: float, meses_acc: int, meses_cons: int, poupanca_atual: float, imposto: float):
    if poupanca_atual < 0 or imposto < 0 or imposto >= 1:
        raise ValueError("Valores negativos ou impostos inválidos.")

    cotas_brutas = np.zeros(meses_acc + meses_cons + 1)
    cotas_brutas[0] = 1.0
    for i in range(1, len(cotas_brutas)):
        cotas_brutas[i] = cotas_brutas[i - 1] * (1 + taxa_mensal)

    matriz_liq = np.zeros((meses_cons, len(cotas_brutas)))
    for m in range(meses_cons):
        for a in range(len(cotas_brutas)):
            if a + m < len(cotas_brutas):
                bruto = cotas_brutas[a + m] / cotas_brutas[a]
                liquido = bruto - imposto * (bruto - 1)
                matriz_liq[m, a] = liquido

    return cotas_brutas, matriz_liq

def calcular_aporte(aporte: float, poupanca_inicial: float, meses_acc: int, taxa_mensal: float,
                    cotas_brutas: np.ndarray, matriz_liq: np.ndarray, resgate_mensal: float):

    total_cotas = poupanca_inicial / cotas_brutas[0]
    cotas_acumuladas = [total_cotas]
    patrimonio_bruto = [total_cotas * cotas_brutas[0]]

    for i in range(1, meses_acc + 1):
        total_cotas += aporte / cotas_brutas[i]
        cotas_acumuladas.append(total_cotas)
        patrimonio_bruto.append(total_cotas * cotas_brutas[i])

    cotas_resgate = []
    for m in range(matriz_liq.shape[0]):
        cotas_necessarias = resgate_mensal / matriz_liq[m, meses_acc + m]
        total_cotas -= cotas_necessarias
        cotas_resgate.append(cotas_necessarias)
        patrimonio_bruto.append(total_cotas * cotas_brutas[meses_acc + m])

    return patrimonio_bruto, cotas_resgate

def bissecao(tipo_objetivo: str, outro_valor: float, poupanca_inicial: float, meses_acc: int,
             taxa_mensal: float, cotas_brutas: np.ndarray, matriz_liq: np.ndarray, resgate_mensal: float,
             tolerancia: float = 0.01, max_iter: int = 100):

    if tipo_objetivo == "manter":
        valor_final_desejado = poupanca_inicial * (1 + taxa_mensal) ** (meses_acc + matriz_liq.shape[0])
    elif tipo_objetivo == "zerar":
        valor_final_desejado = 0
    elif tipo_objetivo == "outro valor":
        if outro_valor is None or outro_valor < 0:
            raise ValueError("Você deve informar o valor final desejado ao escolher 'outro valor'.")
        valor_final_desejado = outro_valor
    else:
        raise ValueError("Tipo de objetivo inválido.")

    a, b = 0, 1_000_000
    for _ in range(max_iter):
        m = (a + b) / 2
        patrimonio_final, _ = calcular_aporte(
            m, poupanca_inicial, meses_acc, taxa_mensal, cotas_brutas, matriz_liq, resgate_mensal
        )
        diferenca = patrimonio_final[-1] - valor_final_desejado
        if abs(diferenca) < tolerancia:
            return m
        if diferenca > 0:
            b = m
        else:
            a = m

    raise ValueError("Não foi possível encontrar um aporte adequado dentro da precisão estabelecida.")
