"""Fluxo contábil multimodal — esqueleto do aluno (módulo 08).

FONTES
------
- Imagem/PDF da nota (fonte primária)
- Sidecar `notas.json` (texto esperado do OCR, para execução offline)
- Razão CSV (lançamentos)
- DRE CSV (demonstrativo)
- Políticas e contratos Markdown (RAG)

REGRA
-----
O agente nunca paga. Divergência ou valor acima da alçada vai para revisão humana.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

TOLERANCIA = 0.01
LIMITE_APROVACAO = 1000.0


@dataclass(frozen=True)
class ItemNota:
    descricao: str
    quantidade: float
    preco_unitario: float
    subtotal: float


@dataclass(frozen=True)
class NotaBruta:
    arquivo: str
    caminho: Path
    checksum: str
    dados: dict[str, Any]


@dataclass(frozen=True)
class NotaFiscal:
    arquivo: str
    numero: str
    fornecedor: str
    cnpj: str
    data: str
    categoria: str
    itens: tuple[ItemNota, ...]
    total: float
    imposto: float
    moeda: str
    texto_ocr: str
    checksum: str


@dataclass(frozen=True)
class Lancamento:
    id: str
    data: str
    fornecedor: str
    documento: str
    valor: float
    status: str
    centro_custo: str


@dataclass(frozen=True)
class Divergencia:
    tipo: str
    severidade: str
    descricao: str
    valor: float = 0.0


@dataclass(frozen=True)
class ValidacaoNota:
    numero: str
    status: str
    total_itens: float
    total_informado: float
    divergencias: tuple[Divergencia, ...]
    requer_aprovacao: bool
    motivo_aprovacao: str | None
    lancamentos: tuple[Lancamento, ...]


@dataclass(frozen=True)
class RespostaConsulta:
    pergunta: str
    resposta: str
    fontes: tuple[str, ...]
    absteve: bool = False


@dataclass(frozen=True)
class WorkflowResult:
    notas: tuple[NotaFiscal, ...]
    validacoes: tuple[ValidacaoNota, ...]
    status: str
    aprovacoes_necessarias: int
    total_divergencias: int
    relatorio: str
    trilha: tuple[str, ...]
    consultas: tuple[RespostaConsulta, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def normalizar(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto.lower())
    return re.sub(r"[^a-z0-9\s]", " ", "".join(c for c in decomposto if not unicodedata.combining(c)))


def formatar_moeda(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def carregar_sidecar(data_dir: Path) -> list[dict[str, Any]]:
    return json.loads((data_dir / "notas_fiscais" / "notas.json").read_text(encoding="utf-8"))


def carregar_lancamentos(data_dir: Path) -> list[Lancamento]:
    with (data_dir / "razao.csv").open(encoding="utf-8", newline="") as arquivo:
        return [
            Lancamento(
                id=linha["lancamento_id"],
                data=linha["data"],
                fornecedor=linha["fornecedor"],
                documento=linha["documento"],
                valor=float(linha["valor"]),
                status=linha["status"],
                centro_custo=linha["centro_custo"],
            )
            for linha in csv.DictReader(arquivo)
        ]


def carregar_dre(data_dir: Path) -> list[dict[str, str]]:
    with (data_dir / "demonstrativos" / "dre_2026.csv").open(encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def ingerir_notas(data_dir: Path) -> list[NotaBruta]:
    """TODO(8.1): carregue o sidecar, localize PNG/PDF e calcule SHA-256.

    Marque a fonte e o checksum; a imagem é a evidência primária.
    """
    # TODO(8.1): implemente ingerir_notas
    raise NotImplementedError("TODO(8.1): implemente ingerir_notas")


def extrair_nota(bruta: NotaBruta) -> NotaFiscal:
    """TODO(8.2): valide campos obrigatórios e converta itens/total.

    O sidecar simula OCR. Em produção, use visão/OCR e mantenha o sidecar como
    gabarito de avaliação — nunca como fonte de verdade silenciosa.
    """
    # TODO(8.2): implemente extrair_nota
    raise NotImplementedError("TODO(8.2): implemente extrair_nota")


def validar_nota(nota: NotaFiscal, lancamentos: list[Lancamento]) -> ValidacaoNota:
    """TODO(8.3): valide itens, total, imposto, razão e duplicidade.

    - soma dos subtotais + imposto vs total;
    - lançamentos por documento (0, 1 ou >1);
    - valor do razão vs nota;
    - alçada > R$ 1.000 e divergências.
    """
    # TODO(8.3): implemente validar_nota
    raise NotImplementedError("TODO(8.3): implemente validar_nota")


def consultar_contabil(pergunta: str, data_dir: Path) -> RespostaConsulta:
    """TODO(8.4): responda com DRE ou trechos de política/contrato, sempre citando.

    Exemplo: receita de março → linha `2026-03` de `dre_2026.csv`.
    """
    # TODO(8.4): implemente consultar_contabil
    raise NotImplementedError("TODO(8.4): implemente consultar_contabil")


def executar_workflow(data_dir: Path) -> WorkflowResult:
    """TODO(8.5): ingira → extraia → valide → recupere → revise → reporte.

    O status global é `revisao_humana` se houver divergência ou aprovação pendente.
    """
    # TODO(8.5): implemente executar_workflow
    raise NotImplementedError("TODO(8.5): implemente executar_workflow")


def gerar_relatorio(
    notas: tuple[NotaFiscal, ...] | list[NotaFiscal],
    validacoes: tuple[ValidacaoNota, ...] | list[ValidacaoNota],
    status: str,
    aprovacoes_necessarias: int,
    trilha: tuple[str, ...] | list[str],
    consultas: tuple[RespostaConsulta, ...] | list[RespostaConsulta] = (),
) -> str:
    """TODO(8.6): gere Markdown com resumo, tabela, divergências, consultas e trilha."""
    # TODO(8.6): implemente gerar_relatorio
    raise NotImplementedError("TODO(8.6): implemente gerar_relatorio")
