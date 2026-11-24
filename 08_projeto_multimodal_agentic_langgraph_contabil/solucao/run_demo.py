"""Demo da solução de referência — módulo 08."""

from pathlib import Path

from accounting_agent import consultar_contabil, executar_workflow, formatar_moeda

DATA = Path(__file__).resolve().parent.parent / "data"
SAIDA = DATA / "relatorios"


def main() -> None:
    resultado = executar_workflow(DATA)
    print(f"Status: {resultado.status}")
    print(f"Notas: {len(resultado.notas)} | Aprovações: {resultado.aprovacoes_necessarias}")
    print(f"Divergências: {resultado.total_divergencias}\n")

    for nota, validacao in zip(resultado.notas, resultado.validacoes):
        print(
            f"NF {nota.numero} | {nota.fornecedor} | {formatar_moeda(nota.total)} | "
            f"itens={formatar_moeda(validacao.total_itens)} | status={validacao.status}"
        )
        for div in validacao.divergencias:
            print(f"  ⚠ {div.tipo} [{div.severidade}]: {div.descricao} ({formatar_moeda(div.valor)})")
        if validacao.requer_aprovacao:
            print(f"  🔒 aprovação: {validacao.motivo_aprovacao}")

    for consulta in resultado.consultas:
        print(f"\nP: {consulta.pergunta}\nR: {consulta.resposta}\nfontes={consulta.fontes}")

    SAIDA.mkdir(parents=True, exist_ok=True)
    caminho = SAIDA / "relatorio_demo.md"
    caminho.write_text(resultado.relatorio, encoding="utf-8")
    print(f"\nRelatório salvo em {caminho}")
    print(f"Receita de março: {consultar_contabil('Qual foi a receita de março de 2026?', DATA).resposta}")


if __name__ == "__main__":
    main()
