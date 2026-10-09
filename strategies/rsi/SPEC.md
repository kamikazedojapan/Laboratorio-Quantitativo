# Hipótese B — RSI Wilder 14

Especificação congelada antes da primeira execução. Adaptação própria, não comprovada pelo PDF.
Compra quando RSI[t-1] <= 30 e RSI[t] > 30; venda quando RSI[t-1] <= 70 e RSI[t] > 70. Ambos cruzamentos ascendentes. Somente comprado; sinais repetidos enquanto posicionado não aumentam posição.
Wilder 14: médias iniciais de ganhos/perdas sobre 14 diferenças (15 fechamentos), recursão alpha=1/14. Primeiro cruzamento possível no 16º fechamento. Série plana retorna 50; apenas ganhos 100; apenas perdas 0.
Aplicam-se exatamente sizing, execução na próxima abertura, sessão artificial e liquidação programada, custos, baseline, partições cronológicas e critérios de avaliação descritos em ../ema/SPEC.md e configs/demo.json. RSI carrega histórico entre sessões da mesma partição; não atravessa fronteiras de partição. Nenhuma otimização, stop ou alvo adicional.
Entrada acima de 30 aparece como exemplo ilustrativo para WIN na página 24 do PDF; esta versão usa ativo à vista sintético, sem futuros, e adiciona saída acima de 70 e demais regras por decisão própria.
