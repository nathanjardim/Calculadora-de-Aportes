# Converte taxa anual para taxa mensal equivalente
def taxa_mensal(taxa_anual):
    return (1 + taxa_anual) ** (1 / 12) - 1

def calcular_ir_regressivo(meses_aporte):
    if meses_aporte <= 24:
        return 0.35
    elif meses_aporte <= 48:
        return 0.30
    elif meses_aporte <= 72:
        return 0.25
    elif meses_aporte <= 96:
        return 0.20
    elif meses_aporte <= 120:
        return 0.15
    else:
        return 0.10

def calcular_ir_progressivo(valor_mensal):
    if valor_mensal <= 2112:
        return 0.0
    elif valor_mensal <= 2826.65:
        return 0.075
    elif valor_mensal <= 3751.05:
        return 0.15
    elif valor_mensal <= 4664.68:
        return 0.225
    else:
        return 0.275

def simular_aposentadoria_com_regime(
    idade_atual,
    idade_aposentadoria,
    expectativa_vida,
    poupanca_inicial,
    aporte_mensal,
    renda_liquida_desejada,
    rentabilidade_anual,
    regime="regressivo"
):
    meses_total = (expectativa_vida - idade_atual) * 12
    meses_aporte = (idade_aposentadoria - idade_atual) * 12

    saldo = poupanca_inicial
    rentab_mensal = taxa_mensal(rentabilidade_anual)
    patrimonio_aposentadoria = None
    historico = []
    aportes = []

    for mes in range(meses_total):
        saldo *= (1 + rentab_mensal)

        if mes < meses_aporte:
            saldo += aporte_mensal
            aportes.append({"mes": mes, "valor": aporte_mensal})
        else:
            if regime == "regressivo":
                total_saque = 0
                montante_necessario = renda_liquida_desejada / (1 - 0.10)
                saldo_remanescente = montante_necessario
                for a in aportes:
                    tempo_meses = mes - a["mes"]
                    ir = calcular_ir_regressivo(tempo_meses)
                    valor_corrigido = a["valor"] * (1 + rentab_mensal) ** (mes - a["mes"])
                    parte = min(saldo_remanescente, valor_corrigido)
                    saque_liquido = parte * (1 - ir)
                    saldo -= parte
                    saldo_remanescente -= parte
                    total_saque += saque_liquido
                    if saldo_remanescente <= 0:
                        break
                if total_saque < renda_liquida_desejada:
                    saldo -= (renda_liquida_desejada - total_saque) / (1 - 0.10)
            elif regime == "progressivo":
                ir = calcular_ir_progressivo(renda_liquida_desejada)
                saque_bruto = renda_liquida_desejada / (1 - ir)
                saldo -= saque_bruto

        historico.append(saldo)

        if mes == meses_aporte - 1:
            patrimonio_aposentadoria = saldo

    return saldo, patrimonio_aposentadoria, historico

def determinar_alvo(modo, patrimonio_aposentadoria, valor_final_desejado):
    if modo == "zerar":
        return 0
    elif modo == "manter":
        return patrimonio_aposentadoria
    elif modo == "atingir":
        return valor_final_desejado or 0
    else:
        raise ValueError("Modo inválido.")

def calcular_aporte(
    idade_atual,
    idade_aposentadoria,
    expectativa_vida,
    poupanca_inicial,
    renda_mensal,
    taxa_juros_real,
    inflacao,
    modo,
    valor_final_desejado=None,
    renda_atual=None,
    percentual_de_renda=None,
    max_aporte=100_000
):
    rentabilidade_anual = (1 + taxa_juros_real) * (1 + inflacao) - 1

    def buscar_aporte(regime):
        min_aporte = 0
        tolerancia = 1
        max_iteracoes = 100
        iteracoes = 0
        max_aporte_local = max_aporte

        while max_aporte_local - min_aporte > tolerancia and iteracoes < max_iteracoes:
            iteracoes += 1
            teste = (min_aporte + max_aporte_local) / 2

            saldo_final, patrimonio_aposentadoria, _ = simular_aposentadoria_com_regime(
                idade_atual,
                idade_aposentadoria,
                expectativa_vida,
                poupanca_inicial,
                teste,
                renda_mensal,
                rentabilidade_anual,
                regime
            )

            alvo = determinar_alvo(modo, patrimonio_aposentadoria, valor_final_desejado)

            if saldo_final > alvo:
                max_aporte_local = teste
            else:
                min_aporte = teste

        saldo_final, patrimonio_aposentadoria, _ = simular_aposentadoria_com_regime(
            idade_atual,
            idade_aposentadoria,
            expectativa_vida,
            poupanca_inicial,
            max_aporte_local,
            renda_mensal,
            rentabilidade_anual,
            regime
        )
        alvo = determinar_alvo(modo, patrimonio_aposentadoria, valor_final_desejado)

        if saldo_final < alvo - tolerancia:
            return None

        return round((min_aporte + max_aporte_local) / 2, 2)

    aporte_prog = buscar_aporte("progressivo")
    aporte_regr = buscar_aporte("regressivo")

    if aporte_prog is None and aporte_regr is None:
        return {"aporte_mensal": None}

    if aporte_prog is None:
        return {"aporte_mensal": aporte_regr, "regime": "Regressivo"}
    if aporte_regr is None:
        return {"aporte_mensal": aporte_prog, "regime": "Progressivo"}

    if aporte_prog < aporte_regr:
        return {"aporte_mensal": aporte_prog, "regime": "Progressivo"}
    else:
        return {"aporte_mensal": aporte_regr, "regime": "Regressivo"}
