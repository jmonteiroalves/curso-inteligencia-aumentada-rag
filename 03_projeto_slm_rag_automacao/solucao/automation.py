"""Referência funcional de automação com SOPs (módulo 03)."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

MUTANTES = {
    "criar_reembolso",
    "criar_solicitacao_compra",
    "criar_usuario",
    "conceder_acesso",
}
FERRAMENTAS_GLOBAIS = {"escalar_suporte"}
RISCOS = {"financeiro", "seguranca", "medio", "indefinido"}


@dataclass(frozen=True)
class Solicitacao:
    id: str
    texto: str
    intencao_esperada: str | None = None
    sop_esperado: str | None = None
    valor: float = 0.0


@dataclass(frozen=True)
class SOP:
    id: str
    titulo: str
    arquivo: str
    palavras_chave: tuple[str, ...]
    ferramentas: tuple[str, ...]
    limite_automatico: float
    risco: str
    passos: tuple[str, ...]


@dataclass(frozen=True)
class Classificacao:
    intencao: str
    confianca: float
    origem: str = "regras"


@dataclass(frozen=True)
class PlanoAcao:
    solicitacao_id: str
    intencao: str
    sop_id: str
    confianca: float
    passos: tuple[str, ...]
    ferramentas: tuple[str, ...]
    requer_aprovacao: bool
    motivo_aprovacao: str | None
    risco: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ResultadoSimulacao:
    solicitacao_id: str
    status: str
    eventos: tuple[str, ...]
    ferramenta_bloqueada: str | None = None
    sucesso: bool = False


def normalizar(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto.lower())
    return re.sub(r"[^a-z0-9\s]", " ", "".join(c for c in decomposto if not unicodedata.combining(c)))


def carregar_sops(data_dir: Path) -> dict[str, SOP]:
    dados = json.loads((data_dir / "sops.json").read_text(encoding="utf-8"))
    itens = [*dados["intencoes"], dados["fallback"]]
    return {
        item["id"]: SOP(
            id=item["id"],
            titulo=item["titulo"],
            arquivo=item["sop"],
            palavras_chave=tuple(item["palavras_chave"]),
            ferramentas=tuple(item["ferramentas"]),
            limite_automatico=float(item["limite_automatico"]),
            risco=item["risco"],
            passos=tuple(item["passos"]),
        )
        for item in itens
    }


def carregar_solicitacoes(data_dir: Path) -> list[Solicitacao]:
    brutos = json.loads((data_dir / "solicitacoes.json").read_text(encoding="utf-8"))
    return [
        Solicitacao(
            id=item["id"],
            texto=item["texto"],
            intencao_esperada=item.get("intencao_esperada"),
            sop_esperado=item.get("sop_esperado"),
            valor=float(item.get("valor", 0.0)),
        )
        for item in brutos
    ]


def _extrair_valor(texto: str) -> float:
    match = re.search(
        r"r\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\d+(?:[.,]\d{1,2})?)",
        texto,
        re.IGNORECASE,
    )
    if not match:
        return 0.0
    bruto = match.group(1)
    if "," in bruto:
        return float(bruto.replace(".", "").replace(",", "."))
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", bruto):
        return float(bruto.replace(".", ""))
    return float(bruto)


def _score_texto(texto_norm: str, palavras: tuple[str, ...]) -> int:
    return sum(1 for palavra in palavras if normalizar(palavra) in texto_norm)


def classificar(solicitacao: Solicitacao, sops: dict[str, SOP]) -> Classificacao:
    texto_norm = normalizar(solicitacao.texto)
    scores = {
        sid: _score_texto(texto_norm, sop.palavras_chave)
        for sid, sop in sops.items()
        if sid != "desconhecido"
    }
    melhor = max(scores.values(), default=0)
    vencedores = [sid for sid, score in scores.items() if score == melhor]
    if melhor == 0 or len(vencedores) > 1:
        return Classificacao("desconhecido", 0.0)
    sid = vencedores[0]
    total = max(1, min(3, len(sops[sid].palavras_chave)))
    return Classificacao(sid, round(min(1.0, melhor / total), 2))


def recuperar_sop(texto: str, sops: dict[str, SOP]) -> tuple[SOP, float]:
    texto_norm = normalizar(texto)
    tokens = set(texto_norm.split())
    scores: list[tuple[float, str]] = []
    for sid, sop in sops.items():
        if sid == "desconhecido":
            continue
        score = 3.0 * _score_texto(texto_norm, sop.palavras_chave)
        score += len(tokens & set(normalizar(" ".join(sop.passos)).split()))
        scores.append((score, sid))
    scores.sort(key=lambda item: (-item[0], item[1]))
    if not scores or scores[0][0] == 0:
        return sops["desconhecido"], 0.0
    score_max = scores[0][0]
    return sops[scores[0][1]], round(score_max / (score_max + 1), 2)


def montar_plano(solicitacao: Solicitacao, classificacao: Classificacao, sop: SOP) -> PlanoAcao:
    valor = max(solicitacao.valor, _extrair_valor(solicitacao.texto))
    aprovacao = sop.limite_automatico > 0 and valor > sop.limite_automatico
    if sop.id == "reembolso":
        ferramentas = ["validar_despesa"]
        ferramentas.append("escalar_gestor" if aprovacao else "criar_reembolso")
    elif sop.id == "compra":
        ferramentas = ["validar_orcamento"]
        ferramentas.append("escalar_gestor" if aprovacao else "criar_solicitacao_compra")
    elif sop.id == "onboarding":
        ferramentas = ["criar_usuario", "agendar_onboarding"]
    elif sop.id == "acesso":
        ferramentas = ["verificar_identidade", "conceder_acesso"]
    else:
        ferramentas = ["escalar_suporte"]
        aprovacao = False

    motivo = (
        f"Valor R$ {valor:.2f} acima do limite automático de R$ {sop.limite_automatico:.2f}"
        if aprovacao
        else None
    )
    return PlanoAcao(
        solicitacao_id=solicitacao.id,
        intencao=sop.id,
        sop_id=sop.arquivo,
        confianca=classificacao.confianca,
        passos=sop.passos,
        ferramentas=tuple(ferramentas),
        requer_aprovacao=aprovacao,
        motivo_aprovacao=motivo,
        risco=sop.risco,
    )


def validar_plano(plano: PlanoAcao, sops: dict[str, SOP]) -> None:
    if plano.intencao not in sops:
        raise ValueError(f"Intenção desconhecida: {plano.intencao}")
    sop = sops[plano.intencao]
    permitidas = set(sop.ferramentas) | FERRAMENTAS_GLOBAIS
    invalidas = set(plano.ferramentas) - permitidas
    if invalidas:
        raise ValueError(f"Ferramenta(s) não permitida(s): {sorted(invalidas)}")
    if not plano.ferramentas:
        raise ValueError("Plano sem ferramentas")
    if len(set(plano.ferramentas)) != len(plano.ferramentas):
        raise ValueError("Ferramenta duplicada no plano")
    if not plano.passos or any(not passo.strip() for passo in plano.passos):
        raise ValueError("Passo vazio")
    if len(set(plano.passos)) != len(plano.passos):
        raise ValueError("Passo duplicado")
    if plano.risco not in RISCOS:
        raise ValueError(f"Risco inválido: {plano.risco}")
    if plano.requer_aprovacao and not plano.motivo_aprovacao:
        raise ValueError("Aprovação exigida sem justificativa")


def simular(plano: PlanoAcao, solicitacao: Solicitacao) -> ResultadoSimulacao:
    eventos: list[str] = []
    for ferramenta in plano.ferramentas:
        if plano.requer_aprovacao and ferramenta in MUTANTES:
            eventos.append(f"{ferramenta}: bloqueada, aprovação necessária")
            return ResultadoSimulacao(
                solicitacao.id, "aguardando_aprovacao", tuple(eventos), ferramenta, False
            )
        if ferramenta == "escalar_gestor":
            eventos.append("escalar_gestor: aprovação pendente")
            return ResultadoSimulacao(
                solicitacao.id, "aguardando_aprovacao", tuple(eventos), None, False
            )
        if ferramenta == "escalar_suporte":
            eventos.append("escalar_suporte: encaminhado para humano")
            return ResultadoSimulacao(solicitacao.id, "escalado", tuple(eventos), None, False)
        eventos.append(f"{ferramenta}: ok")
    return ResultadoSimulacao(solicitacao.id, "concluido", tuple(eventos), None, True)


def executar(solicitacao: Solicitacao, sops: dict[str, SOP]) -> tuple[PlanoAcao, ResultadoSimulacao]:
    classificacao = classificar(solicitacao, sops)
    sop, _ = recuperar_sop(solicitacao.texto, sops)
    if classificacao.intencao != "desconhecido":
        sop = sops[classificacao.intencao]
    plano = montar_plano(solicitacao, classificacao, sop)
    validar_plano(plano, sops)
    return plano, simular(plano, solicitacao)
