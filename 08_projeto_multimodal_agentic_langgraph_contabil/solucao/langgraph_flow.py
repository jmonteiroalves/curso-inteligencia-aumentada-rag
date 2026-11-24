"""Fluxo multimodal em LangGraph (módulo 08).

Requer `langgraph` instalado. O restante do curso e os testes offline não dependem
deste arquivo. Execute:
    python3 solucao/langgraph_flow.py
"""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

try:
    from .accounting_agent import (
        NotaBruta,
        NotaFiscal,
        RespostaConsulta,
        ValidacaoNota,
        consultar_contabil,
        extrair_nota,
        gerar_relatorio,
        ingerir_notas,
        validar_nota,
        carregar_lancamentos,
    )
except ImportError:  # execução direta
    from accounting_agent import (  # type: ignore
        NotaBruta,
        NotaFiscal,
        RespostaConsulta,
        ValidacaoNota,
        consultar_contabil,
        extrair_nota,
        gerar_relatorio,
        ingerir_notas,
        validar_nota,
        carregar_lancamentos,
    )

DATA = Path(__file__).resolve().parent.parent / "data"


class EstadoFluxo(TypedDict, total=False):
    data_dir: str
    brutas: list[NotaBruta]
    notas: list[NotaFiscal]
    validacoes: list[ValidacaoNota]
    consultas: list[RespostaConsulta]
    status: str
    aprovacoes: int
    trilha: list[str]
    relatorio: str


def no_ingerir(state: EstadoFluxo) -> dict[str, object]:
    brutas = ingerir_notas(Path(state["data_dir"]))
    return {
        "brutas": brutas,
        "trilha": [*state.get("trilha", []), f"01_ingestao: {len(brutas)} notas"],
    }


def no_extrair(state: EstadoFluxo) -> dict[str, object]:
    notas = [extrair_nota(b) for b in state["brutas"]]
    return {
        "notas": notas,
        "trilha": [*state.get("trilha", []), f"02_extracao: {len(notas)} notas"],
    }


def no_validar(state: EstadoFluxo) -> dict[str, object]:
    lancamentos = carregar_lancamentos(Path(state["data_dir"]))
    validacoes = [validar_nota(n, lancamentos) for n in state["notas"]]
    divs = sum(len(v.divergencias) for v in validacoes)
    return {
        "validacoes": validacoes,
        "trilha": [*state.get("trilha", []), f"03_validacao: {divs} divergência(s)"],
    }


def no_recuperar(state: EstadoFluxo) -> dict[str, object]:
    data_dir = Path(state["data_dir"])
    consultas = [
        consultar_contabil("Qual o limite de aprovação de notas?", data_dir),
        consultar_contabil("Qual foi a receita de março de 2026?", data_dir),
    ]
    return {
        "consultas": consultas,
        "trilha": [*state.get("trilha", []), "04_consulta: DRE e política"],
    }


def no_revisar(state: EstadoFluxo) -> dict[str, object]:
    validacoes = state.get("validacoes", [])
    aprovacoes = sum(v.requer_aprovacao for v in validacoes)
    tem_divergencia = any(v.divergencias for v in validacoes)
    status = "revisao_humana" if (tem_divergencia or aprovacoes) else "concluido"
    return {
        "status": status,
        "aprovacoes": aprovacoes,
        "trilha": [
            *state.get("trilha", []),
            f"05_revisao: status={status}; {aprovacoes} aprovação(ões)",
        ],
    }


def no_relatorio(state: EstadoFluxo) -> dict[str, object]:
    trilha = [*state.get("trilha", []), "06_relatorio: gerado"]
    relatorio = gerar_relatorio(
        state["notas"],
        state["validacoes"],
        state.get("status", "revisao_humana"),
        int(state.get("aprovacoes", 0)),
        trilha,
        state.get("consultas", []),
    )
    return {"relatorio": relatorio, "trilha": trilha}


def construir_grafo():
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise RuntimeError("Instale langgraph: pip install langgraph") from exc

    builder = StateGraph(EstadoFluxo)
    builder.add_node("ingerir", no_ingerir)
    builder.add_node("extrair", no_extrair)
    builder.add_node("validar", no_validar)
    builder.add_node("recuperar", no_recuperar)
    builder.add_node("revisar", no_revisar)
    builder.add_node("relatorio", no_relatorio)
    builder.add_edge(START, "ingerir")
    builder.add_edge("ingerir", "extrair")
    builder.add_edge("extrair", "validar")
    builder.add_edge("validar", "recuperar")
    builder.add_edge("recuperar", "revisar")
    builder.add_edge("revisar", "relatorio")
    builder.add_edge("relatorio", END)
    return builder.compile()


def executar_fluxo(data_dir: Path = DATA) -> EstadoFluxo:
    grafo = construir_grafo()
    return grafo.invoke({"data_dir": str(data_dir), "trilha": []})  # type: ignore[return-value]


if __name__ == "__main__":
    try:
        estado = executar_fluxo()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Status: {estado['status']}")
    print(f"Aprovações: {estado['aprovacoes']}")
    print("\nTrilha:")
    for evento in estado["trilha"]:
        print(f"- {evento}")
    print("\nRelatório:\n")
    print(estado["relatorio"][:1200])
