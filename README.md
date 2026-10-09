# Laboratório Quantitativo 🧪

Laboratório educacional em Python e Streamlit para explorar indicadores técnicos, simular estratégias EMA/RSI e comparar resultados com benchmarks. Inclui evolução do patrimônio, importação de dados e registros das execuções com configurações, resultados e hashes.

**Os dados sintéticos demonstram o funcionamento do software. Não constituem evidência de rentabilidade ou eficácia no mercado.** O projeto não conecta corretoras nem envia ordens reais.

## Funcionalidades

- Indicadores SMA, EMA, RSI de Wilder, Bandas de Bollinger e MACD.
- Simulações intraday de estratégias EMA/RSI, somente com posições compradas.
- Comparação com caixa sem remuneração e manutenção de posição por sessão.
- Custos por ordem e slippage adverso incorporados à simulação.
- Importação de CSV ou Parquet, acompanhados de configuração JSON.
- Histórico de execuções com dados, resultados, manifesto e cópia do código utilizado.
- Módulo isolado de Black-Scholes, sem integração ao motor intraday.

## Instalação no Windows

Requer Python 3.11 ou superior. No PowerShell, na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
```

O arquivo `requirements-lock.txt` registra versões do ambiente de desenvolvimento. Para tentar reproduzir esse ambiente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
```

A compatibilidade das versões fixadas deve ser conferida no ambiente de destino.

## Executar o dashboard

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abra o endereço local informado pelo Streamlit.

## Demonstração sintética

O dashboard inicia com **60 sessões**, ajustáveis na barra lateral, com mínimo de três.

| Parâmetro | Configuração inicial |
|---|---|
| Calendário | Segunda a sexta, de 01/09/2026 a 23/11/2026, sem tratamento de feriados |
| Partições | 32 sessões de desenvolvimento, 16 de validação e 12 de teste final |
| Dados | 2.160 candles de cinco minutos; 36 por sessão |
| Sessão artificial | 09:00–12:00; liquidação às 11:50 |
| Seed | 42 |
| Capital inicial | 10.000 unidades monetárias por partição |
| Alocação e lote | 95%; lote de uma unidade |
| Taxas por ordem | 5 pontos-base sobre o valor negociado + 0,5 unidade monetária |
| Slippage | 2 pontos-base adversos, incorporados ao preço de execução |

O calendário e os horários são artificiais. Cada partição reinicia o capital e o aquecimento dos indicadores.

A configuração histórica `configs/demo.json` e os arquivos `data/demo_intraday.csv` e `data/demo_intraday.parquet` preservam **15 sessões**. O dashboard deriva sua configuração sintética separadamente.

## Execuções e reprodução

Uma execução sintética de referência está incluída em:

`runs/20261009T035723Z_37aafd9d/`

Ela contém o manifesto, os dados utilizados, resultados por estratégia e partição, resumo e cópia do código com hashes. Os demais históricos e pacotes locais de auditoria não fazem parte desta distribuição.

Para executar a demonstração histórica pela linha de comando:

```powershell
.\.venv\Scripts\python.exe -m trading_lab.cli --config configs/demo.json
```

Esse comando utiliza a configuração histórica de 15 sessões. Para gerar a demonstração de 60 sessões, utilize o dashboard.

Os identificadores de novas execuções mudam. Comparações de reprodução devem considerar dados, configurações, código, dependências e resultados, e não apenas o nome da pasta.

## Dados próprios

Forneça CSV ou Parquet com as colunas:

`timestamp`, `asset`, `Open`, `High`, `Low`, `Close`, `Volume`.

O timestamp deve conter o deslocamento de fuso, por exemplo: `2026-09-01T09:00:00-03:00`.

Adapte `configs/demo.json` para informar procedência, tipo de dados, calendário, horários, custos e fronteiras das partições. Dados diários são rejeitados pelo motor intraday.

```powershell
.\.venv\Scripts\python.exe -m trading_lab.cli --config configs/meu_estudo.json --data data/meus_dados.parquet
```

Não publique dados de terceiros sem verificar as condições de uso e redistribuição.

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

A implementação das 60 sessões foi acompanhada por um relato de 176 testes aprovados e reexecução de 13 testes afetados. Esses números descrevem aquela execução local; não substituem a execução dos testes na versão baixada.

## Organização

- `app.py`: entrada do dashboard.
- `src/trading_lab/`: indicadores, dados, simulações, métricas e interface.
- `strategies/`: especificações das estratégias e do módulo Black-Scholes.
- `configs/` e `data/`: configuração e dados da demonstração histórica.
- `tests/`: testes automatizados.
- `docs/`: metodologia, referências e registros técnicos históricos.
- `runs/`: execução sintética de referência.
- `reports/acompanhamento/20261007-retomada/method_coverage.csv`: tabela histórica de cobertura exibida no dashboard.

Documentos históricos podem mencionar evidências preservadas somente no ambiente local.

## Limitações

O modelo não contempla liquidez, fila de execução, impacto de mercado, leilões, impostos ou eventos corporativos. O slippage é fixo. Não há otimização nem seleção automática de uma estratégia vencedora.

A partição chamada “teste final” integra uma demonstração sintética já observada; não representa validação independente em dados reais.

Este projeto tem finalidade educacional e não fornece recomendação de investimento.