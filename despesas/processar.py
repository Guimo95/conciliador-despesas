"""Junta as peças: classifica os lançamentos novos, reaplica regras e respostas e calcula as divisões."""
from decimal import Decimal

from .config import Config
from .divisao import dividir, fracoes_do_lancamento
from .regras import classificar


def _aplicar(linha: dict, regras: dict, respostas: dict) -> dict:
    c = classificar(linha["descricao_banco"], regras, linha.get("parcela", ""), respostas)
    if c.acao == "ignorar":
        linha.update(status="ignorado", categoria="", descricao="", motivo=c.motivo)
    elif c.acao == "classificado":
        linha.update(status="classificado", categoria=c.categoria, descricao=c.descricao, motivo="")
    else:
        motivo = c.motivo
        if linha.get("tipo") == "entrada" and c.acao == "sem_regra":
            motivo = "Entrada não reconhecida: receita, estorno ou transferência entre contas?"
        linha.update(status="perguntar", categoria="", descricao="", motivo=motivo)
    return linha


def classificar_novos(novos: list, regras: dict, cfg: Config, respostas: dict | None = None) -> list:
    for n in novos:
        n.setdefault("pago_por", cfg.titular)
        _aplicar(n, regras, respostas or {})
    return novos


def reaplicar(livro: list, regras: dict, respostas: dict | None = None) -> int:
    """Depois que a pessoa responde dúvidas ou ganha regra nova: reclassifica só o que ainda está em 'perguntar'."""
    mudou = 0
    for linha in livro:
        if linha.get("status") == "perguntar":
            antes = (linha["status"], linha["categoria"])
            _aplicar(linha, regras, respostas or {})
            mudou += (linha["status"], linha["categoria"]) != antes
    return mudou


def calcular_divisoes(livro: list, cfg: Config, categorias_receita=("Receita",)) -> list:
    """Uma linha por lançamento e pessoa. Estorno (entrada numa categoria de despesa) entra negativo.
    Receitas e lançamentos ignorados ou pendentes não dividem."""
    resultado = []
    for l in livro:
        if l.get("status") != "classificado" or l.get("categoria") in categorias_receita:
            continue
        sinal = Decimal(1) if l.get("tipo", "saida") == "saida" else Decimal(-1)
        fracoes = fracoes_do_lancamento(cfg, l["categoria"], l["descricao_banco"], l.get("divisao_manual", ""))
        for pessoa, valor in dividir(Decimal(l["valor"]) * sinal, fracoes, cfg.titular).items():
            resultado.append({"id": l["id"], "pessoa": pessoa, "valor": f"{valor:.2f}"})
    return resultado
