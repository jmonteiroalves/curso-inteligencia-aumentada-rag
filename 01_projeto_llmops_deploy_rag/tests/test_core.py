"""Smoke tests da referência do módulo 01."""

import unittest
from pathlib import Path

from solucao.rag_core import Documento, RagService

DATA = Path(__file__).resolve().parent.parent / "data"


class TestRagService(unittest.TestCase):
    def setUp(self) -> None:
        self.service = RagService(DATA)
        self.service.carregar_diretorio()

    def test_ingestao_e_idempotente(self) -> None:
        antes = len(self.service.chunks)
        relatorio = self.service.carregar_diretorio()
        self.assertGreater(relatorio["ignorados"], 0)
        self.assertEqual(len(self.service.chunks), antes)

    def test_documento_atualizado_reindexa(self) -> None:
        doc = Documento.criar("novo", "Novo", "Fato exclusivo: o portal abre às 7h.", "novo.md")
        self.service.ingest([doc])
        self.assertGreater(len(self.service.chunks), 0)
        doc2 = Documento.criar("novo", "Novo", "Fato novo: o portal abre às 9h.", "novo.md")
        rel = self.service.ingest([doc2])
        self.assertEqual(rel["atualizados"], 1)

    def test_query_cita_fonte_e_mede_latencia(self) -> None:
        resultado = self.service.query("Quantos usuários o plano Pro permite?")
        self.assertFalse(resultado.absteve)
        self.assertTrue(resultado.fontes)
        self.assertGreaterEqual(resultado.latencia_ms, 0)
        self.assertTrue(resultado.request_id.startswith("req_"))

    def test_evento_estruturado(self) -> None:
        self.service.query("Qual o SLA de P1?")
        evento = self.service.eventos[-1]
        self.assertEqual(evento["evento"], "consulta")
        self.assertIn("latencia_ms", evento)
        self.assertIn("request_id", evento)

    def test_abstencao(self) -> None:
        self.assertTrue(self.service.query("Qual a política de passagens aéreas?").absteve)

    def test_health(self) -> None:
        self.assertEqual(self.service.health()["status"], "ok")


if __name__ == "__main__":
    unittest.main()
