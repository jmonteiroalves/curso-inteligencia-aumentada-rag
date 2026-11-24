"""Assistente de RH com matching explicável — esqueleto (módulo 04).

PRINCÍPIOS
----------
1. Atributos protegidos (gênero, idade, raça, religião etc.) não entram no score.
2. O sistema produz evidências e perguntas; a decisão final é humana.
3. A auditoria de viés é um farol, não um ajuste automático de ranking.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
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
    """Cria a visão usada pelo matching, somente com campos permitidos.

    TODO(4.1): use uma whitelist (CAMPOS_ANONIMOS), não uma blacklist.
    Normalize tipos e garanta que nenhum atributo protegido vaze.
    """
    # TODO(4.1): implemente anonimizar_candidato
    raise NotImplementedError("TODO(4.1): implemente anonimizar_candidato")


def validar_vaga(vaga: Vaga) -> None:
    """Valida critérios e pesos.

    TODO(4.2):
    - pelo menos 5 critérios;
    - todos os pesos > 0 e soma ≈ 1,0;
    - nomes/termos não podem conter atributos protegidos.
    """
    # TODO(4.2): implemente validar_vaga
    raise NotImplementedError("TODO(4.2): implemente validar_vaga")


def pontuar_candidato(
    candidato: CandidatoAnonimizado, vaga: Vaga
) -> ResultadoMatching:
    """Calcula score 0–100 com evidências por critério.

    TODO(4.3/4.4): para cada critério:
    - cobertura = termos encontrados / termos;
    - nível = média das habilidades encontradas (1–5);
    - combine cobertura e nível; trate `experiencia` por anos;
    - registre trecho/fonte em `Evidencia`;
    - marque lacunas quando o score do critério for baixo.
    """
    # TODO(4.3): implemente pontuar_candidato
    raise NotImplementedError("TODO(4.3): implemente pontuar_candidato")


def ranking(candidatos: list[CandidatoAnonimizado], vaga: Vaga) -> list[ResultadoMatching]:
    """Ordena por score desc, com desempate estável por id."""
    resultados = [pontuar_candidato(c, vaga) for c in candidatos]
    return sorted(resultados, key=lambda r: (-r.score, r.candidato_id))


def gerar_perguntas(resultado: ResultadoMatching, vaga: Vaga) -> list[PerguntaEntrevista]:
    """Gera exatamente 5 perguntas ligadas a critérios.

    TODO(4.5): combine os critérios de maior peso (evidência) e os de menor score
    (lacuna). Nunca pergunte gênero, idade, estado civil, religião ou deficiência.
    """
    # TODO(4.5): implemente gerar_perguntas
    raise NotImplementedError("TODO(4.5): implemente gerar_perguntas")


def auditar_vies(
    ranking_resultados: list[ResultadoMatching],
    candidatos_brutos: list[dict[str, object]],
    top_n: int = 2,
) -> dict[str, object]:
    """Calcula taxa de seleção por grupo sintético.

    TODO(4.6): monte um relatório por `genero` e `faixa_etaria`, com total,
    selecionados e taxa. Não altere o score nem selecione por cota.
    """
    # TODO(4.6): implemente auditar_vies
    raise NotImplementedError("TODO(4.6): implemente auditar_vies")
