# Como contribuir

Toda ajuda é bem-vinda: regra nova de exemplo, perfil de CSV de outro banco, correção, melhoria no painel.

Antes de abrir o pull request:

1. Rode `pytest -q` e o `python scripts/verificar_dados_pessoais.py`. Os dois rodam também no GitHub a cada envio.
2. Use só dados fictícios nos exemplos e nos testes. Nada de extrato, nome ou estabelecimento real.
3. Escreva a mensagem do commit no padrão Conventional Commits: `feat: ...`, `fix: ...`, `docs: ...`, `test: ...`, `chore: ...`. Uma mudança por commit.
4. Conta e divisão ficam no Python, com teste. O que for instrução pro agente vai no `AGENTS.md` ou em `prompts/`.

Perfil de CSV de um banco novo: mande o perfil (`config/exemplo/config.yaml`, seção `perfis_csv`) e um arquivo de exemplo com valores inventados.
