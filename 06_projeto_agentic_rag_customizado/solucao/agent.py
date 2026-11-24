"""Referência funcional do agente com ferramentas (módulo 06)."""

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
    if not re.search(r"\d", bruto):
        raise ValueError(f"Número inválido: {texto!r}")
    if "," in bruto:
        return float(bruto.replace(".", "").replace(",", "."))
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", bruto):
        return float(bruto.replace(".", ""))
    return float(bruto)


def _fmt_num(valor: float) -> str:
    return str(int(round(valor))) if abs(valor - round(valor)) < 1e-9 else f"{valor:.2f}"


def extrair_expressao(texto: str) -> str | None:
    if len(texto) > 200:
        return None
    t = texto.replace("R$", " ").replace("r$", " ")

    # "3 diárias de 250" ou "4 dias a 120"
    m = re.search(
        r"(\d+)\s*(?:diárias|diarias|dias|noites|unidades)\s*(?:de|a|por)?\s*(\d[\d.,]*)",
        t,
        re.IGNORECASE,
    )
    if m:
        return f"{_fmt_num(_num_br(m.group(1)))}*{_fmt_num(_num_br(m.group(2)))}"

    # "180 por dia em 4 dias"
    m = re.search(
        r"(\d[\d.,]*)\s*(?:por dia|por noite|/ ?dia)\s*(?:em|por|x)\s*(\d+)\s*"
        r"(?:dias|diarias|diárias|noites)",
        t,
        re.IGNORECASE,
    )
    if m:
        return f"{_fmt_num(_num_br(m.group(1)))}*{_fmt_num(_num_br(m.group(2)))}"

    # "12 * 8", "1.200 + 300"
    m = re.search(r"(?<![\w.])(\d[\d.,]*(?:\s*[+\-*/]\s*\d[\d.,]*)+)", t)
    if m:
        partes = re.split(r"(\s*[+\-*/]\s*)", m.group(1))
        convertidas: list[str] = []
        for parte in partes:
            limpa = parte.strip()
            if not limpa:
                continue
            if limpa in {"+", "-", "*", "/"}:
                convertidas.append(limpa)
            else:
                convertidas.append(_fmt_num(_num_br(limpa)))
        if any(op in convertidas for op in {"+", "-", "*", "/"}):
            return "".join(convertidas)
    return None


def calcular(expressao: str) -> Calculo:
    if len(expressao) > 80:
        raise ValueError("Expressão longa demais")
    try:
        arvore = ast.parse(expressao, mode="eval")
    except SyntaxError as exc:
        raise ValueError("Expressão inválida") from exc

    if sum(1 for _ in ast.walk(arvore)) > 30:
        raise ValueError("Expressão complexa demais")

    def avaliar(no: ast.AST) -> float:
        if isinstance(no, ast.Expression):
            return avaliar(no.body)
        if isinstance(no, ast.Constant) and isinstance(no.value, (int, float)) and not isinstance(no.value, bool):
            return float(no.value)
        if isinstance(no, ast.UnaryOp) and isinstance(no.op, (ast.UAdd, ast.USub)):
            valor = avaliar(no.operand)
            return valor if isinstance(no.op, ast.UAdd) else -valor
        if isinstance(no, ast.BinOp) and isinstance(no.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            esquerda = avaliar(no.left)
            direita = avaliar(no.right)
            if isinstance(no.op, ast.Add):
                return esquerda + direita
            if isinstance(no.op, ast.Sub):
                return esquerda - direita
            if isinstance(no.op, ast.Mult):
                return esquerda * direita
            if direita == 0:
                raise ValueError("Divisão por zero")
            return esquerda / direita
        raise ValueError(f"Nó não permitido: {type(no).__name__}")

    valor = avaliar(arvore)
    if not math.isfinite(valor) or abs(valor) > 1e12:
        raise ValueError("Resultado fora do limite")
    return Calculo(expressao, valor, _fmt_num(valor))


def classificar_rota(pergunta: str) -> tuple[str, ...]:
    p = normalizar(pergunta)
    if any(termo in p for termo in INJECTION_TERMS):
        return ("guardrail",)
    if re.match(r"^(ola|oi|bom dia|boa tarde|boa noite)\b", p) or "o que voce faz" in p:
        return ("direct",)
    tem_calculo = extrair_expressao(pergunta) is not None
    tem_politica = any(termo in p for termo in POLICY_TERMS)
    if tem_calculo and tem_politica:
        return ("buscar_politicas", "calcular")
    if tem_calculo:
        return ("calcular",)
    if tem_politica:
        return ("buscar_politicas",)
    return ("abstencao",)


def _stem_token(token: str) -> str:
    """Radical mínimo para o corpus de políticas (não é um stemmer geral)."""
    if token.startswith("diari") or token == "diario":
        return "dia"
    if token.startswith("politic"):
        return "politica"
    if token.startswith("reembols"):
        return "reembolso"
    if token.startswith("aprov"):
        return "aprovacao"
    if token.startswith("aliment"):
        return "alimentacao"
    return token


def buscar_politicas(
    pergunta: str, data_dir: Path, top_k: int = 3, min_score: float = 0.34
) -> list[Trecho]:
    q = {_stem_token(t) for t in tokenizar(pergunta)}
    if not q:
        return []
    trechos: list[Trecho] = []
    for fonte, texto in carregar_docs(data_dir):
        frases = [
            frase.strip()
            for paragrafo in re.split(r"\n\s*\n", texto)
            for frase in re.split(r"(?<=[.!?])\s+", " ".join(paragrafo.split()))
            if frase.strip()
        ]
        for frase in frases:
            tokens = {_stem_token(t) for t in tokenizar(frase)}
            if not tokens:
                continue
            score = len(q & tokens) / len(q)
            if score >= min_score:
                trechos.append(Trecho(fonte, frase.strip(), round(score, 3)))
    trechos.sort(key=lambda t: (-t.score, t.fonte, t.texto))
    return trechos[:top_k]


def refletir(estado: AgentState) -> AgentState:
    if len(estado.passos) > estado.max_passos:
        estado.status = "orcamento_excedido"
        estado.motivo = f"Passos {len(estado.passos)} > orçamento {estado.max_passos}"
        return estado
    if any(not passo.ok for passo in estado.passos):
        estado.status = "falhou"
        estado.motivo = "Uma ferramenta retornou erro"
        return estado
    usadas = set(estado.ferramentas_usadas)
    if "buscar_politicas" in usadas and not estado.evidencias and not estado.calculos:
        estado.status = "abstencao"
        estado.motivo = "Retrieval sem evidência"
        estado.resposta = "Não encontrei evidência suficiente no corpus para responder."
        return estado
    if "buscar_politicas" in usadas and estado.evidencias and "[" not in estado.resposta:
        estado.status = "falhou"
        estado.motivo = "Resposta de política sem citação"
        return estado
    if "calcular" in usadas and not estado.calculos:
        estado.status = "falhou"
        estado.motivo = "Cálculo solicitado, mas não produzido"
        return estado
    if estado.status == "novo":
        estado.status = "concluido" if estado.resposta else "abstencao"
    return estado


def executar_agente(pergunta: str, data_dir: Path, max_passos: int = 6) -> AgentState:
    estado = AgentState(pergunta=pergunta, max_passos=max_passos)
    if max_passos <= 0:
        estado.status = "orcamento_excedido"
        estado.motivo = "Orçamento inicial é zero"
        return estado

    estado.rota = classificar_rota(pergunta)
    if estado.rota == ("guardrail",):
        estado.passos.append(Passo("guardrail", pergunta, "bloqueado", True))
        estado.resposta = (
            "Não posso atender a pedidos que tentam ignorar regras ou expor dados sensíveis."
        )
        estado.status = "bloqueado"
        return estado
    if estado.rota == ("direct",):
        estado.passos.append(Passo("direct", pergunta, "saudação", True))
        estado.resposta = (
            "Sou um assistente de políticas internas. Posso consultar políticas, fazer cálculos "
            "simples e citar as fontes."
        )
        estado.status = "concluido"
        return estado
    if estado.rota == ("abstencao",):
        estado.resposta = "Não tenho uma ferramenta adequada para responder a essa pergunta."
        estado.status = "abstencao"
        return estado

    for ferramenta in estado.rota:
        if len(estado.passos) >= max_passos:
            estado.status = "orcamento_excedido"
            estado.motivo = f"Orçamento de {max_passos} passos esgotado"
            break
        if ferramenta == "buscar_politicas":
            trechos = buscar_politicas(pergunta, data_dir)
            estado.evidencias.extend(trechos)
            estado.passos.append(
                Passo(
                    "buscar_politicas",
                    pergunta,
                    f"{len(trechos)} trecho(s)",
                    True,
                )
            )
        elif ferramenta == "calcular":
            expressao = extrair_expressao(pergunta)
            if not expressao:
                estado.passos.append(Passo("calcular", pergunta, "sem expressão", False))
                continue
            try:
                calculo = calcular(expressao)
                estado.calculos.append(calculo)
                estado.passos.append(
                    Passo("calcular", expressao, f"={calculo.formatado}", True)
                )
            except ValueError as exc:
                estado.passos.append(Passo("calcular", expressao, str(exc), False))

    if estado.status in {"orcamento_excedido", "falhou"}:
        return refletir(estado)

    partes: list[str] = []
    for trecho in estado.evidencias[:2]:
        partes.append(f"[{trecho.fonte}] {trecho.texto}")
    tem_moeda = "R$" in pergunta or "r$" in pergunta
    for calculo in estado.calculos:
        prefixo = "R$ " if tem_moeda else ""
        partes.append(f"Cálculo: {calculo.expressao} = {prefixo}{calculo.formatado}.")
    if not partes:
        estado.resposta = "Não encontrei evidência suficiente no corpus para responder."
        estado.status = "abstencao"
    else:
        estado.resposta = " ".join(partes)
        estado.status = "concluido"
    return refletir(estado)
