# Belvo MCP: conectar as próprias contas

A Belvo oferece um servidor MCP que deixa o seu agente ler as contas e os cartões que você mesmo conectar pelo Open Finance. Para uso pessoal, a Belvo informa que conectar e usar é gratuito (confira as condições atuais no site da Belvo). Ninguém além de você e do seu agente vê os dados.

## Conectar

1. Adicione o servidor MCP da Belvo no seu cliente (Claude, ou outro cliente compatível com MCP), seguindo as instruções da Belvo.
2. Peça ao agente o link de conexão e autorize cada banco pelo consentimento do Open Finance. Você não entrega senha para o agente.
3. Anote no `meus-dados/config.yaml`, se quiser, o nome que cada conexão deve ter no livro (`conta`).

## O que o agente grava em `meus-dados/entrada/belvo_AAAA-MM-DD.json`

Uma lista JSON com as transações, cada uma com pelo menos:

| Campo | O que é |
|---|---|
| `value_date` (ou `accounting_date`) | Data da transação |
| `description` | Descrição como veio do banco |
| `local_currency_amount` | Valor em reais. Use este: `amount` é a moeda original (compras no exterior) |
| `type` | `OUTFLOW` (despesa) ou `INFLOW` (entrada ou estorno) |
| `account.name` | Nome da conta ou do cartão |
| `parcela` | Opcional: "2/10" quando a compra é parcelada |

## Cuidados que já apareceram no uso real

- **IOF e ajustes no cartão** podem vir como linhas separadas. Classifique pelo que são (taxa, imposto) ou ignore se forem ajuste duplicado; pergunte se tiver dúvida.
- **Entrada no cartão** costuma ser estorno: ela abate a despesa da mesma categoria.
- **Pagamento da fatura** aparece na conta corrente e deve ser ignorado, porque as compras já estão na fatura. O exemplo de `regras.yaml` já tem o padrão.
- **Paginação:** peça todas as páginas antes de gravar o arquivo.
- **Atualização:** peça à Belvo para atualizar a conexão antes de baixar; se falhar, use os dados já disponíveis e avise no report.
