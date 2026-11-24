"""Classificação + RAG de SOPs + plano de automação — esqueleto (módulo 03).

O classificador pode ser um SLM local ou regras determinísticas. Neste curso, a
solução de referência usa regras para que tudo rode offline; o adaptador Ollama é
uma extensão. A regra mais importante: nenhum plano executa ferramenta não prevista
no SOP, e ações mutantes exigem aprovação quando o valor ultrapassa o limite.
"""

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
    """Carrega intenções e fallback. Retorna um dict por id de intenção."""
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


def classificar(solicitacao: Solicitacao, sops: dict[str, SOP]) -> Classificacao:
    """Classifica a intenção com confiança e fallback seguro.

    TODO(3.2):
    - normalize texto e palavras-chave;
    - pontue correspondências únicas por intenção;
    - confiança = matches / min(3, total de palavras-chave), limitada a 1;
    - se o melhor score for 0, retorne `desconhecido` com confiança 0;
    - considere empate como baixa confiança (fallback).
    """
    # TODO(3.2): implemente classificar
    raise NotImplementedError("TODO(3.2): implemente classificar")


def recuperar_sop(texto: str, sops: dict[str, SOP]) -> tuple[SOP, float]:
    """Recupera o SOP por ranking lexical.

    TODO(3.3): use tokens/palavras-chave do texto e o conteúdo dos passos.
    Retorne sempre o fallback se todos os scores forem zero.
    """
    # TODO(3.3): implemente recuperar_sop
    raise NotImplementedError("TODO(3.3): implemente recuperar_sop")


def montar_plano(solicitacao: Solicitacao, classificacao: Classificacao, sop: SOP) -> PlanoAcao:
    """Monta o plano JSON conforme SOP, valor e política de aprovação.

    TODO(3.4):
    - valor = máximo entre o campo e o R$ extraído do texto;
    - requer aprovação se limite_automatico > 0 e valor > limite;
    - selecione ferramentas do SOP na ordem segura (validação antes de mutação);
    - para `desconhecido`, use apenas `escalar_suporte`;
    - preencha motivo_aprovacao quando necessário.
    """
    # TODO(3.4): implemente montar_plano
    raise NotImplementedError("TODO(3.4): implemente montar_plano")


def validar_plano(plano: PlanoAcao, sops: dict[str, SOP]) -> None:
    """Valida o contrato do plano; levanta ValueError se inválido.

    TODO(3.4): valide:
    - intenção/SOP existentes (ou fallback);
    - ferramentas ⊆ SOP.ferramentas ∪ FERRAMENTAS_GLOBAIS;
    - passos não vazios e sem duplicatas;
    - risco conhecido;
    - aprovação com motivo.
    """
    # TODO(3.4): implemente validar_plano
    raise NotImplementedError("TODO(3.4): implemente validar_plano")


def simular(plano: PlanoAcao, solicitacao: Solicitacao) -> ResultadoSimulacao:
    """Simula a execução das ferramentas.

    TODO(3.5):
    - execute leituras normalmente;
    - se requer_aprovacao, bloqueie a primeira ferramenta mutante;
    - `escalar_gestor`/`escalar_suporte` encerram como pendente/escalado;
    - retorne eventos legíveis e `sucesso=True` somente em conclusão segura.
    """
    # TODO(3.5): implemente simular
    raise NotImplementedError("TODO(3.5): implemente simular")


def executar(solicitacao: Solicitacao, sops: dict[str, SOP]) -> tuple[PlanoAcao, ResultadoSimulacao]:
    """Orquestra classificação → retrieval → plano → validação → simulação."""
    classificacao = classificar(solicitacao, sops)
    sop, _ = recuperar_sop(solicitacao.texto, sops)
    plano = montar_plano(solicitacao, classificacao, sop)
    validar_plano(plano, sops)
    return plano, simular(plano, solicitacao)
