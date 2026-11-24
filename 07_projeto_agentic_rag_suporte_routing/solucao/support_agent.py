"""Referência funcional do agente de suporte e routing (módulo 07)."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

CATEGORIAS = ("cobranca", "acesso", "integracao", "seguranca")
PRIORIDADES = ("P1", "P2", "P3")
FILAS = {
    "cobranca": "financeiro",
    "acesso": "suporte_n1",
    "integracao": "engenharia",
    "seguranca": "seguranca",
    "indefinido": "triagem",
}
SLA_HORAS = {"P1": 1.0, "P2": 8.0, "P3": 24.0}
MUTANTES = {"solicitar_reembolso", "bloquear_conta", "reset_senha", "desbloquear_conta", "reprocessar_evento"}

KEYWORDS = {
    "seguranca": {
        "acesso indevido": 3,
        "vazamento": 3,
        "credencial": 2,
        "suspeito": 2,
        "seguranca": 2,
        "dados de pacientes": 2,
        "incidente": 1,
    },
    "integracao": {
        "api": 2,
        "webhook": 2,
        "integracao": 2,
        "erp": 2,
        "500": 2,
        "evento": 1,
        "fila": 1,
    },
    "acesso": {
        "senha": 2,
        "login": 2,
        "acesso": 1,
        "bloqueado": 2,
        "mfa": 2,
    },
    "cobranca": {
        "fatura": 2,
        "cobranca": 2,
        "cobrado": 2,
        "reembolso": 3,
        "cartao": 2,
        "plano": 1,
        "duplicada": 2,
        "valor": 1,
    },
}


@dataclass(frozen=True)
class Ticket:
    id: str
    cliente_id: str
    texto: str
    categoria_esperada: str | None = None
    prioridade_esperada: str | None = None
    status_esperado: str | None = None
    valor: float = 0.0


@dataclass(frozen=True)
class Cliente:
    id: str
    nome: str
    plano: str


@dataclass(frozen=True)
class Roteamento:
    categoria: str
    prioridade: str
    fila: str
    sla_horas: float
    confianca: float
    justificativa: str


@dataclass(frozen=True)
class Runbook:
    categoria: str
    titulo: str
    conteudo: str


@dataclass(frozen=True)
class Acao:
    ferramenta: str
    requer_aprovacao: bool = False
    motivo: str = ""


@dataclass(frozen=True)
class ResultadoTicket:
    ticket_id: str
    roteamento: Roteamento
    status: str
    acoes: tuple[Acao, ...]
    eventos: tuple[str, ...]
    runbook: str
    motivo_escalonamento: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def normalizar(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto.lower())
    return re.sub(r"[^a-z0-9\s]", " ", "".join(c for c in decomposto if not unicodedata.combining(c)))


def carregar_tickets(data_dir: Path) -> list[Ticket]:
    itens = [
        json.loads(linha)
        for linha in (data_dir / "tickets.jsonl").read_text(encoding="utf-8").splitlines()
        if linha.strip()
    ]
    return [
        Ticket(
            id=i["id"],
            cliente_id=i["cliente_id"],
            texto=i["texto"],
            categoria_esperada=i.get("categoria_esperada"),
            prioridade_esperada=i.get("prioridade_esperada"),
            status_esperado=i.get("status_esperado"),
            valor=float(i.get("valor", 0.0)),
        )
        for i in itens
    ]


def carregar_clientes(data_dir: Path) -> dict[str, Cliente]:
    dados = json.loads((data_dir / "clientes.json").read_text(encoding="utf-8"))
    return {i["id"]: Cliente(i["id"], i["nome"], i["plano"]) for i in dados}


def classificar_ticket(ticket: Ticket) -> tuple[str, float]:
    p = normalizar(ticket.texto)
    scores: dict[str, int] = {}
    for categoria, palavras in KEYWORDS.items():
        scores[categoria] = sum(peso for termo, peso in palavras.items() if termo in p)
    melhor = max(scores.values(), default=0)
    if melhor == 0:
        return ("indefinido", 0.0)
    # Segurança vence empates; depois integração, acesso e cobrança.
    ordem = {"seguranca": 0, "integracao": 1, "acesso": 2, "cobranca": 3}
    categoria = sorted(
        (c for c, score in scores.items() if score == melhor), key=lambda c: ordem[c]
    )[0]
    confianca = min(1.0, 0.35 + 0.2 * melhor)
    return (categoria, round(confianca, 2))


def priorizar(ticket: Ticket, categoria: str) -> str:
    p = normalizar(ticket.texto)
    if categoria == "seguranca":
        return "P1"
    if categoria == "integracao":
        if "todos os clientes" in p or "indisponibilidade total" in p:
            return "P1"
        if "parada" in p or "webhook" in p or "50 usuarios" in p or "fila" in p:
            return "P2"
        return "P3"
    if categoria == "cobranca":
        if any(t in p for t in ("duplicada", "indevida", "reembolso", "cobrado duas")):
            return "P2"
        return "P3"
    if categoria == "acesso":
        if "todos" in p or "admin" in p:
            return "P2"
        return "P3"
    return "P2"


def rotear(ticket: Ticket, cliente: Cliente) -> Roteamento:
    categoria, confianca = classificar_ticket(ticket)
    prioridade = priorizar(ticket, categoria)
    fila = FILAS.get(categoria, "triagem")
    sla = SLA_HORAS[prioridade]
    if cliente.plano == "Enterprise" and prioridade == "P1":
        sla = 0.5
    return Roteamento(
        categoria=categoria,
        prioridade=prioridade,
        fila=fila,
        sla_horas=sla,
        confianca=confianca,
        justificativa=(
            f"Categoria {categoria} (confiança {confianca:.0%}); "
            f"prioridade {prioridade}; cliente {cliente.plano}."
        ),
    )


def recuperar_runbook(categoria: str, data_dir: Path) -> Runbook:
    nome = categoria if categoria in CATEGORIAS else "fallback"
    caminho = data_dir / "runbooks" / f"{nome}.md"
    if not caminho.exists():
        caminho = data_dir / "runbooks" / "fallback.md"
    conteudo = caminho.read_text(encoding="utf-8").strip()
    titulo = conteudo.splitlines()[0].lstrip("# ").strip()
    return Runbook(nome, titulo, conteudo)


def deve_escalar(ticket: Ticket, roteamento: Roteamento) -> str | None:
    p = normalizar(ticket.texto)
    if roteamento.categoria == "seguranca":
        return "Incidente de segurança exige time especializado"
    if roteamento.prioridade == "P1":
        return "Prioridade P1 exige handoff imediato"
    if roteamento.categoria == "indefinido" or roteamento.confianca < 0.34:
        return "Classificação de baixa confiança; encaminhar para triagem"
    if roteamento.categoria == "integracao" and any(
        termo in p for termo in ("parada", "indisponibilidade", "perda de dados")
    ):
        return "Integração parada; requer engenharia"
    return None


def planejar_acoes(ticket: Ticket, roteamento: Roteamento) -> list[Acao]:
    p = normalizar(ticket.texto)
    if roteamento.categoria == "seguranca":
        return [Acao("escalar_seguranca", motivo="Incidente de segurança")]
    if roteamento.categoria == "indefinido":
        return [Acao("escalar_suporte", motivo="Baixa confiança")]
    if roteamento.prioridade == "P1":
        if roteamento.categoria == "integracao":
            return [
                Acao("verificar_status_integracao"),
                Acao("escalar_engenharia", motivo="P1 de integração"),
            ]
        return [Acao("escalar_suporte", motivo="P1")]
    if roteamento.categoria == "integracao" and "parada" in p:
        return [
            Acao("verificar_status_integracao"),
            Acao("escalar_engenharia", motivo="Serviço parado"),
        ]
    if roteamento.categoria == "cobranca":
        if any(t in p for t in ("duplicada", "indevida", "reembolso", "cobrado duas")):
            return [
                Acao("consultar_fatura"),
                Acao("solicitar_reembolso", True, "Reembolso exige aprovação do financeiro"),
            ]
        if "cartao" in p:
            return [Acao("consultar_fatura"), Acao("orientar_cliente")]
        return [Acao("orientar_cliente")]
    if roteamento.categoria == "acesso":
        acoes = [Acao("verificar_identidade")]
        acoes.append(Acao("desbloquear_conta") if "bloqueado" in p else Acao("reset_senha"))
        return acoes
    if roteamento.categoria == "integracao":
        return [Acao("verificar_status_integracao"), Acao("reprocessar_evento")]
    return [Acao("escalar_suporte")]


def executar_ticket(ticket: Ticket, cliente: Cliente, data_dir: Path) -> ResultadoTicket:
    roteamento = rotear(ticket, cliente)
    runbook = recuperar_runbook(roteamento.categoria, data_dir)
    acoes = tuple(planejar_acoes(ticket, roteamento))
    motivo = deve_escalar(ticket, roteamento)
    eventos: list[str] = []
    status = "resolvido"

    for acao in acoes:
        if acao.requer_aprovacao:
            eventos.append(f"{acao.ferramenta}: bloqueada (aprovação humana)")
            status = "aguardando_aprovacao"
            break
        if acao.ferramenta.startswith("escalar"):
            eventos.append(f"{acao.ferramenta}: handoff")
            status = "handoff"
            break
        eventos.append(f"{acao.ferramenta}: ok")

    if motivo and status not in {"handoff", "aguardando_aprovacao"}:
        eventos.append(f"escalonamento: {motivo}")
        status = "handoff"

    return ResultadoTicket(
        ticket_id=ticket.id,
        roteamento=roteamento,
        status=status,
        acoes=acoes,
        eventos=tuple(eventos),
        runbook=runbook.titulo,
        motivo_escalonamento=motivo,
    )
