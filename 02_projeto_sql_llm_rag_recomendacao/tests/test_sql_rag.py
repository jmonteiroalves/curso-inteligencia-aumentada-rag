"""Smoke tests da referência do módulo 02."""

import sqlite3
import unittest
from pathlib import Path

from solucao.sql_rag import (
    carregar_schema,
    executar_sql,
    gerar_sql,
    recomendar,
    responder,
    validar_sql,
)

DB = Path(__file__).resolve().parent.parent / "data" / "loja.db"


class TestSQLRAG(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = carregar_schema(DB)

    def test_schema(self) -> None:
        self.assertIn("produtos", self.schema)
        self.assertIn("preco", self.schema["produtos"].colunas)
        self.assertEqual(len(self.schema), 6)

    def test_consulta_receita(self) -> None:
        resposta = responder(DB, "Quais os 3 produtos com maior receita?")
        self.assertIsNone(resposta.erro)
        self.assertEqual(resposta.linhas[0][0], "Fone Bluetooth Aurora")
        self.assertIn("LIMIT", resposta.sql or "")

    def test_guardrails(self) -> None:
        ataques = [
            "DROP TABLE produtos",
            "DELETE FROM produtos",
            "SELECT * FROM produtos; DELETE FROM produtos",
            "PRAGMA table_info(produtos)",
            "SELECT * FROM tabela_inexistente",
        ]
        for ataque in ataques:
            with self.subTest(ataque=ataque):
                with self.assertRaises(ValueError):
                    validar_sql(ataque, self.schema)

    def test_limit_automatico(self) -> None:
        seguro = validar_sql("SELECT nome FROM produtos", self.schema, max_linhas=7)
        self.assertTrue(seguro.endswith("LIMIT 7"))

    def test_read_only(self) -> None:
        with self.assertRaises(sqlite3.Error):
            executar_sql(DB, "INSERT INTO produtos (id, nome) VALUES (99, 'x')")

    def test_faturamento_total(self) -> None:
        resposta = responder(DB, "Qual o faturamento total dos pedidos pagos?")
        self.assertIsNone(resposta.erro)
        self.assertGreater(resposta.linhas[0][0], 3500)

    def test_recomendacao_explicavel(self) -> None:
        recs = recomendar(DB, 1, top_n=3)
        self.assertEqual(len(recs), 3)
        self.assertIn(6, {r.produto_id for r in recs})
        self.assertTrue(all(r.motivos for r in recs))
        self.assertTrue(any("co-comprado" in motivo for r in recs for motivo in r.motivos))


if __name__ == "__main__":
    unittest.main()
