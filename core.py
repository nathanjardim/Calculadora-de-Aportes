from typing import Callable, Optional, Tuple, List

# ==== UTILITÁRIOS ====

def taxa_mensal(taxa_anual: float) -> float:
    """Converte uma taxa anual para taxa mensal equivalente."""
    return (1 + taxa_anual) ** (1 / 12) - 1

# ==== IMPOSTO DE RENDA ====

def ir_progressivo(valor: float) -> float:
    """IR pela tabela progressiva mensal (2024), com proteção contra valores negativos."""
    if valor <= 2112:
        return 0
    elif valor <= 2826.65:
        return max(valor * 0.075 - 158.4, 0)
    elif valor <= 3751.05:
        return max(valor * 0.15 - 370.4, 0)
    elif valor <= 4664.68:
        return max(valor * 0.225 - 651.73, 0)
    else:
        return max(valor * 0.275 - 884.96, 0)

def ir_regressivo(valor: float, mes: int, anos_aporte: int = 35) -> float:
    """IR regressivo com base no tempo médio de cada aporte."""
    anos_de_saque = mes / 12
    tempo_medio = anos_aporte - anos_de_saque

    if tempo_medio >= 10:
        aliquota = 0.10
    elif tempo_medio <= 0:
        aliquota = 0.35
    else:
        aliquota = 0.35 - ((tempo_medio / 10) * 0.25)

    aliquota = max(min(aliquota, 0.35), 0.10)
    return valor * aliquota

# ==== SIMULAÇÃO DE PATRIMÔNIO ====

def simular_aposentadoria(
    idade_atual: int,
    idade_aposentadoria: int,
    expectativa_vida: int,
    poupanca_inicial: float,
    aporte_mensal: float,
    renda_mensal: float,
    rentabilidade_anual: float,
    funcao_imposto: Callable[[float, int, int], float]
) -> Tuple[float, float, List[float], float]:
    """Simula a evolução do patrimônio mês a mês até o fim da vida."""
    meses_total = (expectativa_vida - idade_atual) * 12
    meses_aporte = (idade_aposentadoria - idade_atual) * 12
    anos_aporte = idade_aposentadoria - idade_atual

    saldo = poupanca_inicial
    rentab_mensal = taxa_mensal(rentabilidade_anual)
    patrimonio_no_aposentadoria = None
    historico = []
    total_ir_pago = 0

    for mes in range(meses_total):
        saldo *= (1 + rentab_mensal)

        if mes < meses_aporte:
            saldo += aporte_mensal
        else:
            saque_liquido = renda_mensal
            saque_bruto_estimado = saque_liquido / 0.85
            ir = funcao_imposto(saque_bruto_estimado, mes - meses_aporte, anos_aporte)
            saque_bruto = saque_liquido + ir
            saldo -= saque_bruto
            total_ir_pago += ir

        historico.append(saldo)

        if mes == meses_aporte - 1:
            patrimonio_no_aposentadoria = saldo

    return saldo, patrimonio_no_aposentadoria, historico, total_ir_pago

# ==== OBJETIVO FINAL ====

def determinar_alvo(
    modo: str,
    patrimonio_aposentadoria: float,
    valor_final_desejado: Optional[float]
) -> float:
    """Determina o valor alvo no final da simulação."""
    if modo == "zerar":
        return 0
    elif modo == "manter":
        return patrimonio_aposentadoria
    elif modo == "atingir":
        return valor_final_desejado or 0
    else:
        raise ValueError("Modo inválido. Use 'zerar', 'manter' ou 'atingir'.")

# ==== BISSERÇÃO DO APORTE ====

def calcular_aporte_com_ir(
    idade_atual: int,
    idade_aposentadoria: int,
    expectativa_vida: int,
    poupanca_inicial: float,
    renda_mensal: float,
    rentabilidade_anual: float,
    modo: str,
    funcao_imposto: Callable[[float, int, int], float],
    valor_final_desejado: Optional[float] = None,
    max_aporte: float = 100_000
) -> Tuple[Optional[float], Optional[float]]:
    """Aplica bisseção para encontrar o menor aporte mensal necessário com IR aplicado."""
    min_aporte = 0
    tolerancia = 1
    max_iteracoes = 100
    iteracoes = 0

    while max_aporte - min_aporte > tolerancia and iteracoes < max_iteracoes:
        iteracoes += 1
        aporte_teste = (min_aporte + max_aporte) / 2

        saldo_final, patrimonio_aposentadoria, _, _ = simular_aposentadoria(
            idade_atual, idade_aposentadoria, expectativa_vida,
            poupanca_inicial, aporte_teste, renda_mensal, rentabilidade_anual, funcao_imposto
        )

        alvo = determinar_alvo(modo, patrimonio_aposentadoria, valor_final_desejado)

        if saldo_final > alvo:
            max_aporte = aporte_teste
        else:
            min_aporte = aporte_teste

    aporte_final = round((min_aporte + max_aporte) / 2, 2)
    saldo_final, patrimonio_aposentadoria, _, _ = simular_aposentadoria(
        idade_atual, idade_aposentadoria, expectativa_vida,
        poupanca_inicial, aporte_final, renda_mensal, rentabilidade_anual, funcao_imposto
    )
    alvo = determinar_alvo(modo, patrimonio_aposentadoria, valor_final_desejado)

    if saldo_final < alvo - tolerancia:
        return None, None

    _, _, _, total_ir = simular_aposentadoria(
        idade_atual, idade_aposentadoria, expectativa_vida,
        poupanca_inicial, aporte_final, renda_mensal, rentabilidade_anual, funcao_imposto
    )
    return aporte_final, total_ir

# ==== COMPARAÇÃO ENTRE REGIMES ====

def selecionar_melhor_regime(
    prog: Optional[Tuple[float, float]],
    regr: Optional[Tuple[float, float]]
) -> dict:
    """Compara os dois regimes e retorna o mais vantajoso."""
    if prog is None and regr is None:
        return {"aporte_mensal": None}
    if prog is None:
        return {"aporte_mensal": regr[0], "regime": "regressivo"}
    if regr is None:
        return {"aporte_mensal": prog[0], "regime": "progressivo"}
    return {"aporte_mensal": prog[0], "regime": "progressivo"} if prog[0] < regr[0] else {"aporte_mensal": regr[0], "regime": "regressivo"}

# ==== FUNÇÃO PRINCIPAL ====

def calcular_aporte(
    idade_atual: int,
    idade_aposentadoria: int,
    expectativa_vida: int,
    poupanca_inicial: float,
    renda_mensal: float,
    rentabilidade_anual: float,
    imposto=None,  # mantido por compatibilidade
    modo: str = "manter",
    valor_final_desejado: Optional[float] = None,
    renda_atual: Optional[float] = None,
    percentual_de_renda: Optional[float] = None,
    max_aporte: float = 100_000
) -> dict:
    """Calcula o aporte ideal comparando regimes progressivo e regressivo de IR."""
    resultado_prog = calcular_aporte_com_ir(
        idade_atual, idade_aposentadoria, expectativa_vida,
        poupanca_inicial, renda_mensal, rentabilidade_anual,
        modo, lambda v, m, a: ir_progressivo(v),
        valor_final_desejado, max_aporte
    )

    resultado_regr = calcular_aporte_com_ir(
        idade_atual, idade_aposentadoria, expectativa_vida,
        poupanca_inicial, renda_mensal, rentabilidade_anual,
        modo, ir_regressivo,
        valor_final_desejado, max_aporte
    )

    return selecionar_melhor_regime(resultado_prog, resultado_regr)
