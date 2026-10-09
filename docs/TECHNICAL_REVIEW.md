# Correções da revisão técnica — 06/10/2026 (America/Bahia)

Nova execução: **20261007T002250Z_66bfdcc1**. O ID usa UTC (07/10); a execução ocorreu em 06/10 às 21:22 no horário America/Bahia.

## Alterações
1. Benchmark caixa preenche custos (taxas, slippage e total), exposição, tempo posicionado, turnover, P&L realizado/não realizado, quantidade e valor de posição com zero. Métricas por operação sem operações continuam ausentes/não estimáveis; anualização também permanece não estimável.
2. Colunas de métricas são numéricas, inclusive quando inteiramente ausentes. O dashboard usa Pandas Styler para percentuais, unidades monetárias e texto de valores ausentes apenas na apresentação. Nenhuma string é inserida nas colunas numéricas ou exportada no CSV. O aviso ArrowInvalid desapareceu sem ocultação de logs.
3. O registro selecionado ganhou gráfico de preços, SMA/EMA/Bollinger, RSI, MACD e sinais persistidos, com compras/vendas efetivamente executadas ao preço com slippage. Quantidade, motivo e taxa aparecem no hover das execuções, inclusive encerramento de sessão. Os sinais são círculos; execuções são triângulos. Timestamp identifica a abertura da barra; o sinal associado à barra só é conhecido no fechamento.
4. O gráfico lê exclusivamente data.csv, manifesto e CSVs de indicadores, sinais e ordens do registro selecionado. Nenhum indicador é recalculado nesse gráfico. Novos indicadores/sinais incluem timestamp. Registros antigos, sem essa coluna, continuam legíveis por alinhamento de barras conferido contra o ledger e as fronteiras do manifesto. Inconsistências geram erro explícito.

## Verificação
- Suíte completa: **38 passed in 6.98s**, saída integral em pytest-review-full-output.txt; nenhum ArrowInvalid ou fallback automático de conversão de tabelas. O aviso de contexto do Streamlit em AppTest permanece visível no log.
- 15 casos adicionais verificam caixa completo, roundtrip CSV numérico, formatação sem mutação, séries e ordens das nove combinações de partição/estratégia, leitura de valores persistidos sem recálculo, suporte a formato legado, rejeição de timestamps desalinhados, ausência de ordens e integração com dados atuais diferentes.
- Nova execução usa exatamente configs/demo.json e o snapshot da execução 20261006T235127Z_5e766240. Log CLI em review-execution-output.txt.
- SHA256 dos 349 arquivos monitorados antes da revisão confirmou preservação de registros anteriores, configurações, especificações, indicadores, estratégias e motor de backtest. Evidência em preservation-audit.json.
- Nenhuma estratégia, parâmetro, regra de sizing, custo, sessão ou divisão cronológica foi alterada. Não houve otimização. Registros antigos mantêm seus resultados originais, inclusive campos incompletos do benchmark caixa; a correção aparece nas novas execuções.

## Entrega
ZIP contém o pacote instalável src/trading_lab, testes, configuração, documentação, logs, dados e todos os registros locais (incluindo o novo ID acima). Exclui .venv, .git, caches, temporários e ZIPs anteriores. PACKAGE_MANIFEST.json registra hashes dos arquivos, ID da execução e resultado do pytest.

Os arquivos avulsos fornecidos no Desktop foram consultados como referência; o código corrigido entregue está no pacote src/trading_lab do projeto/ZIP. Dados permanecem sintéticos, com evidência insuficiente de eficácia de mercado.
