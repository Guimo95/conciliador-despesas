"""Divisão de cada despesa entre as pessoas e acerto de contas (quem deve a quem)."""
from collections import defaultdict
from decimal import ROUND_HALF_EVEN, Decimal

from .config import Config, ErroConfig

CENTAVO = Decimal("0.01")


def ler_divisao_manual(texto: str, pessoas) -> dict | None:
    """Divisão marcada no próprio lançamento, ex.: 'Ana=0.7;Bruno=0.3'. Vazio = usa a regra."""
    texto = (texto or "").strip()
    if not texto:
        return None
    fracoes = {}
    for parte in texto.split(";"):
        pessoa, _, valor = parte.partition("=")
        pessoa = pessoa.strip()
        if pessoa not in pessoas:
            raise ErroConfig(f"divisão manual '{texto}': '{pessoa}' não está na lista de pessoas")
        fracoes[pessoa] = Decimal(valor.strip())
    if sum(fracoes.values()) != 1:
        raise ErroConfig(f"divisão manual '{texto}': as frações precisam somar 1")
    return fracoes


def fracoes_do_lancamento(cfg: Config, categoria: str, descricao_banco: str = "", manual: str = "") -> dict:
    d = cfg.divisao
    marcada = ler_divisao_manual(manual, cfg.pessoas)
    if marcada:
        return marcada
    if d.modo == "individual" or len(cfg.pessoas) == 1:
        return {cfg.titular: Decimal(1)}
    texto = (descricao_banco or "").upper()
    for e in d.excecoes:
        if e["padrao"] in texto:
            return e["divisao"]
    if d.modo == "igual":
        if categoria in d.sem_divisao:
            return {cfg.titular: Decimal(1)}
        n = len(cfg.pessoas)
        return {p: Decimal(1) / n for p in cfg.pessoas}
    return d.categorias.get(categoria, d.padrao)


def dividir(valor, fracoes: dict, titular: str) -> dict:
    """Valor por pessoa, em centavos. Arredondamento bancário (meio centavo vai para o par, como o round do Python),
    que não puxa a soma de muitas linhas sempre para cima. A sobra fica com o titular, para a soma bater com o valor."""
    valor = Decimal(str(valor))
    partes = {p: (valor * f).quantize(CENTAVO, rounding=ROUND_HALF_EVEN) for p, f in fracoes.items() if f}
    sobra = valor - sum(partes.values())
    if sobra:
        partes[titular] = partes.get(titular, Decimal(0)) + sobra
    return partes


def acerto(lancamentos, cfg: Config, pagamentos=()) -> dict:
    """Saldo de cada pessoa: positivo = tem a receber; negativo = deve.
    lancamentos: dicts com valor, pago_por (vazio = titular) e partes {pessoa: valor}.
    pagamentos: dicts com de, para, valor (acerto feito entre as pessoas, ex.: um Pix)."""
    saldo = defaultdict(Decimal)
    for l in lancamentos:
        pagador = l.get("pago_por") or cfg.titular
        saldo[pagador] += Decimal(str(l["valor"]))
        for pessoa, parte in l["partes"].items():
            saldo[pessoa] -= Decimal(str(parte))
    for p in pagamentos:
        saldo[p["de"]] += Decimal(str(p["valor"]))
        saldo[p["para"]] -= Decimal(str(p["valor"]))
    return {p: saldo[p].quantize(CENTAVO) for p in cfg.pessoas}


def frase_acerto(saldos: dict, moeda="R$") -> list:
    """Texto curto: 'Bruno deve R$ 120,50 a Ana'. Com mais de duas pessoas, cada devedor paga a quem tem a receber."""
    credores = sorted([[p, v] for p, v in saldos.items() if v > 0], key=lambda x: -x[1])
    devedores = sorted([[p, -v] for p, v in saldos.items() if v < 0], key=lambda x: -x[1])
    frases = []
    while credores and devedores:
        c, d = credores[0], devedores[0]
        valor = min(c[1], d[1])
        frases.append(f"{d[0]} deve {moeda} {valor:,.2f} a {c[0]}".replace(",", "X").replace(".", ",").replace("X", "."))
        c[1] -= valor
        d[1] -= valor
        if not c[1]:
            credores.pop(0)
        if not d[1]:
            devedores.pop(0)
    return frases or ["Ninguém deve nada"]
