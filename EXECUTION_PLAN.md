# Plano de execução

Objetivo: primeira versão local do Laboratório de Trading com ChatGPT.

## Etapas e critérios
1. [x] Inspecionar diretório (vazio, apenas .git) e ler as 27 páginas do PDF.
2. [x] Fixar especificações, configuração e fronteiras cronológicas antes dos resultados.
3. [x] Implementar pacote Python, validação, indicadores, estratégias e contabilidade.
4. [x] Implementar relatórios rastreáveis e dashboard em português.
5. [x] Executar testes manuais conhecidos, custos, sessões, causalidade e integração.
6. [x] Iniciar aplicação local, verificar saúde e documentar evidências.

## Decisões
- Sem dados reais fornecidos: demonstração sintética intraday com semente fixa.
- Sessão artificial explícita, sem atribuí-la à B3. Calendário de sessões fornecido na configuração.
- Um ativo à vista por execução; sem futuros, alavancagem ou shorts.
- Execução na abertura seguinte; encerramento programado na abertura de uma barra anterior ao término.
- Dados incompletos, sessões não previstas e lacunas intradiárias são rejeitados.
- Divisão por sessões completas, sem ajuste de parâmetros; indicadores reiniciam a cada partição, mas não por sessão.
- Sem anualização nesta versão; teste final é exploratório e não servirá para seleção.

## Verificação e bloqueios
Ambiente isolado .venv criado, pacote instalado em modo editável e versões congeladas em requirements-lock.txt. Instalação e testes exigiram execução autorizada fora do sandbox por bloqueios no cache e temporários. Primeira suíte: 16 passavam, dois erros de temporários e um caminho relativo do AppTest incorreto. Corrigido caminho absoluto; suíte passou, depois foi ampliada para cruzamentos, métricas e horários.

Servidor Streamlit iniciado em 127.0.0.1:8501; saúde HTTP 200 / ok. AppTest carregou interface, clicou execução e verificou tabelas sem exceções. Tentativa de navegador integrado falhou antes da navegação (CreateProcessWithLogonW 1056); revisão visual pelo navegador permanece não verificada. Não impede uso local.

Resultados: demonstração com 540 barras, 15 sessões artificiais; desenvolvimento 8 sessões, validação 4, teste 3. Nenhum parâmetro escolhido após os resultados. Documentação e hashes em runs/. Dados reais/calendário oficial não foram fornecidos; eficácia de mercado permanece sem evidência. Sem bloqueios indispensáveis restantes.

## Revisão técnica solicitada em 06/10/2026
- [x] Completar métricas caixa, mantendo métricas por operação ausentes.
- [x] Preservar tipos numéricos e formatar somente a apresentação; remover causa de ArrowInvalid.
- [x] Gráfico do registro usando snapshot e indicadores/sinais/ordens persistidos, independente dos dados atuais.
- [x] Regressões e suíte completa: 38 testes aprovados; log integral em docs/pytest-review-full-output.txt.
- [x] Nova execução 20261007T002250Z_66bfdcc1, mesmos parâmetros e dados; conferência de preservação por hash.
- [x] ZIP atualizado com fontes, testes, logs, registros e resumo em docs/TECHNICAL_REVIEW.md.

Primeira rodada das novas regressões detectou colunas inteiramente ausentes com dtype object e perda de timezone na conversão Pandas/Plotly. Corrigidos com conversão numérica explícita e timestamps ISO com offset. Reexecução completa passou; sem novas estratégias ou otimização.
