# Agendar a rotina

A rotina diária precisa de um agente rodando (para buscar os dados e fazer perguntas). Três jeitos, do mais simples ao mais manual:

1. **Agendador do próprio agente.** Alguns clientes (como o app do Claude) têm tarefas agendadas. Crie uma tarefa diária com o texto: "Siga `prompts/rotina_diaria.md` no repositório conciliador-despesas". O computador e o app precisam estar ligados no horário.
2. **Agendador de Tarefas do Windows ou cron**, para a parte que não precisa de agente (importar os arquivos que você deixou em `meus-dados/entrada/`):
   - Windows (PowerShell, na raiz do repositório):
     ```powershell
     $acao = New-ScheduledTaskAction -Execute "$PWD\.venv\Scripts\python.exe" -Argument "-m despesas importar meus-dados\entrada\extrato.ofx" -WorkingDirectory $PWD
     Register-ScheduledTask -TaskName "conciliador - importar" -Action $acao -Trigger (New-ScheduledTaskTrigger -Daily -At "07:15")
     ```
   - Linux ou Mac (`crontab -e`): `15 7 * * * cd /caminho/conciliador-despesas && .venv/bin/python -m despesas importar meus-dados/entrada/extrato.ofx`
3. **Manual:** peça ao agente "rode a rotina diária" quando quiser.
