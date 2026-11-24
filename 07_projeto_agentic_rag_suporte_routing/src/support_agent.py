"""Agente de suporte e routing — esqueleto do aluno (módulo 07).

TICKET → CLASSIFICAÇÃO → PRIORIDADE → FILA → RUNBOOK → PLANO → APROVAÇÃO/HANDOFF

Segurança vence acesso. Mutação exige aprovação. Handoff é um resultado válido.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
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
    """TODO(7.1/7.2): pontue palavras-chave de cada categoria, priorize segurança e
    devolva (`categoria`, confiança). Sem evidência → `indefinido`, confiança 0."""
    # TODO(7.2): implemente classificar_ticket
    raise NotImplementedError("TODO(7.2): implemente classificar_ticket")


def priorizar(ticket: Ticket, categoria: str) -> str:
    """TODO(7.2): aplique a política de prioridade.

    P1: todos os clientes, indisponibilidade total, incidente de segurança grave.
    P2: cobrança duplicada, serviço parado, webhook atrasado, 50 usuários.
    P3: dúvida, cartão, senha individual, usuário bloqueado.
    """
    # TODO(7.2): implemente priorizar
    raise NotImplementedError("TODO(7.2): implemente priorizar")


def rotear(ticket: Ticket, cliente: Cliente) -> Roteamento:
    """TODO(7.2): combine categoria, prioridade, fila e SLA (Enterprise P1 menor)."""
    # TODO(7.2): implemente rotear
    raise NotImplementedError("TODO(7.2): implemente rotear")


def recuperar_runbook(categoria: str, data_dir: Path) -> Runbook:
    """TODO(7.3): carregue `data/runbooks/<categoria>.md`, com fallback seguro."""
    # TODO(7.3): implemente recuperar_runbook
    raise NotImplementedError("TODO(7.3): implemente recuperar_runbook")


def deve_escalar(ticket: Ticket, roteamento: Roteamento) -> str | None:
    """TODO(7.5): retorne o motivo do handoff ou None.

    Gatilhos: P1, segurança, baixa confiança e integração parada/total.
    """
    # TODO(7.5): implemente deve_escalar
    raise NotImplementedError("TODO(7.5): implemente deve_escalar")


def planejar_acoes(ticket: Ticket, roteamento: Roteamento) -> list[Acao]:
    """TODO(7.4): escolha ferramentas do runbook.

    - reembolso: consultar_fatura → solicitar_reembolso (aprovação);
    - acesso: verificar_identidade → reset/desbloqueio;
    - integração: verificar status → reprocessar ou escalar;
    - segurança/P1: escalar, sem mutação;
    - indefinido: escalar_suporte.
    """
    # TODO(7.4): implemente planejar_acoes
    raise NotImplementedError("TODO(7.4): implemente planejar_acoes")


def executar_ticket(ticket: Ticket, cliente: Cliente, data_dir: Path) -> ResultadoTicket:
    """TODO(7.4/7.5): roteie, recupere o runbook, planeje e simule a execução.

    Pare em `aguardando_aprovacao` antes de qualquer mutação que exija aprovação.
    Handoff encerra com status `handoff`; nunca marque como resolvido.
    """
    # TODO(7.4): implemente executar_ticket
    raise NotImplementedError("TODO(7.4): implemente executar_ticket")
