"""Valida a estrutura do curso, datasets e marcadores TODO.

Uso:
    python3 scripts/validate_repo.py
"""

from __future__ import annotations

import compileall
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MODULOS = [
    "00_estudo_de_caso_rag_local",
    "01_projeto_llmops_deploy_rag",
    "02_projeto_sql_llm_rag_recomendacao",
    "03_projeto_slm_rag_automacao",
    "04_projeto_slm_rag_assistente_rh",
    "05_projeto_graphrag_knowledge_graph",
    "06_projeto_agentic_rag_customizado",
    "07_projeto_agentic_rag_suporte_routing",
    "08_projeto_multimodal_agentic_langgraph_contabil",
]

ARQUIVOS_RAIZ = [
    "AGENTS.md",
    "PROGRESS.md",
    "README.md",
    "docker-compose.yml",
    "pyproject.toml",
    "requirements.txt",
    ".env.example",
    "Makefile",
    "docs/ANALOGIAS.md",
    "LICENSE",
    "scripts/init_pgvector.sql",
]

ESTRUTURA_MODULO = [
    "README.md",
    "data",
    "src",
    "solucao",
    "tests",
    "solucao/run_demo.py",
    "solucao/evaluate.py",
]

DADOS_OBRIGATORIOS = {
    "00_estudo_de_caso_rag_local": ["data/politica_ferias.md", "data/perguntas.jsonl"],
    "01_projeto_llmops_deploy_rag": ["data/base_conhecimento/planos.md", "data/perguntas.jsonl"],
    "02_projeto_sql_llm_rag_recomendacao": ["data/loja.db", "data/seed.sql"],
    "03_projeto_slm_rag_automacao": ["data/sops.json", "data/solicitacoes.json"],
    "04_projeto_slm_rag_assistente_rh": ["data/vaga.json", "data/curriculos.json"],
    "05_projeto_graphrag_knowledge_graph": ["data/entidades.json", "data/textos/01_pessoas.txt"],
    "06_projeto_agentic_rag_customizado": ["data/docs/politica_viagens.md", "data/tarefas.json"],
    "07_projeto_agentic_rag_suporte_routing": ["data/tickets.jsonl", "data/clientes.json"],
    "08_projeto_multimodal_agentic_langgraph_contabil": [
        "data/notas_fiscais/notas.json",
        "data/notas_fiscais/nf_1001.png",
        "data/notas_fiscais/nf_1001.pdf",
        "data/razao.csv",
        "data/demonstrativos/dre_2026.csv",
    ],
}


def main() -> None:
    erros: list[str] = []
    avisos: list[str] = []

    for arquivo in ARQUIVOS_RAIZ:
        if not (ROOT / arquivo).exists():
            erros.append(f"arquivo raiz ausente: {arquivo}")

    for modulo in MODULOS:
        base = ROOT / modulo
        if not base.is_dir():
            erros.append(f"módulo ausente: {modulo}")
            continue
        for relativo in ESTRUTURA_MODULO:
            if not (base / relativo).exists():
                erros.append(f"{modulo}: ausente {relativo}")
        readme = (base / "README.md").read_text(encoding="utf-8")
        if "### Conceito-chave e tarefa prática por etapa" not in readme:
            erros.append(f"{modulo}: README sem conceito/tarefa por etapa")
        for relativo in DADOS_OBRIGATORIOS.get(modulo, []):
            if not (base / relativo).exists():
                erros.append(f"{modulo}: dado ausente {relativo}")

        arquivos_src = list((base / "src").glob("*.py"))
        if not arquivos_src:
            erros.append(f"{modulo}: src sem Python")
            continue
        todos = sum(
            arquivo.read_text(encoding="utf-8").count("# TODO(") for arquivo in arquivos_src
        )
        print(f"{modulo:<58} TODO(s) em src: {todos}")
        if todos == 0:
            erros.append(f"{modulo}: nenhum marcador # TODO( em src")

        solucao = base / "solucao"
        if not (solucao / "run_demo.py").exists():
            erros.append(f"{modulo}: run_demo.py ausente")
        if any("TODO(" in p.read_text(encoding="utf-8") for p in solucao.glob("*.py")):
            avisos.append(f"{modulo}: solução ainda contém TODO(")

    # Verificação de sintaxe de todo o repositório (não importa dependências).
    if not compileall.compile_dir(ROOT, quiet=1):
        erros.append("erro de sintaxe em algum arquivo Python")

    progresso = (ROOT / "PROGRESS.md").read_text(encoding="utf-8")
    etapas = re.findall(r"^- \[[ x]\] \*\*", progresso, flags=re.MULTILINE)
    if len(etapas) != 51:
        erros.append(f"PROGRESS.md deveria ter 51 etapas; encontrou {len(etapas)}")

    # Imagens sintéticas precisam ter conteúdo real.
    for png in (ROOT / "08_projeto_multimodal_agentic_langgraph_contabil" / "data/notas_fiscais").glob("*.png"):
        if png.stat().st_size < 10_000:
            erros.append(f"imagem suspeita/pequena: {png.name}")

    print()
    for aviso in avisos:
        print(f"aviso: {aviso}")
    if erros:
        print("\nFalhas:")
        for erro in erros:
            print(f"- {erro}")
        sys.exit(1)
    print(f"OK: {len(MODULOS)} módulos, estrutura e datasets validados.")


if __name__ == "__main__":
    main()
