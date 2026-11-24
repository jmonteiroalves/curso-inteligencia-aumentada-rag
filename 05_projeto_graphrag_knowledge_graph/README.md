# 05 — GraphRAG e knowledge graph

**Resultado:** um grafo de conhecimento sintético com entidades, relações, consultas multi-hop,
resposta híbrida (grafo + trechos) e exportação idempotente para Neo4j.

> **Analogia:** RAG vetorial é uma pilha de fichas por semelhança. GraphRAG é o mapa de metrô:
> ele mostra que a estação “Qdrant” se conecta ao “Projeto Aurora RAG”, que se conecta à pessoa
> que o lidera. Para perguntas relacionais, o mapa vale mais que a ficha isolada.

## Arquitetura

```text
textos → entidades (gazetteer/linker) → triplas (sujeito, relação, objeto)
                                            ↓
                                   grafo dirigido + evidências
                                            ↓
pergunta → âncoras → caminhos 1–3 hops → score por tipo/relação → resposta
                                            ↓
                               + trechos textuais (híbrido)
                                            ↓
                                  Cypher idempotente → Neo4j
```

## Micro-etapas

| ID | Tempo | Objetivo | Arquivo | Validação |
|---|---:|---|---|---|
| 5.1 | 25 | Extrair e tipar entidades | `src/graph_rag.py` | entidades canônicas sem duplicatas |
| 5.2 | 30 | Extrair relações com evidência | `src/graph_rag.py` | triplas válidas e rastreáveis |
| 5.3 | 25 | Construir o grafo | `src/graph_rag.py` | vizinhança e grau conferem |
| 5.4 | 30 | Responder multi-hop | `src/graph_rag.py` | 5 perguntas relacionais corretas |
| 5.5 | 30 | Combinar grafo + texto | `src/graph_rag.py` | contexto e fontes dos dois sinais |
| 5.6 | 30 | Exportar Neo4j e comunidades | `solucao/neo4j_export.py` | Cypher idempotente e resumo de componente |

**Tempo total:** 2h50.

### Conceito-chave e tarefa prática por etapa

| ID | Conceito-chave | Tarefa prática |
|---|---|---|
| 5.1 | NER + entity linking resolvem nomes e aliases. | Extrair e canonicalizar entidades. |
| 5.2 | Aresta sem evidência é boato estruturado. | Extrair triplas com fonte e frase. |
| 5.3 | Grafo é adjacência dirigida + deduplicação. | Construir nós, arestas e grau. |
| 5.4 | Multi-hop é busca, não prompt maior. | Enumerar caminhos e pontuar por tipo/relação. |
| 5.5 | Grafo responde relações; texto dá contexto. | Combinar subgrafo e trechos citáveis. |
| 5.6 | Cypher idempotente e comunidades ajudam a operar. | Gerar `MERGE` e componentes conectados. |

## Como executar

```bash
cd 05_projeto_graphrag_knowledge_graph
python3 src/main.py
python3 solucao/run_demo.py
python3 solucao/evaluate.py
python3 -m unittest discover -s tests -v

# Opcional: exportar para Neo4j
docker compose --profile graph up -d neo4j
python3 solucao/neo4j_export.py
```

## O que implementar

- `# TODO(5.1)` em `extrair_entidades`: gazetteer + canonicalização por alias.
- `# TODO(5.2)` em `extrair_triplas`: padrões de relação, fonte e evidência.
- `# TODO(5.3)` em `construir_grafo`: nós, arestas dirigidas e deduplicação.
- `# TODO(5.4)` em `caminhos`/`responder`: BFS/DFS limitado e score de caminho.
- `# TODO(5.5)` em `recuperar_contexto_textual`/`responder_hibrido`: unir grafo e trechos.
- `# TODO(5.6)` em `exportar_cypher` e `comunidades`.

### Dicas

1. **Gazetteer é um baseline de NER.** Em produção, troque por um modelo e mantenha o “entity
   linking” para resolver aliases e duplicatas.
2. **Direção importa.** `Marina lidera Projeto` é diferente de `Projeto lidera Marina`.
3. **Toda aresta deve ter evidência.** Sem fonte, o grafo vira boato estruturado.
4. **Multi-hop é busca em grafo, não prompt maior.** Limite saltos e use score por tipo esperado.
5. **Comunidades** ajudam a resumir; não substituem a resposta local.
6. **Cypher idempotente:** `MERGE` com chave estável evita duplicar nós ao reimportar.

## Dados

| Arquivo | Conteúdo |
|---|---|
| `data/textos/01_pessoas.txt` | pessoas, empregos, liderança, mentoria |
| `data/textos/02_projetos.txt` | projetos, tecnologias, dependências |
| `data/textos/03_empresas.txt` | parcerias, financiamento, sedes |
| `data/textos/04_contexto.txt` | contexto narrativo para o sinal textual |
| `data/entidades.json` | gazetteer com nomes, aliases e tipos |

Perguntas de referência:

1. Quem lidera o projeto que usa Qdrant?
2. Qual instituto financia o projeto que usa LangGraph?
3. Quem trabalha na empresa parceira da Nimbus Cloud?
4. Qual tecnologia o projeto liderado por Beatriz Nunes usa?
5. Quem Marina Costa mentora e onde essa pessoa trabalha?

## Critério de conclusão

- [ ] O grafo tem pelo menos 20 nós e 15 arestas, sem triplas duplicadas.
- [ ] As 5 perguntas multi-hop retornam resposta esperada com caminho.
- [ ] Toda resposta cita arquivos de origem.
- [ ] O Cypher exportado usa `MERGE` e pode rodar duas vezes sem duplicar.
- [ ] Você explica quando GraphRAG perde para RAG vetorial (e vice-versa).

## Extensões

- Trocar o gazetteer por spaCy/GLiNER e comparar precisão/recall.
- Adicionar resolução de entidades por similaridade (ex.: “Aurora” → “Aurora Tech”).
- Importar no Neo4j e rodar `MATCH p=(:Pessoa)-[*1..3]-(:Tecnologia)`.
- Implementar comunidades com Louvain via `networkx` e sumários por comunidade.
- Adicionar temporalidade (`desde`, `até`) e arestas invalidadas.
- Medir custo por consulta: hops, arestas visitadas, tokens de contexto.
