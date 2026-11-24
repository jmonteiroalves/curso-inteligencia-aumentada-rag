"""Referência funcional do assistente de RH (módulo 04)."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

ATRIBUTOS_PROIBIDOS = {
    "nome", "email", "telefone", "genero", "idade", "faixa_etaria", "raca", "religiao",
    "estado_civil", "deficiencia", "foto", "endereco",
}
TERMOS_PROIBIDOS_CRITERIO = {
    "genero", "idade", "raca", "religiao", "deficiencia", "estado civil", "orientacao",
}
CAMPOS_ANONIMOS = (
    "id", "resumo", "habilidades", "anos_experiencia", "senioridade", "formacao",
    "certificacoes", "idiomas", "disponibilidade",
)


@dataclass(frozen=True)
class Criterio:
    id: str
    nome: str
    peso: float
    termos: tuple[str, ...]
    obrigatorio: bool = False


@dataclass(frozen=True)
class Vaga:
    id: str
    titulo: str
    senioridade: str
    anos_minimos: int
    resumo: str
    criterios: tuple[Criterio, ...]
    diferenciais: tuple[str, ...]


@dataclass(frozen=True)
class CandidatoAnonimizado:
    id: str
    resumo: str
    habilidades: dict[str, int]
    anos_experiencia: int
    senioridade: str
    formacao: str
    certificacoes: tuple[str, ...]
    idiomas: dict[str, str]
    disponibilidade: str


@dataclass(frozen=True)
class Evidencia:
    criterio: str
    peso: float
    score: float
    evidencia: str
    lacuna: bool


@dataclass(frozen=True)
class ResultadoMatching:
    candidato_id: str
    score: float
    evidencias: tuple[Evidencia, ...]
    lacunas: tuple[str, ...]


@dataclass(frozen=True)
class PerguntaEntrevista:
    criterio: str
    pergunta: str
    tipo: str


def normalizar(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto.lower())
    return re.sub(r"[^a-z0-9\s]", " ", "".join(c for c in decomposto if not unicodedata.combining(c)))


def carregar_vaga(caminho: Path) -> Vaga:
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    return Vaga(
        id=dados["id"],
        titulo=dados["titulo"],
        senioridade=dados["senioridade"],
        anos_minimos=int(dados["anos_minimos"]),
        resumo=dados["resumo"],
        criterios=tuple(
            Criterio(
                c["id"], c["nome"], float(c["peso"]), tuple(c["termos"]), c.get("obrigatorio", False)
            )
            for c in dados["criterios"]
        ),
        diferenciais=tuple(dados.get("diferenciais", [])),
    )


def carregar_candidatos(caminho: Path) -> list[dict[str, object]]:
    return json.loads(caminho.read_text(encoding="utf-8"))


def anonimizar_candidato(bruto: dict[str, object]) -> CandidatoAnonimizado:
    faltando = [campo for campo in CAMPOS_ANONIMOS if campo not in bruto]
    if faltando:
        raise ValueError(f"Campos obrigatórios ausentes: {faltando}")
    return CandidatoAnonimizado(
        id=str(bruto["id"]),
        resumo=str(bruto["resumo"]),
        habilidades={str(k): int(v) for k, v in dict(bruto["habilidades"]).items()},
        anos_experiencia=int(bruto["anos_experiencia"]),
        senioridade=str(bruto["senioridade"]),
        formacao=str(bruto["formacao"]),
        certificacoes=tuple(str(x) for x in bruto["certificacoes"]),
        idiomas={str(k): str(v) for k, v in dict(bruto["idiomas"]).items()},
        disponibilidade=str(bruto["disponibilidade"]),
    )


def validar_vaga(vaga: Vaga) -> None:
    if len(vaga.criterios) < 5:
        raise ValueError("A vaga precisa de pelo menos 5 critérios")
    if any(c.peso <= 0 for c in vaga.criterios):
        raise ValueError("Todo peso deve ser positivo")
    soma = sum(c.peso for c in vaga.criterios)
    if abs(soma - 1.0) > 1e-6:
        raise ValueError(f"Pesos devem somar 1.0; soma atual={soma}")
    for criterio in vaga.criterios:
        texto = normalizar(criterio.nome + " " + " ".join(criterio.termos))
        if any(re.search(rf"\b{re.escape(termo)}\b", texto) for termo in TERMOS_PROIBIDOS_CRITERIO):
            raise ValueError(f"Critério usa atributo protegido: {criterio.nome}")
    if vaga.anos_minimos < 0:
        raise ValueError("anos_minimos inválido")


def _texto_candidato(candidato: CandidatoAnonimizado) -> str:
    partes = [
        candidato.resumo,
        *candidato.habilidades.keys(),
        *candidato.certificacoes,
        candidato.formacao,
        *candidato.idiomas.keys(),
        *candidato.idiomas.values(),
    ]
    return normalizar(" ".join(partes))


def _nivel_idioma(candidato: CandidatoAnonimizado) -> float:
    idioma = normalizar(candidato.idiomas.get("Inglês", ""))
    if "fluente" in idioma or "avancado" in idioma:
        return 1.0
    if "intermediario" in idioma:
        return 0.6
    if "basico" in idioma:
        return 0.25
    return 0.0


def _trecho(candidato: CandidatoAnonimizado, termo: str) -> str:
    for frase in re.split(r"(?<=[.!?])\s+", candidato.resumo.replace("\n", " ")):
        if normalizar(termo) in normalizar(frase):
            return frase.strip()
    return ""


def _avaliar_criterio(
    candidato: CandidatoAnonimizado, criterio: Criterio
) -> tuple[float, str]:
    texto = _texto_candidato(candidato)
    if criterio.id == "experiencia":
        return 0.0, f"{candidato.anos_experiencia} anos de experiência declarados"

    if criterio.id == "ingles":
        nivel = _nivel_idioma(candidato)
        score = nivel if nivel else (1.0 if "ingles" in texto else 0.0)
        idioma = candidato.idiomas.get("Inglês", "não informado")
        return score, f"Inglês: {idioma}"

    encontrados = [termo for termo in criterio.termos if normalizar(termo) in texto]
    cobertura = len(encontrados) / max(1, len(criterio.termos))
    niveis: list[float] = []
    habilidades: list[str] = []
    for chave, valor in candidato.habilidades.items():
        chave_norm = normalizar(chave)
        if any(chave_norm in normalizar(t) or normalizar(t) in chave_norm for t in encontrados):
            niveis.append(valor / 5)
            habilidades.append(f"{chave} nível {valor}/5")
    if not niveis and encontrados:
        niveis = [0.6]
    nivel = sum(niveis) / len(niveis) if niveis else 0.0
    score = 0.6 * cobertura + 0.4 * nivel if encontrados else 0.0

    trechos = []
    for termo in encontrados[:2]:
        trecho = _trecho(candidato, termo)
        if trecho and trecho not in trechos:
            trechos.append(trecho)
    evidencia = " | ".join(trechos) if trechos else "; ".join(habilidades)
    if not evidencia:
        evidencia = "Sem evidência observável no currículo anonimizado"
    return min(1.0, score), evidencia


def pontuar_candidato(candidato: CandidatoAnonimizado, vaga: Vaga) -> ResultadoMatching:
    evidencias: list[Evidencia] = []
    lacunas: list[str] = []
    total = 0.0
    for criterio in vaga.criterios:
        if criterio.id == "experiencia":
            score = min(1.0, candidato.anos_experiencia / max(1, vaga.anos_minimos))
            texto = f"{candidato.anos_experiencia} anos; mínimo exigido: {vaga.anos_minimos}"
        else:
            score, texto = _avaliar_criterio(candidato, criterio)
        lacuna = score < 0.5
        if lacuna:
            lacunas.append(criterio.nome)
        total += criterio.peso * score
        evidencias.append(
            Evidencia(
                criterio=criterio.nome,
                peso=criterio.peso,
                score=round(score, 3),
                evidencia=texto[:300],
                lacuna=lacuna,
            )
        )
    return ResultadoMatching(
        candidato_id=candidato.id,
        score=round(100 * total, 1),
        evidencias=tuple(evidencias),
        lacunas=tuple(lacunas),
    )


def ranking(candidatos: list[CandidatoAnonimizado], vaga: Vaga) -> list[ResultadoMatching]:
    resultados = [pontuar_candidato(c, vaga) for c in candidatos]
    return sorted(resultados, key=lambda r: (-r.score, r.candidato_id))


def gerar_perguntas(resultado: ResultadoMatching, vaga: Vaga) -> list[PerguntaEntrevista]:
    scores = {e.criterio: e.score for e in resultado.evidencias}
    nomes = {c.nome: c for c in vaga.criterios}
    por_peso = sorted(vaga.criterios, key=lambda c: (-c.peso, c.nome))
    por_lacuna = sorted(
        (c for c in vaga.criterios if scores.get(c.nome, 0) < 0.6),
        key=lambda c: (scores.get(c.nome, 0), -c.peso),
    )
    selecionados: list[tuple[Criterio, str]] = []
    vistos: set[str] = set()
    for criterio in por_peso[:3]:
        if criterio.nome not in vistos:
            selecionados.append((criterio, "evidencia"))
            vistos.add(criterio.nome)
    for criterio in por_lacuna:
        if len(selecionados) >= 5:
            break
        if criterio.nome not in vistos:
            selecionados.append((criterio, "lacuna"))
            vistos.add(criterio.nome)
    for criterio in por_peso:
        if len(selecionados) >= 5:
            break
        if criterio.nome not in vistos:
            selecionados.append((criterio, "evidencia"))
            vistos.add(criterio.nome)

    perguntas = []
    for criterio, tipo in selecionados[:5]:
        if tipo == "lacuna":
            pergunta = (
                f"Seu currículo tem pouca evidência em {criterio.nome}. "
                "Como você lidaria com uma demanda real nessa área e o que faria para se preparar?"
            )
        else:
            pergunta = (
                f"Conte uma situação concreta em que você aplicou {criterio.nome}. "
                "Qual era o contexto, qual foi sua ação e qual resultado mensurável você obteve?"
            )
        perguntas.append(PerguntaEntrevista(criterio.nome, pergunta, tipo))
    return perguntas


def auditar_vies(
    ranking_resultados: list[ResultadoMatching],
    candidatos_brutos: list[dict[str, object]],
    top_n: int = 2,
) -> dict[str, object]:
    selecionados = {r.candidato_id for r in ranking_resultados[:top_n]}
    relatorio: dict[str, object] = {
        "metodo": "auditoria descritiva; não altera ranking",
        "top_n": top_n,
    }
    for campo in ("genero", "faixa_etaria"):
        grupos: dict[str, dict[str, object]] = defaultdict(
            lambda: {"total": 0, "selecionados": 0, "taxa": 0.0}
        )
        for candidato in candidatos_brutos:
            grupo = str(candidato.get(campo, "não informado"))
            grupos[grupo]["total"] = int(grupos[grupo]["total"]) + 1
            if str(candidato["id"]) in selecionados:
                grupos[grupo]["selecionados"] = int(grupos[grupo]["selecionados"]) + 1
        for dados in grupos.values():
            dados["taxa"] = round(int(dados["selecionados"]) / max(1, int(dados["total"])), 3)
        relatorio[campo] = dict(sorted(grupos.items()))
    return relatorio


def como_dict(resultado: ResultadoMatching) -> dict[str, object]:
    return asdict(resultado)
