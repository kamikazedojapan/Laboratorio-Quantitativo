# Hipótese A — EMA 9/21

Especificação congelada antes da primeira execução. Adaptação própria, não comprovada pelo PDF.
Sinal ao fechamento t: EMA9[t] > EMA21[t] e EMA9[t-1] <= EMA21[t-1] compra; desigualdades inversas vendem. Sem sinal quando qualquer valor necessário é ausente.
EMA inicializada pela média simples de n fechamentos, alpha=2/(n+1). Primeiro cruzamento elegível após 22 barras. Indicadores carregam histórico entre sessões dentro da partição, sem carregar entre partições.
Somente comprado, um ativo à vista, uma posição, sem piramidação. Quantidade inteira em múltiplos do lote configurado; orçamento de 95% do caixa por entrada, incluindo taxa fixa/proporcional, com slippage no preço. Capital inicial 10.000 unidades monetárias na demonstração.
Ordens de sinais executam na abertura seguinte, apenas na mesma sessão e antes do horário de liquidação. Sinais na última barra não geram ordens no dia seguinte.
Liquidação programada na abertura 11:50, sessão artificial 09:00–12:00, barras de 5 minutos (timestamp indica abertura). Horários, calendário e procedência constam em configs/demo.json; dados reais exigem configuração própria. Não há stop ou alvo adicional.
Custos em todas as execuções: 5 bps + 0,50 por ordem; slippage adverso 2 bps, configuráveis. Não inclui impostos, impacto ou fila.
Baselines: caixa sem remuneração e compra na primeira abertura de cada sessão, venda na abertura de liquidação, mesmos custos/sizing. Não é buy-and-hold overnight.
Avaliação: retorno líquido, drawdown, operações fechadas, win rate, ganho/perda médios, expectancy, profit factor, exposição, turnover e custos. Sem anualização. Fronteiras fixadas em configs/demo.json antes dos resultados: desenvolvimento até 10/09/2026, validação até 16/09/2026, restante teste final. Cada partição começa com caixa e warm-up independentes.
Nenhuma otimização ou escolha de vencedor. Demonstração sintética sempre significa evidência insuficiente para eficácia de mercado. Amostras reais pequenas também; a versão inicial não implementa inferência estatística.
