# Instruções para o agente (qualquer LLM)

Este repositório é um conciliador de despesas pessoais. Você, agente, faz o que precisa de julgamento (buscar os dados, entender um lançamento que as regras não cobrem, perguntar à pessoa, escrever o report). Todo cálculo fica nos scripts em Python: não some, não divida e não classifique "de cabeça" o que um comando resolve.

## Onde estão as coisas

- `meus-dados/` (fora do git): `config.yaml`, `regras.yaml`, `respostas.yaml`, `contas.yaml`, `livro.csv`, `divisoes.csv`, `pagamentos.csv` e a pasta `entrada/` com os arquivos baixados. Se não existir, rode o assistente de configuração (`prompts/configurar.md`).
- `config/exemplo/`: modelo de configuração com pessoas fictícias.
- Comandos (sempre a partir da raiz do repositório):
  - `python -m despesas importar <arquivo> [--perfil X] [--conta Y]`
  - `python -m despesas reaplicar`
  - `python -m despesas resumo --mes AAAA-MM`
  - `python -m despesas acerto`

## Regras de trabalho

1. **Dados da pessoa ficam na máquina dela.** Nunca coloque nada de `meus-dados/` em commit, issue, log público ou serviço externo. Não cole extrato em ferramenta de terceiros.
2. **Cálculo é do script.** Valores, divisão e acerto vêm dos comandos. Se um número do report não veio de um comando, não escreva.
3. **Na dúvida, pergunte.** É melhor uma pergunta curta do que uma categoria errada que muda a divisão.
4. **Resposta vira regra.** Quando a pessoa responder, grave em `respostas.yaml` (`DESCRIÇÃO DO BANCO: {categoria: X, descricao: Y}`). Se o mesmo estabelecimento vai aparecer de novo, proponha uma regra no `regras.yaml` e grave só depois do ok. Depois rode `reaplicar`.
5. **Não é aconselhamento financeiro.** Você organiza e avisa; não recomenda investimento, crédito ou produto.

## Quando perguntar

- Estabelecimento sem regra.
- Loja que vende de tudo (marketplace, loja on-line): a categoria muda a divisão.
- Restaurante, bar e delivery quando a pessoa usa categorias diferentes para "comida fora" e "lazer".
- Compra parcelada nova: confirmar a categoria uma vez; as parcelas seguintes seguem a primeira.
- Entrada que não é salário conhecido: receita, estorno ou transferência entre contas?
- Mercado com valor fora do padrão da pessoa (pode ser compra de outra categoria no mesmo lugar).

Faça as perguntas numeradas, uma por linha, com data, descrição do banco e valor, e diga o que muda conforme a resposta (por exemplo, a divisão).

## Fontes de dados

- **Belvo MCP** (contas da própria pessoa): passo a passo em `docs/belvo_mcp.md`.
- **Arquivo do banco**: OFX (extrato ou fatura) ou CSV com um perfil de colunas no `config.yaml`. Funciona com qualquer banco e qualquer LLM.

## Rotinas

- Diária: `prompts/rotina_diaria.md`.
- Report na frequência do `config.yaml`: `prompts/report.md`.
- Primeira configuração: `prompts/configurar.md`.
- Como agendar: `docs/agendamento.md`.
