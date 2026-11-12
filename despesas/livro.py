"""Livro-razão em CSV (um lançamento por linha) e divisões por pessoa (divisoes.csv)."""
import csv
import hashlib
from decimal import Decimal
from pathlib import Path

COLUNAS = ["id", "data", "tipo", "origem", "conta", "descricao_banco", "valor", "categoria", "descricao", "parcela",
           "pago_por", "status", "motivo", "fatura", "divisao_manual"]
COLUNAS_DIVISAO = ["id", "pessoa", "valor"]
STATUS = ("classificado", "perguntar", "ignorado")


def chave(data, descricao_banco, valor, parcela) -> str:
    """Mesma chave de duplicidade do conciliador original: data, descrição, valor e parcela."""
    texto = f"{data}|{(descricao_banco or '').strip().upper()}|{Decimal(str(valor)):.2f}|{(parcela or '').strip()}"
    return hashlib.sha1(texto.encode("utf-8")).hexdigest()[:12]


def ler(caminho) -> list:
    caminho = Path(caminho)
    if not caminho.exists():
        return []
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def gravar(caminho, linhas, colunas=COLUNAS):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(".tmp")
    with temporario.open("w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=colunas, delimiter=";", extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(linhas)
    temporario.replace(caminho)  # grava inteiro ou não grava: nunca deixa o livro pela metade


def acrescentar(existentes: list, novos: list) -> tuple:
    """Junta os lançamentos novos sem duplicar. Duas compras iguais no mesmo dia (mesma chave) recebem sufixo."""
    ids = {l["id"] for l in existentes}
    vistos_no_lote = {}
    entraram = []
    for n in novos:
        base = chave(n["data"], n["descricao_banco"], n["valor"], n.get("parcela", ""))
        ordem = vistos_no_lote.get(base, 0)
        vistos_no_lote[base] = ordem + 1
        id_ = base if ordem == 0 else f"{base}-{ordem}"
        if id_ in ids:
            continue
        linha = {c: "" for c in COLUNAS}
        linha.update({k: v for k, v in n.items() if k in COLUNAS})
        linha["id"] = id_
        ids.add(id_)
        entraram.append(linha)
    return existentes + entraram, entraram
