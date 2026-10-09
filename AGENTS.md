# Instruções para agentes

## 1. Ambiente e organização
- Pasta canônica: `C:\Users\Marcio\Desktop\Analise Quantitativa\Quant Trading\Laboratorio Quantitativo`.
- Repositório: `kamikazedojapan/Laboratorio-Quantitativo`; branch atual esperada: `main`.
- Trabalhar diretamente na pasta canônica, sem duplicar o projeto em `Documents\ChatGPT` nem criar outra workspace.
- Antes de editar, executar `Get-Location`, `git rev-parse --show-toplevel`, `git branch --show-current` e `git status --short`.
- Conferir a raiz Git, a branch e as alterações existentes; preservar alterações anteriores do usuário.
- No Windows, usar `.\.venv\Scripts\python.exe` para comandos Python.
- O projeto exige Python >= 3.11; conferir a versão efetiva com `.\.venv\Scripts\python.exe --version`.
- Respeitar `.gitignore`; guardar arquivos temporários e backups em `tmp/`.

## 2. Escopo e execução
- Executar as tarefas autorizadas até concluir implementação e validação.
- Manter mudanças relacionadas à tarefa, sem refatorações paralelas.
- Alterar regras de negociação, custos ou cálculos somente quando a tarefa solicitar expressamente.
- Atualizar a documentação quando o comportamento mudar.
- Comunicar em português o resultado, os arquivos alterados, as verificações executadas e as pendências reais.

## 3. Preservação histórica
- Preservar dados, resultados, manifestos e snapshots existentes.
- Proteger especialmente `runs/20261009T035723Z_37aafd9d/`.
- Manter no `.gitattributes` a regra `runs/20261009T035723Z_37aafd9d/** -text`.
- Tratar hashes como verificações dos bytes, incluindo finais de linha.
- Quando a tarefa afetar a preservação histórica, conferir `artifact_sha256` contra os artefatos da execução e `source_sha256` contra os arquivos correspondentes em `source/`.
- Antes de restaurar arquivos históricos, fazer backup em `tmp/` e confirmar que os bytes propostos correspondem aos hashes originais.
- Não apagar arquivos históricos nem recalcular seus hashes para acomodar modificações.

## 4. Contrato do dashboard
- Somente o valor exato `LAB_PUBLIC_DEMO="1"` ativa o modo público.
- Variável ausente ou com outro valor mantém o comportamento local.
- No modo público: usar dados sintéticos, sem importação nem uploaders.
- Restringir o histórico público a `config.data_kind == "synthetic"`.
- No modo público, permitir de 3 a 260 sessões, com valor inicial 60.
- Preservar indicadores, comparações, gráficos e download do resumo.
- Preservar a importação no modo local.

## 5. Validação
- Executar testes relevantes durante alterações de código.
- Ao concluir mudanças funcionais, executar `.\.venv\Scripts\python.exe -m pytest -q`.
- Quando houver alterações no ambiente ou nas dependências, executar `.\.venv\Scripts\python.exe -m pip check`.
- Verificar mudanças somente documentais por leitura, conteúdo, comandos e diff.
- Registrar resultados realmente obtidos, sem fixar uma quantidade permanente de testes aprovados.

## 6. Code Review Rules
- Quando afetadas, revisar causalidade dos sinais, separação temporal das partições, aplicação de custos e consistência contábil.
- Conferir isolamento entre os modos público e local.
- Conferir preservação histórica quando aplicável.
- Revisar status, diff completo e arquivos novos antes de versionar.
- Usar também `git diff --ignore-cr-at-eol` para distinguir finais de linha, mantendo a verificação de hashes quando necessária.
- Para verificar whitespace sem tratar CRLF preservado como erro, executar `git -c core.whitespace=cr-at-eol diff --check`.
- Staging, commit, push e publicação somente quando expressamente autorizados pelo usuário.
- Selecionar explicitamente apenas os arquivos revisados para staging e versionamento.
