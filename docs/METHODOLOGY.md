# Convenções e limites

## Dados e sessões
Na demonstração do dashboard, o controle “Número de sessões sintéticas” começa em
60 (mínimo 3). O calendário artificial começa na primeira data de configs/demo.json
e inclui segunda a sexta, sem ajuste de feriados. Desenvolvimento recebe
max(1, floor(8N/15)) sessões; validação max(1, floor(4N/15)); teste final recebe o
restante. Para N=60: 32/16/12 e 2.160 barras de cinco minutos. A configuração
histórica de 15 sessões e seus arquivos de dados permanecem disponíveis para
reprodução. O gerador conserva seed e fórmula: cada tamanho é determinístico, mas
alterar N pode alterar Open/High/Low/Volume do prefixo, pois muda o consumo do RNG.
Não se apresenta a nova série como concatenação byte a byte da anterior.
Os custos efetivos são preservados em config e execution_costs no manifesto;
summary.csv contém taxas, slippage e custo total por estratégia/partição.

Timestamp indica **abertura** da barra; Close só fica conhecido ao fim dessa barra. Exige offset/timezone explícito e converte ao timezone configurado. Um ativo por execução, preços positivos/finite, volume não negativo, OHLC consistente, ordem estrita e sem duplicatas. Não preenche, reordena ou remove observações silenciosamente.
CSV e Parquet exigem timestamp, asset, Open, High, Low, Close, Volume. Calendário explícito deve coincidir exatamente com dias presentes, e cada dia deve conter a grade completa. Esta política rejeita pregões incompletos, barras faltantes e interrupções; calendários especiais precisam ser pré-processados e não são suportados em uma mesma configuração. Não há validação automática de calendário da bolsa. Na importação real, usuário deve informar fonte, horários e calendário verificados para o ativo e período. Não há suporte a futuros, multiplicadores, desdobramentos, proventos ou moedas múltiplas.

## Indicadores
Todos usam fechamento, janelas passadas e float64. SMA exige n pontos. EMA exige n pontos consecutivos, seed=SMA(n), depois alpha=2/(n+1). NaN/infinito reinicia suavizadores; entrada do backtest rejeita ambos. RSI usa n diferenças, seed das médias simples de ganhos/perdas e Wilder alpha=1/n. Sem perdas e com ganhos retorna 100; sem ganhos e com perdas 0; ambos zero retorna 50. Warm-up mantém NaN, sem sinais. SMA/Bollinger exigem janela completa após ausência. Bollinger usa desvio populacional ddof=0, n=20 e k=2. MACD12/26: primeira linha no 26º ponto; sinal EMA9 no 34º. SMA/EMA/bandas/MACD têm unidade do preço; RSI é adimensional entre 0–100. Indicadores não são reiniciados por sessão (incluem variação overnight), mas são reiniciados por partição.

## Execução e contabilidade
Sinal conhecido ao fim de t executa Open[t+1], com slippage adverso. Pressupõe ordem sem latência disponível nessa abertura; preço OHLC não garante fill real. Ordens não atravessam sessões. Liquidação no horário fixo configurado é programada previamente e independe de preços futuros. Tem prioridade sobre sinais; entradas são proibidas nesse horário ou depois. Não se liquida retroativamente usando a última barra encontrada. Conjunto incompleto é rejeitado antes do backtest público (pipeline).
Capital e P&L em unidades monetárias dos preços; sem alavancagem. Quantidade arredondada para baixo pelo lote, considerando taxas e preço com slippage. Sem piramidação. Taxa fixa e proporcional cobrada em toda compra e venda, inclusive liquidação. Slippage integra preço de execução; relatório o exibe separadamente sem segundo débito. Base de custo inclui taxa de entrada. Realizado usa saída líquida menos base; não realizado usa quantidade × fechamento menos base (não estima futura taxa de saída). Caixa + posição marcada = patrimônio; patrimônio−capital = realizado+não realizado. Ledger registra posições abertas mesmo em prefixos de sessão.

## Métricas e pesquisa
Retorno líquido = patrimônio final/capital−1. Drawdown relativo ao pico acumulado incluindo capital inicial. Operação significa par compra/venda concluído; win rate inclui empates no denominador. Ganho e perda médios condicionais; perda é negativa. Expectancy é média do P&L líquido por operação. Profit factor = ganhos totais / módulo das perdas; sem perdas retorna não estimável (não infinito). Sem operações, métricas por operação são não estimáveis. Exposição é média aritmética da posição marcada/patrimônio por barra; tempo posicionado é fração de barras após execução. Turnover é soma dos notionals executados/capital inicial, contando ambos lados. São aproximações discretas, sem ponderação por horas fora da sessão.
Caixa sem remuneração tem retorno zero; baseline session_hold compra primeira abertura e vende no horário de liquidação, mesmos custos/sizing. Esta regra de calendário é pré-programada e não depende de sinal. Não é benchmark de compra e manutenção overnight.
Partições por dias completos e fronteiras externas registradas antes do cálculo. Caixa e indicadores reiniciam em cada partição. A amostra mínima técnica de 35 barras por partição não demonstra suficiência estatística. Todas as conclusões desta versão são exploratórias, com evidência insuficiente e sem ranking de vencedor. Não estima Sharpe ou retorno anualizados. Teste final é executado com regras já fixadas; novas pesquisas precisam reservar novo teste final se usarem os resultados para decisões.

## Rastreabilidade
Cada execução cria diretório único, configuração completa, fronteiras, versões instaladas, SHA256 da representação CSV canônica e SHA256 do código do pacote, snapshot dos dados, sinais, indicadores, ordens, operações e ledger. O hash identifica conteúdo normalizado, não bytes do arquivo original. Registros anteriores não são sobrescritos. Filtros do dashboard apenas exibem registros; executar novamente cria novo ID. Diretórios com apenas manifesto são tentativas incompletas. Não existe mecanismo de proteção contra edição manual de registros no disco.
