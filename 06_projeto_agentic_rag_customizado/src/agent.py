"""Agente RAG com ferramentas — esqueleto do aluno (módulo 06).

ESTADO → ROTA → FERRAMENTAS → REFLEXÃO → RESPOSTA

Regras de ouro:
- prompt injection é bloqueado antes de qualquer ferramenta;
- cálculo usa AST com whitelist, nunca `eval`;
- retrieval sem citação é falha de reflexão;
- o loop tem orçamento máximo de passos.
"""

from __future__ import annotations

import ast
import json
import math
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path

STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "de", "do", "da", "dos", "das", "em", "no", "na",
    "nos", "nas", "por", "para", "com", "sem", "que", "qual", "quais", "quando", "onde",
    "como", "quem", "e", "ou", "é", "são", "ser", "foi", "tem", "ter", "há", "ao", "aos",
    "se", "sua", "seu", "suas", "seus", "mais", "menos", "muito", "quanto", "quantos",
}

POLICY_TERMS = {
    "politica", "limite", "reembolso", "viagem", "alimentacao", "hotel", "home office",
    "compra", "comprar", "monitor", "aprovacao", "beneficio", "despesa", "diaria", "bonus",
}
INJECTION_TERMS = {
    "ignore as regras", "ignorar as regras", "desconsidere", "revele", "system prompt",
    "salario de todos", "finja que",
}


@dataclass(frozen=True)
class Trecho:
    fonte: str
    texto: str
    score: float


@dataclass(frozen=True)
class Calculo:
    expressao: str
    valor: float
    formatado: str


@dataclass(frozen=True)
class Passo:
    ferramenta: str
    entrada: str
    saida: str
    ok: bool


@dataclass
class AgentState:
    pergunta: str
    rota: tuple[str, ...] = ()
    passos: list[Passo] = field(default_factory=list)
    evidencias: list[Trecho] = field(default_factory=list)
    calculos: list[Calculo] = field(default_factory=list)
    resposta: str = ""
    status: str = "novo"
    motivo: str = ""
    max_passos: int = 6

    @property
    def ferramentas_usadas(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(p.ferramenta for p in self.passos))

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def normalizar(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto.lower())
    return re.sub(r"[^a-z0-9\s]", " ", "".join(c for c in decomposto if not unicodedata.combining(c)))


def tokenizar(texto: str) -> list[str]:
    return [
        t for t in normalizar(texto).split()
        if (len(t) > 2 or t.isdigit()) and t not in STOPWORDS
    ]


def carregar_docs(data_dir: Path) -> list[tuple[str, str]]:
    return [
        (caminho.name, caminho.read_text(encoding="utf-8").strip())
        for caminho in sorted((data_dir / "docs").glob("*.md"))
    ]


def carregar_tarefas(data_dir: Path) -> list[dict[str, object]]:
    return json.loads((data_dir / "tarefas.json").read_text(encoding="utf-8"))


def _num_br(texto: str) -> float:
    bruto = texto.strip().replace(" ", "")
    if "," in bruto:
        return float(bruto.replace(".", "").replace(",", "."))
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", bruto):
        return float(bruto.replace(".", ""))
    return float(bruto)


def _fmt_num(valor: float) -> str:
    return str(int(round(valor))) if abs(valor - round(valor)) < 1e-9 else f"{valor:.2f}"


def extrair_expressao(texto: str) -> str | None:
    """Extrai uma expressão aritmética de uma pergunta em português.

    TODO(6.4): cubra pelo menos:
    - "N diárias/dias de R$ X" -> N*X;
    - "R$ X por dia em N dias" -> X*N;
    - expressão explícita "12 * 8";
    - valores brasileiros ("1.200,50").
    Retorne None quando não houver cálculo.
    """
    # TODO(6.4): implemente extrair_expressao
    raise NotImplementedError("TODO(6.4): implemente extrair_expressao")


def calcular(expressao: str) -> Calculo:
    """Calculadora segura via AST (sem `eval`).

    TODO(6.4): permita apenas números, +, -, *, /, parênteses e unários.
    Rejeite chamadas, nomes, atributos, potência e divisão por zero.
    """
    # TODO(6.4): implemente calcular
    raise NotImplementedError("TODO(6.4): implemente calcular")


def classificar_rota(pergunta: str) -> tuple[str, ...]:
    """Decide o caminho antes de agir.

    TODO(6.2): retorne uma combinação de:
    - ("guardrail",) para prompt injection;
    - ("direct",) para saudação;
    - ("abstencao",) para pergunta fora das capacidades;
    - ("buscar_politicas",), ("calcular",) ou ambos.
    """
    # TODO(6.2): implemente classificar_rota
    raise NotImplementedError("TODO(6.2): implemente classificar_rota")


def buscar_politicas(pergunta: str, data_dir: Path, top_k: int = 3) -> list[Trecho]:
    """Retrieval lexical de frases de políticas.

    TODO(6.3): split por frase, score de sobreposição, threshold mínimo e top_k.
    """
    # TODO(6.3): implemente buscar_politicas
    raise NotImplementedError("TODO(6.3): implemente buscar_politicas")


def refletir(estado: AgentState) -> AgentState:
    """Verifica citações, erros, abstenção e orçamento.

    TODO(6.5): mude `status`/`motivo` quando:
    - retrieval não trouxe evidência e não houve cálculo → abstencao;
    - etapa falhou → falhou;
    - resposta de política sem citação → falhou;
    - passos > max_passos → orcamento_excedido.
    """
    # TODO(6.5): implemente refletir
    raise NotImplementedError("TODO(6.5): implemente refletir")


def executar_agente(
    pergunta: str, data_dir: Path, max_passos: int = 6
) -> AgentState:
    """Loop principal do agente.

    TODO(6.5):
    - crie o estado, classifique a rota e respeite o orçamento antes de cada passo;
    - execute ferramentas, registre `Passo` e acumule evidências/cálculos;
    - monte resposta com citações e cálculos;
    - chame `refletir` e devolva o estado serializável.
    """
    # TODO(6.5): implemente executar_agente
    raise NotImplementedError("TODO(6.5): implemente executar_agente")
