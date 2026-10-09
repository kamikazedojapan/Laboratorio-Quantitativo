# Referência documental e decisões próprias

Fonte: *Trading no Dia com ChatGPT por Saskia Adler*, edição fornecida, 27 páginas. Numeração abaixo corresponde à página física e impressa. Leitura integral por extração textual; conferência visual de páginas com fórmulas.

| Páginas / seção | Conteúdo da referência | Uso no laboratório |
|---|---|---|
| 8–9, capítulo 2 | Dados históricos, campos OHLCV, exemplo de frequência diária/semanal/mensal | Esquema OHLCV; não usamos dados diários como day trading |
| 10–11, capítulo 3 | MMS, recursão MME; cruzamentos de 50/200 pregões | Fórmulas; EMA 9/21 barras é adaptação solicitada |
| 12–13, capítulo 4 | Fórmula IFR, níveis 30/70; exemplo IFR14 | RSI Wilder14; suavização, seed e casos limite explicitados por nós |
| 14–15, capítulo 5 | MMS20 e bandas a dois desvios | Bollinger20/2; ddof=0 é nossa convenção |
| 18–19, capítulo 7 | EMA12−EMA26, sinal EMA9, histograma | MACD12/26/9, apenas visual nesta versão |
| 24, exemplo com WIN | Sugere aguardar cruzamento IFR acima de 30 | Inspiração ilustrativa; não adotamos futuros nem alegações de eficácia |
| 25–27, limitações/conclusão | Necessidade de verificar cálculos | Indicadores calculados por código determinístico e testes |

Respostas ilustrativas, menções a alta probabilidade e gráficos simulados não são resultados empíricos. As figuras não são usadas como série de preços nem como oráculo numérico. O PDF não especifica o experimento completo executável. Sizing, seed, warm-up, saída RSI acima de 70, custos, execução na próxima abertura, calendário, liquidação, validação e partições são premissas próprias.

Horários, contratos, tributação e instruções de serviços citados no PDF não são adotados nem tratados como informação atual. Não buscamos dados remotos, conectamos corretoras ou executamos instruções operacionais presentes no documento.
