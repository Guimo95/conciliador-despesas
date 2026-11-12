# Report

Mensagem curta, em texto simples, que a pessoa lê no celular. Todo número vem de um comando.

1. Rode `python -m despesas report`. Ele já traz o total, as categorias, a parte de cada pessoa, o acerto, os alertas de contas e as dúvidas agrupadas por estabelecimento (uma resposta resolve todos os lançamentos do mesmo lugar).
2. Use esse rascunho como base e ajuste o texto à pessoa, nesta ordem, pulando o que estiver vazio:
   1. Total do mês até hoje e as três categorias que mais pesaram.
   2. Parte de cada pessoa e a frase do acerto ("Bruno deve R$ 120,50 a Ana").
   3. Alertas de contas (vencida, a vencer, paga em dobro).
   4. Perguntas pendentes, numeradas, com data, descrição e valor.
   5. No máximo três observações úteis e específicas (por exemplo, uma categoria bem acima do mês passado). Sem conselho de investimento.
3. Se a pessoa configurou planilha ou painel, gere e anexe (ver `README.md`).
4. Envie pelo canal combinado no `config.yaml` (e-mail, chat do próprio agente). Se não houver canal configurado, deixe o texto pronto na conversa.
