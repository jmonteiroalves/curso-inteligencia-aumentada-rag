"""Avaliação do fluxo contábil multimodal (módulo 08)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from accounting_agent import consultar_contabil, executar_workflow, formatar_moeda

DATA = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    resultado = executar_workflow(DATA)
    por_numero = {v.numero: v for v in resultado.validacoes}

    print("== Validações ==")
    for nota, validacao in zip(resultado.notas, resultado.validacoes):
        print(
            f"NF {nota.numero} | total={formatar_moeda(nota.total)} | "
            f"itens={formatar_moeda(validacao.total_itens)} | status={validacao.status} | "
            f"checksum={nota.checksum}"
        )
        for div in validacao.divergencias:
            print(f"  - {div.severidade}/{div.tipo}: {div.descricao} ({formatar_moeda(div.valor)})")

    consulta = consultar_contabil("Qual foi a receita de março de 2026?", DATA)
    politica = consultar_contabil("Qual o limite de aprovação de notas?", DATA)
    print("\n== Consultas ==")
    print(f"{consulta.pergunta} -> {consulta.resposta} fontes={consulta.fontes}")
    print(f"{politica.pergunta} -> {politica.resposta[:120]} fontes={politica.fontes}")

    falhas: list[str] = []
    if resultado.status != "revisao_humana":
        falhas.append("status global deveria ser revisao_humana")
    if resultado.aprovacoes_necessarias != 2:
        falhas.append("esperadas 2 aprovações")
    if por_numero["1002"].status != "valida":
        falhas.append("NF 1002 deveria ser válida")
    if not any(abs(d.valor - 50.0) < 0.01 for d in por_numero["1003"].divergencias):
        falhas.append("divergência de R$ 50 da NF 1003 não detectada")
    if len(por_numero["1001"].lancamentos) != 2:
        falhas.append("duplicidade da NF 1001 não detectada")
    if "150.000,00" not in consulta.resposta or not any(
        "dre_2026.csv" in fonte for fonte in consulta.fontes
    ):
        falhas.append("consulta à DRE sem valor/fonte")
    if "05_revisao" not in resultado.relatorio or "06_relatorio" not in resultado.relatorio:
        falhas.append("trilha ausente no relatório")
    if "1004" not in " ".join(resultado.trilha):
        falhas.append("lançamento órfão 1004 não registrado")

    print("\n== LangGraph ==")
    if importlib.util.find_spec("langgraph"):
        from langgraph_flow import executar_fluxo

        estado = executar_fluxo(DATA)
        print(f"status={estado.get('status')} aprovacoes={estado.get('aprovacoes')}")
        if estado.get("status") != "revisao_humana":
            falhas.append("fluxo LangGraph divergiu")
    else:
        print("langgraph não instalado; validação opcional ignorada (pip install langgraph)")

    print("\n== Resumo ==")
    print(f"status={resultado.status}")
    print(f"notas={len(resultado.notas)}")
    print(f"aprovacoes={resultado.aprovacoes_necessarias}")
    print(f"divergencias={resultado.total_divergencias}")
    print(f"relatorio_chars={len(resultado.relatorio)}")

    if falhas:
        raise SystemExit("Falhas: " + "; ".join(falhas))
    print("Critérios de avaliação atingidos.")


if __name__ == "__main__":
    main()
