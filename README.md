
# Documentação Técnica Detalhada - Wealth Planning

## Estrutura dos Arquivos

```
.
├── core.py            # Módulo de lógica da simulação
├── streamlit_app.py   # Interface do app (frontend)
├── requirements.txt   # Dependências
```

---

## core.py — Módulo de Lógica

Funções puras, sem dependência do Streamlit. Essencial para testes unitários e reuso em outras interfaces (API, desktop, etc.).

### Blocos:

### taxa_mensal(taxa_anual)
Converte taxa de juros anual em mensal composta:
```python
return (1 + taxa_anual) ** (1 / 12) - 1
```

### simular_aposentadoria(...)
Simula mês a mês o saldo do investidor, com:
- Acúmulo de aportes até a aposentadoria
- Resgates líquidos após a aposentadoria

Retorna:
- saldo_final: saldo ao fim da vida
- patrimonio_no_aposentadoria: montante acumulado no mês da aposentadoria
- historico: vetor com o saldo mês a mês

### determinar_alvo(...)
Interpreta o modo de objetivo:
- "manter" → manter o patrimônio acumulado
- "zerar" → consumir tudo até o final
- "atingir" → alcançar um valor final específico

### calcular_aporte(...)
Função principal que usa o método da bisseção:
1. Estima um aporte inicial (min_aporte, max_aporte)
2. Chama simular_aposentadoria() a cada iteração
3. Compara o resultado com o alvo
4. Ajusta os limites até convergir

Retorna o menor aporte possível para atingir o objetivo definido.

---

## streamlit_app.py — Interface em Streamlit

Define a experiência visual, coleta inputs, chama core.py, exibe resultados e exporta.

### Blocos:

### 1. Senha de Acesso
Impede acesso ao app sem senha. Senha atual: sow123.

### 2. verificar_alertas(...) — Validações de Input
Retorna três listas:
- erros → impedem a simulação
- alertas → sinalizam riscos ou inconsistências
- informativos → mensagens auxiliares ao usuário

### 3. Inputs do Formulário
Organizado em 4 blocos:
- Dados Iniciais
- Dados Econômicos
- Aposentadoria
- Objetivo Final

### 4. Cálculo e Execução
Chama calcular_aporte() do core.py, depois simular_aposentadoria() e calcula:
- aporte_int
- patrimonio_final
- anos_aporte
- percentual da renda

### 5. Exibição dos Resultados
KPIs: aporte, poupança necessária, tempo, percentual da renda

### 6. Gráfico de Patrimônio
Altair: gráfico idade × patrimônio, com tooltip

### 7. Exportação para Excel
Função gerar_excel() escreve:
- KPIs
- Curva do patrimônio
- Formatação via xlsxwriter

---

## Onde mexer para Manutenção

- Novos modos de simulação → editar determinar_alvo() e calcular_aporte()
- Novas regras de validação → editar verificar_alertas()
- Novos campos no formulário → streamlit_app.py (bloco with st.form())
- Otimização de performance → revisar simular_aposentadoria()

