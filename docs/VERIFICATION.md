# Evidências de verificação — 06/10/2026

Implementação local concluída; nenhuma publicação, corretora ou serviço contratado.

## Ambiente
Python 3.12.14; NumPy 2.5.3, Pandas 2.3.3, Streamlit 1.65.0, Plotly 6.9.0, pytest 9.1.1, pyarrow 23.0.1. Compatibilidade verificada pela instalação e execução; dependências transitivas em requirements-lock.txt.

## Testes
Comando: `.venv\Scripts\python.exe -m pytest -q`.
Suíte cobre valores manuais de SMA/EMA/RSI Wilder/Bollinger/MACD, warm-up, ausência, roundtrip CSV/Parquet, rejeição de dados inválidos/diários, execução seguinte com contabilidade manual e custos, limite de capital, liquidação com taxas, sinais sem carregamento overnight, causalidade por perturbação e truncamento futuro, cruzamentos exatos, métricas conhecidas, execução do pipeline e AppTest do dashboard com clique em executar.
Resultado final: **23 passed in 4.63s**. Saída final em docs/test-results.txt.

## Aplicação
Servidor iniciado com `--server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false`.
GET http://127.0.0.1:8501/_stcore/health respondeu HTTP 200 e `ok`.
AppTest renderizou componentes e gerou execução sem exceções. A ferramenta de navegador integrado não iniciou devido a `CreateProcessWithLogonW failed: 1056`; aparência visual no navegador não inspecionada. Servidor fica disponível enquanto seu processo estiver ativo; README permite reiniciá-lo.

## Pesquisa
Dados sintéticos: 540 barras de 5 minutos, 15 sessões artificiais e semente 42. Datas e horários não representam calendário oficial, inclusive podem coincidir com feriados reais. Divisão 288/144/108 barras (8/4/3 sessões), fronteiras registradas antes dos resultados.
Execução CLI final: runs/20261006T235127Z_5e766240. Resultados reproduzíveis e snapshots em runs/. Arquivo summary.csv apresenta hipóteses EMA/RSI e baselines por partição; ledger reconcilia P&L realizado/não realizado, caixa e patrimônio. Não houve seleção de vencedor nem ajuste de parâmetros.

## Pendências de escopo futuro
Histórico intraday real adequado e configuração de sessões com fonte verificável; avaliação empírica fora da amostra com dados suficientes; execução/impacto e eventos corporativos mais realistas. Black-Scholes, machine learning e NautilusTrader foram explicitamente adiados. Não há evidência de rentabilidade de mercado.
