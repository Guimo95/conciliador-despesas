# Rotina diária

Rode em silêncio. Só fale com a pessoa se houver pergunta nova, alerta ou se for dia de report.

1. **Buscar os dados novos.**
   - Com Belvo MCP: atualize as conexões e baixe as transações de cada conta e cartão desde a data do último lançamento do `meus-dados/livro.csv` menos 5 dias (a Belvo às vezes traz compras com atraso). Grave a lista em `meus-dados/entrada/belvo_AAAA-MM-DD.json` no formato descrito em `docs/belvo_mcp.md`. Se a atualização falhar, siga com o que a Belvo já tiver e anote isso para o report.
   - Sem Belvo: use os arquivos OFX ou CSV que a pessoa deixou em `meus-dados/entrada/` e que ainda não foram importados.
2. **Importar.** Para cada arquivo novo: `python -m despesas importar <arquivo> --conta "<nome da conta>"` (CSV também leva `--perfil`). O comando não duplica o que já existe.
3. **Separar as perguntas.** O comando lista os lançamentos com pergunta. Antes de perguntar, veja se dá para resolver com o que você já sabe da pessoa (respostas anteriores, regras parecidas). O que sobrar vai para a lista de perguntas.
4. **Aplicar respostas recebidas** desde a última rodada: grave em `respostas.yaml`, proponha regras quando fizer sentido e rode `python -m despesas reaplicar`.
5. **Alertas de contas** (quando o `contas.yaml` existir): conta a vencer em até N dias sem pagamento, conta vencida e pagamento em dobro.
6. **Report:** se hoje é dia de report pelo `config.yaml`, siga `prompts/report.md`. Se não for, só avise a pessoa quando houver alerta de conta ou pergunta que muda muito a divisão.
