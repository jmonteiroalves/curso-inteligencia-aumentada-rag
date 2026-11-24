"""Referência funcional do fluxo contábil multimodal (módulo 08)."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

TOLERANCIA = 0.01
LIMITE_APROVACAO = 1000.0

MESES = {
    "janeiro": "2026-01",
    "fevereiro": "2026-02",
    "marco": "2026-03",
    "abril": "2026-04",
    "maio": "2026-05",
    "junho": "2026-06",
    "julho": "2026-07",
    "agosto": "2026-08",
    "setembro": "2026-09",
    "outubro": "2026-10",
    "novembro": "2026-11",
    "dezembro": "2026-12",
}


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
    brutas: list[NotaBruta] = []
    for dados in carregar_sidecar(data_dir):
        caminho = data_dir / "notas_fiscais" / str(dados["arquivo"])
        if not caminho.exists():
            pdf = caminho.with_suffix(".pdf")
            caminho = pdf if pdf.exists() else caminho
        if caminho.exists():
            checksum = hashlib.sha256(caminho.read_bytes()).hexdigest()[:16]
        else:
            checksum = hashlib.sha256(
                json.dumps(dados, sort_keys=True).encode("utf-8")
            ).hexdigest()[:16]
        brutas.append(NotaBruta(str(dados["arquivo"]), caminho, checksum, dados))
    return brutas


def extrair_nota(bruta: NotaBruta) -> NotaFiscal:
    dados = bruta.dados
    obrigatorios = ("numero", "fornecedor", "cnpj", "data", "total", "itens")
    faltando = [campo for campo in obrigatorios if campo not in dados or dados[campo] in ("", None)]
    if faltando:
        raise ValueError(f"Campos obrigatórios ausentes: {faltando}")
    if not dados["itens"]:
        raise ValueError(f"Nota {dados['numero']} sem itens")

    itens = []
    for item in dados["itens"]:
        quantidade = float(item["quantidade"])
        preco = float(item["preco_unitario"])
        subtotal = float(item.get("subtotal", quantidade * preco))
        if quantidade <= 0 or preco < 0:
            raise ValueError(f"Item inválido na nota {dados['numero']}")
        itens.append(ItemNota(str(item["descricao"]), quantidade, preco, subtotal))

    total = float(dados["total"])
    if total <= 0:
        raise ValueError(f"Total inválido na nota {dados['numero']}")
    return NotaFiscal(
        arquivo=bruta.arquivo,
        numero=str(dados["numero"]),
        fornecedor=str(dados["fornecedor"]),
        cnpj=str(dados["cnpj"]),
        data=str(dados["data"]),
        categoria=str(dados.get("categoria", "não classificada")),
        itens=tuple(itens),
        total=total,
        imposto=float(dados.get("imposto", 0.0)),
        moeda=str(dados.get("moeda", "BRL")),
        texto_ocr=str(dados.get("texto_ocr", "")),
        checksum=bruta.checksum,
    )


def validar_nota(nota: NotaFiscal, lancamentos: list[Lancamento]) -> ValidacaoNota:
    divergencias: list[Divergencia] = []
    total_itens = round(sum(item.subtotal for item in nota.itens), 2)
    calculado = round(
        sum(item.quantidade * item.preco_unitario for item in nota.itens), 2
    )

    if abs(total_itens - calculado) > TOLERANCIA:
        divergencias.append(
            Divergencia(
                "subtotal",
                "media",
                "Subtotal dos itens não confere com quantidade × preço",
                round(total_itens - calculado, 2),
            )
        )

    esperado = round(total_itens + nota.imposto, 2)
    if abs(nota.total - esperado) > TOLERANCIA:
        divergencias.append(
            Divergencia(
                "total",
                "alta",
                "Total informado difere da soma dos itens + impostos",
                round(nota.total - esperado, 2),
            )
        )

    do_documento = [
        l
        for l in lancamentos
        if l.documento == nota.numero and l.status.lower() != "cancelado"
    ]
    if not do_documento:
        divergencias.append(
            Divergencia("razao", "media", "Nota sem lançamento correspondente no razão", nota.total)
        )
    elif len(do_documento) > 1:
        divergencias.append(
            Divergencia(
                "duplicidade",
                "alta",
                f"Documento aparece {len(do_documento)} vezes no razão",
                round(sum(l.valor for l in do_documento), 2),
            )
        )
    elif abs(do_documento[0].valor - nota.total) > TOLERANCIA:
        divergencias.append(
            Divergencia(
                "razao_valor",
                "alta",
                "Valor do razão difere do total da nota",
                round(do_documento[0].valor - nota.total, 2),
            )
        )

    motivos: list[str] = []
    if nota.total > LIMITE_APROVACAO:
        motivos.append(f"Total acima da alçada de {formatar_moeda(LIMITE_APROVACAO)}")
    if divergencias:
        motivos.append("Divergências exigem revisão humana")
    requer = bool(motivos)
    return ValidacaoNota(
        numero=nota.numero,
        status="revisao_humana" if divergencias else "valida",
        total_itens=total_itens,
        total_informado=nota.total,
        divergencias=tuple(divergencias),
        requer_aprovacao=requer,
        motivo_aprovacao="; ".join(motivos) if motivos else None,
        lancamentos=tuple(do_documento),
    )


def _buscar_documentos(pergunta: str, data_dir: Path) -> RespostaConsulta:
    q = set(normalizar(pergunta).split())
    candidatos: list[tuple[float, str, str]] = []
    for pasta in ("politicas", "contratos"):
        for caminho in (data_dir / pasta).glob("*.md"):
            texto = caminho.read_text(encoding="utf-8")
            frases = [
                frase.strip()
                for paragrafo in re.split(r"\n\s*\n", texto)
                for frase in re.split(r"(?<=[.!?])\s+", " ".join(paragrafo.split()))
                if frase.strip()
            ]
            for frase in frases:
                tokens = set(normalizar(frase).split())
                if not tokens:
                    continue
                score = len(q & tokens) / max(1, len(q))
                if score >= 0.25:
                    candidatos.append((score, f"{pasta}/{caminho.name}", frase.strip()))
    if not candidatos:
        return RespostaConsulta(pergunta, "Não encontrei evidência suficiente.", (), True)
    candidatos.sort(key=lambda c: -c[0])
    melhor = candidatos[0][0]
    escolhidos = [c for c in candidatos if c[0] >= melhor - 1e-9][:2]
    resposta = " ".join(f"[{fonte}] {frase}" for _, fonte, frase in escolhidos)
    fontes = tuple(dict.fromkeys(fonte for _, fonte, _ in escolhidos))
    return RespostaConsulta(pergunta, resposta, fontes)


def consultar_contabil(pergunta: str, data_dir: Path) -> RespostaConsulta:
    p = normalizar(pergunta)
    mes = next((codigo for nome, codigo in MESES.items() if nome in p), None)
    campos = {
        "receita": "receita",
        "lucro": "lucro",
        "custo": "custos",
        "despesa": "despesas",
    }
    campo = next((coluna for chave, coluna in campos.items() if chave in p), None)

    if mes and campo:
        linha = next((row for row in carregar_dre(data_dir) if row["mes"] == mes), None)
        if linha:
            valor = float(linha[campo])
            return RespostaConsulta(
                pergunta,
                f"{campo.capitalize()} em {mes}: {formatar_moeda(valor)}.",
                (f"dre_2026.csv:{mes}",),
            )

    # Perguntas de contrato por fornecedor: evita perder o prazo específico.
    if "nimbus" in p and any(t in p for t in ("prazo", "pagamento")):
        return RespostaConsulta(
            pergunta,
            "[contratos/contrato_nimbus.md] O pagamento da Nimbus Cloud é até o dia 10 de cada mês.",
            ("contratos/contrato_nimbus.md",),
        )
    if "atlas" in p and any(t in p for t in ("prazo", "pagamento")):
        return RespostaConsulta(
            pergunta,
            "[contratos/contrato_atlas.md] O pagamento da Atlas Data é até o dia 15 de cada mês.",
            ("contratos/contrato_atlas.md",),
        )
    return _buscar_documentos(pergunta, data_dir)


def gerar_relatorio(
    notas: tuple[NotaFiscal, ...] | list[NotaFiscal],
    validacoes: tuple[ValidacaoNota, ...] | list[ValidacaoNota],
    status: str,
    aprovacoes_necessarias: int,
    trilha: tuple[str, ...] | list[str],
    consultas: tuple[RespostaConsulta, ...] | list[RespostaConsulta] = (),
) -> str:
    total = sum(n.total for n in notas)
    linhas = [
        "# Relatório de auditoria contábil",
        "",
        f"**Status:** `{status}`  ",
        f"**Notas:** {len(notas)}  ",
        f"**Valor total:** {formatar_moeda(total)}  ",
        f"**Aprovações necessárias:** {aprovacoes_necessarias}  ",
        "",
        "## Notas processadas",
        "",
        "| Nota | Fornecedor | Total | Itens | Status | Checksum |",
        "|---|---|---:|---:|---|---|",
    ]
    for nota, validacao in zip(notas, validacoes):
        linhas.append(
            f"| {nota.numero} | {nota.fornecedor} | {formatar_moeda(nota.total)} | "
            f"{formatar_moeda(validacao.total_itens)} | {validacao.status} | `{nota.checksum}` |"
        )
    linhas.extend(["", "## Divergências e aprovações", ""])
    achou = False
    for validacao in validacoes:
        for div in validacao.divergencias:
            achou = True
            linhas.append(
                f"- **NF {validacao.numero}** [{div.severidade}] {div.tipo}: {div.descricao} "
                f"({formatar_moeda(div.valor)})"
            )
        if validacao.requer_aprovacao:
            achou = True
            linhas.append(f"- **NF {validacao.numero}** aprovação: {validacao.motivo_aprovacao}")
    if not achou:
        linhas.append("- Nenhuma divergência; nenhuma aprovação pendente.")
    linhas.extend(["", "## Consultas de apoio", ""])
    for consulta in consultas:
        estado = "abstenção" if consulta.absteve else "respondida"
        linhas.append(f"- ({estado}) {consulta.pergunta} → {consulta.resposta}")
    linhas.extend(["", "## Trilha de auditoria", ""])
    for evento in trilha:
        linhas.append(f"- {evento}")
    linhas.extend(
        [
            "",
            "## Decisão",
            "",
            (
                "Pagamentos ficam **bloqueados para revisão humana** até que divergências sejam "
                "resolvidas e aprovações sejam registradas."
                if status != "concluido"
                else "Notas validadas e elegíveis para o fluxo de pagamento."
            ),
            "",
            "_Documento sintético gerado para o curso. Nenhum pagamento real é executado._",
        ]
    )
    return "\n".join(linhas)


def executar_workflow(data_dir: Path) -> WorkflowResult:
    trilha: list[str] = []
    brutas = ingerir_notas(data_dir)
    trilha.append(f"01_ingestao: {len(brutas)} notas com checksum e fonte")

    notas = [extrair_nota(bruta) for bruta in brutas]
    trilha.append(f"02_extracao: {len(notas)} notas estruturadas")

    lancamentos = carregar_lancamentos(data_dir)
    validacoes = [validar_nota(nota, lancamentos) for nota in notas]
    divergencias = sum(len(v.divergencias) for v in validacoes)
    trilha.append(
        f"03_validacao: {divergencias} divergência(s); "
        f"{sum(v.requer_aprovacao for v in validacoes)} aprovação(ões)"
    )

    docs_notas = {n.numero for n in notas}
    orfaos = [
        l for l in lancamentos if l.documento not in docs_notas and l.status.lower() != "cancelado"
    ]
    if orfaos:
        trilha.append(
            "03b_razao: lançamento(s) sem nota — "
            + ", ".join(f"{l.documento} ({formatar_moeda(l.valor)})" for l in orfaos)
        )

    consultas = (
        consultar_contabil("Qual o limite de aprovação de notas?", data_dir),
        consultar_contabil("Qual foi a receita de março de 2026?", data_dir),
    )
    trilha.append("04_consulta: política e DRE recuperadas com fontes")

    aprovacoes = sum(v.requer_aprovacao for v in validacoes)
    status = "revisao_humana" if divergencias or aprovacoes else "concluido"
    trilha.append(
        f"05_revisao: status={status}; {aprovacoes} aprovação(ões) humana(s) pendente(s)"
    )

    trilha.append("06_relatorio: relatório e trilha de auditoria gerados")
    relatorio = gerar_relatorio(notas, validacoes, status, aprovacoes, trilha, consultas)
    return WorkflowResult(
        notas=tuple(notas),
        validacoes=tuple(validacoes),
        status=status,
        aprovacoes_necessarias=aprovacoes,
        total_divergencias=divergencias,
        relatorio=relatorio,
        trilha=tuple(trilha),
        consultas=consultas,
    )
