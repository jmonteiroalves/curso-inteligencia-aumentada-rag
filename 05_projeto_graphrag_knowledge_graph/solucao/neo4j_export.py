"""Exportação opcional para Neo4j (módulo 05).

Por padrão, apenas imprime o Cypher. Para executar:
    NEO4J_URI=bolt://localhost:7687 NEO4J_USER=neo4j NEO4J_PASSWORD=... \
      python3 solucao/neo4j_export.py --executar
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

try:
    from .graph_rag import construir_grafo, exportar_cypher
except ImportError:  # execução direta
    from graph_rag import construir_grafo, exportar_cypher

DATA = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executar", action="store_true", help="executa no Neo4j local")
    args = parser.parse_args()

    grafo = construir_grafo(DATA)
    cypher = exportar_cypher(grafo)
    if not args.executar:
        print(cypher)
        print("\nDry-run. Use --executar e configure NEO4J_* para importar.")
        return

    try:
        from neo4j import GraphDatabase
    except ImportError as exc:
        raise SystemExit("Instale o extra: pip install neo4j") from exc

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "curso-rag-local")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    comandos = [c.strip() for c in cypher.split(";") if c.strip() and not c.strip().startswith("//")]
    try:
        with driver.session() as session:
            for comando in comandos:
                session.run(comando)
        print(f"Importados {len(grafo.entidades)} nós e {len(grafo.triplas)} arestas em {uri}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
