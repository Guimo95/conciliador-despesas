# Assistente de configuração

Use na primeira vez, ou quando a pessoa quiser mudar quem divide o quê. Faça uma pergunta por vez, em linguagem simples, e mostre um resumo antes de gravar.

1. **Quem é o titular** (o dono das contas conectadas)?
2. **Divide despesas com alguém?** Se não, o modo é `individual` e pule para o passo 5.
3. **Com quem?** Nomes curtos, como aparecem no report.
4. **Como dividem?**
   - Tudo igual entre todos (modo `igual`). Há categorias que cada um paga sozinho? Elas vão em `sem_divisao`.
   - Por categoria (modo `por_categoria`): para cada categoria que dividem, quanto fica com cada pessoa (ex.: Casa 50% e 50%, Mercado 70% e 30%). O que não for dividido fica com o titular.
   - Algum estabelecimento foge da regra da categoria? Ele vai em `excecoes`.
   - Lembre a pessoa de que dá para marcar a divisão de um lançamento específico depois.
5. **De onde vêm os dados?** Belvo MCP (veja `docs/belvo_mcp.md`) ou arquivos do banco. Para CSV, peça um arquivo de exemplo e monte o perfil de colunas.
6. **Contas fixas** para os alertas: nome, dia do vencimento, valor aproximado e com quantos dias de antecedência avisar.
7. **Report:** frequência (diária, semanal ou mensal, e em que dia) e canal.

Grave em `meus-dados/config.yaml` partindo de `config/exemplo/config.yaml`, e copie `config/exemplo/regras.yaml` para `meus-dados/regras.yaml` (as regras de exemplo servem de ponto de partida; vá ajustando com as respostas). As frações de cada divisão precisam somar 1: o programa recusa se não somarem.
