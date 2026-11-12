"""Procura dados pessoais nos arquivos que vão para o git: CPF, número de cartão, e-mail, caminho de usuário do
Windows e as palavras da sua lista local `.dados_pessoais.txt` (uma por linha: seu nome, de quem divide com você,
estabelecimentos, cidade...). Essa lista fica fora do git.

Uso: python scripts/verificar_dados_pessoais.py      (sai com erro se achar algo)
Roda no hook de pre-commit (.githooks) e no GitHub Actions.
"""
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
IGNORAR = {"LICENSE", "painel/vendor/echarts-5.5.1.min.js", "painel/vendor/ECHARTS-LICENSE.txt"}
PADROES = {
    "CPF": re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
    "cartão": re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"),
    "e-mail": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "caminho de usuário": re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+", re.IGNORECASE),
}
EMAILS_PERMITIDOS = re.compile(r"(noreply|exemplo|example)", re.IGNORECASE)


def arquivos():
    saida = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=RAIZ,
                           capture_output=True, text=True, check=True).stdout
    return [a for a in saida.splitlines() if a not in IGNORAR]


def main():
    proibidas = []
    lista = RAIZ / ".dados_pessoais.txt"
    if lista.exists():
        proibidas = [p.strip() for p in lista.read_text(encoding="utf-8").splitlines() if p.strip() and not p.startswith("#")]
    achados = []
    for nome in arquivos():
        try:
            texto = (RAIZ / nome).read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        for n, linha in enumerate(texto.splitlines(), start=1):
            for tipo, padrao in PADROES.items():
                for m in padrao.finditer(linha):
                    if tipo == "e-mail" and EMAILS_PERMITIDOS.search(m.group()):
                        continue
                    achados.append(f"{nome}:{n}: {tipo}")
            for palavra in proibidas:
                if palavra.lower() in linha.lower():
                    achados.append(f"{nome}:{n}: palavra da lista pessoal")
    if achados:
        print("Possíveis dados pessoais (o valor não é mostrado):")
        print("\n".join(sorted(set(achados))))
        sys.exit(1)
    print(f"ok  {len(arquivos())} arquivos sem dados pessoais" + ("" if proibidas else " (sem lista .dados_pessoais.txt)"))


if __name__ == "__main__":
    main()
