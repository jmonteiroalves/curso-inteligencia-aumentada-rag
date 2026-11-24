"""Smoke tests da referência do módulo 08."""

import importlib.util
import unittest
from pathlib import Path

from solucao.accounting_agent import (
    carregar_lancamentos,
    consultar_contabil,
    executar_workflow,
    extrair_nota,
    formatar_moeda,
    ingerir_notas,
    validar_nota,
)

DATA = Path(__file__).resolve().parent.parent / "data"
TEM_LANGGRAPH = importlib.util.find_spec("langgraph") is not None


class TestContabil(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.brutas = ingerir_notas(DATA)
        cls.notas = [extrair_nota(b) for b in cls.brutas]
        cls.lancamentos = carregar_lancamentos(DATA)
        cls.validacoes = {n.numero: validar_nota(n, cls.lancamentos) for n in cls.notas}
        cls.workflow = executar_workflow(DATA)

    def test_ingestao_multimodal_com_checksum(self) -> None:
        self.assertEqual(len(self.brutas), 3)
        self.assertTrue(all(len(b.checksum) == 16 for b in self.brutas))
        self.assertTrue(all(b.caminho.suffix in {".png", ".pdf"} for b in self.brutas))

    def test_extracao_campos(self) -> None:
        nota = next(n for n in self.notas if n.numero == "1001")
        self.assertEqual(nota.fornecedor, "Nimbus Cloud Serviços Ltda.")
        self.assertEqual(nota.total, 1500.0)
        self.assertEqual(len(nota.itens), 2)
        self.assertIn("Total da nota", nota.texto_ocr)

    def test_validacao_limpa(self) -> None:
        self.assertEqual(self.validacoes["1002"].status, "valida")
        self.assertFalse(self.validacoes["1002"].requer_aprovacao)

    def test_divergencia_de_total(self) -> None:
        validacao = self.validacoes["1003"]
        self.assertEqual(validacao.status, "revisao_humana")
        self.assertTrue(any(abs(d.valor - 50.0) < 0.01 for d in validacao.divergencias))
        self.assertTrue(validacao.requer_aprovacao)

    def test_duplicidade_no_razao(self) -> None:
        validacao = self.validacoes["1001"]
        self.assertEqual(len(validacao.lancamentos), 2)
        self.assertTrue(any(d.tipo == "duplicidade" for d in validacao.divergencias))

    def test_consultas_com_fonte(self) -> None:
        dre = consultar_contabil("Qual foi a receita de março de 2026?", DATA)
        self.assertIn("150.000,00", dre.resposta)
        self.assertIn("dre_2026.csv:2026-03", dre.fontes)
        politica = consultar_contabil("Qual o limite de aprovação de notas?", DATA)
        self.assertFalse(politica.absteve)
        self.assertIn("politicas/politica_contabil.md", politica.fontes)

    def test_workflow_status_e_trilha(self) -> None:
        self.assertEqual(self.workflow.status, "revisao_humana")
        self.assertEqual(self.workflow.aprovacoes_necessarias, 2)
        self.assertEqual(self.workflow.total_divergencias, 2)
        self.assertIn("05_revisao", self.workflow.relatorio)
        self.assertIn("1004", " ".join(self.workflow.trilha))
        self.assertTrue(all(n.checksum in self.workflow.relatorio for n in self.workflow.notas))

    def test_nenhum_pagamento_automatico(self) -> None:
        self.assertIn("revisão humana", self.workflow.relatorio.lower())
        self.assertNotIn("pagamento executado", self.workflow.relatorio.lower())

    def test_formatar_moeda(self) -> None:
        self.assertEqual(formatar_moeda(1234.5), "R$ 1.234,50")

    @unittest.skipUnless(TEM_LANGGRAPH, "langgraph opcional não instalado")
    def test_langgraph_flow(self) -> None:
        from solucao.langgraph_flow import executar_fluxo

        estado = executar_fluxo(DATA)
        self.assertEqual(estado["status"], "revisao_humana")
        self.assertEqual(estado["aprovacoes"], 2)
        self.assertIn("06_relatorio", estado["relatorio"])


if __name__ == "__main__":
    unittest.main()
