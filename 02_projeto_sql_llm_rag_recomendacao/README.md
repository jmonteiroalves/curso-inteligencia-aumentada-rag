# 02 — SQL + LLM + RAG + recomendação

**Resultado:** um assistente que entende uma pergunta de negócio, seleciona o schema relevante,
gera SQL **somente leitura**, executa com limites e complementa a resposta com recomendações
híbridas (co-compra + similaridade de conteúdo).

> **Analogia:** o banco é um arquivo físico com mil gavetas. O LLM não pode abrir todas; o
> *schema linking* é o índice das gavetas, o SQL é o pedido de consulta e os guardrails são o
> funcionário que confere se você pediu “ler” e não “incendiar”.

## Arquitetura

```text
pergunta
  ├─> schema linking (tabelas/colunas relevantes)
  ├─> geração de SQL (template ou LLM)
  ├─> validação: SELECT-only, tabelas conhecidas, 1 statement, LIMIT
  ├─> execução read-only (SQLite URI mode=ro)
  └─> resposta tabular + explicação
                 │
cliente ─────────┴─> recomendador: co-compra + categoria/preço/nota
```

## Micro-etapas

| ID | Tempo | Objetivo | Arquivo | Validação |
|---|---:|---|---|---|
| 2.1 | 25 | Inspecionar o modelo relacional | `data/loja.db` | contagens e FKs conferem |
| 2.2 | 20 | Schema linking por pergunta | `src/sql_rag.py` | tabelas relevantes no topo |
| 2.3 | 30 | Gerar e validar SQL perigoso | `src/sql_rag.py` | DROP/DELETE/ATTACH e tabela desconhecida rejeitados |
| 2.4 | 25 | Executar somente leitura e responder | `src/sql_rag.py` | `LIMIT` aplicado; resultado explicado |
| 2.5 | 30 | Recomendação híbrida e avaliação | `src/sql_rag.py` | co-compra no top-3; precision@3 reportada |

**Tempo total:** 2h10.

### Conceito-chave e tarefa prática por etapa

| ID | Conceito-chave | Tarefa prática |
|---|---|---|
| 2.1 | Schema é o mapa das gavetas do banco. | Inspecionar tabelas, colunas e chaves. |
| 2.2 | Schema linking reduz custo e alucinação. | Pontuar e selecionar tabelas relevantes. |
| 2.3 | SQL gerado é código não confiável até ser validado. | Implementar templates e guardrails. |
| 2.4 | Leitura segura é conexão `mode=ro` + `LIMIT` + explicação. | Executar e formatar o resultado. |
| 2.5 | Recomendação útil é híbrida e explicável. | Combinar co-compra, categoria e nota. |

## Como executar

```bash
cd 02_projeto_sql_llm_rag_recomendacao

# Conferir o banco
python3 - <<'PY'
import sqlite3
con = sqlite3.connect("data/loja.db")
for t in ("produtos", "pedidos", "itens_pedido", "avaliacoes"):
    print(t, con.execute(f"select count(*) from {t}").fetchone()[0])
PY

python3 src/main.py
python3 solucao/run_demo.py
python3 solucao/evaluate.py
python3 -m unittest discover -s tests -v
```

## O que implementar

- `# TODO(2.1)` em `carregar_schema`: leia tabelas/colunas via `PRAGMA table_info`.
- `# TODO(2.2)` em `selecionar_tabelas`: pontue tabelas por tokens e sinônimos.
- `# TODO(2.3)` em `gerar_sql` e `validar_sql`: templates determinísticos + guardrails.
- `# TODO(2.4)` em `executar_sql` e `responder`: conexão read-only, limite e explicação.
- `# TODO(2.5)` em `recomendar`: matriz de co-compra + afinidade de categoria/preço.

### Dicas

1. **Nunca** concatene a pergunta do usuário dentro do SQL. Gere SQL a partir de regras/LLM e
   valide a saída.
2. `sqlite3.connect("file:data/loja.db?mode=ro", uri=True)` impede escrita no nível da conexão.
3. Rejeite comentários (`--`, `/*`), `;` extra, `PRAGMA`, `ATTACH`, `VACUUM`, DDL e DML.
4. `LIMIT 50` é uma política de produto, não apenas performance.
5. Recomendação não é “SELECT aleatório”: explique cada item (co-compra, categoria, nota, preço).

## Modelo de dados

| Tabela | Papel | Colunas-chave |
|---|---|---|
| `categorias` | taxonomia | `id`, `nome` |
| `produtos` | catálogo | `nome`, `preco`, `estoque`, `categoria_id` |
| `clientes` | compradores sintéticos | `id`, `cidade`, `segmento` |
| `pedidos` | transações | `status`, `total`, `data` |
| `itens_pedido` | linhas | `pedido_id`, `produto_id`, `quantidade` |
| `avaliacoes` | feedback | `nota`, `comentario` |

O banco `data/loja.db` já vem gerado. Para recriar: `python3 data/reset_db.py`.

## Perguntas de referência

1. Quais os 3 produtos com maior receita?
2. Quais produtos custam menos de R$ 150 e têm estoque acima de 30?
3. Quantos pedidos existem por status?
4. Qual a nota média por produto?
5. Qual o faturamento total dos pedidos pagos?
6. Recomende produtos para o cliente 1.

## Critério de conclusão

- [ ] `validate_sql` rejeita `DROP`, `DELETE`, `PRAGMA`, `ATTACH` e múltiplos statements.
- [ ] Toda consulta executada termina com `LIMIT` e usa conexão `mode=ro`.
- [ ] A resposta mostra SQL, linhas e uma explicação em linguagem natural.
- [ ] `precision@3` da recomendação é reportado; ao menos um item co-comprado aparece.
- [ ] Você explica por que schema linking reduz custo e alucinação.

## Extensões

- Plugar um LLM local para gerar SQL e comparar com os templates (mantenha os guardrails).
- Adicionar `EXPLAIN QUERY PLAN` e rejeitar varreduras completas acima de um custo.
- Criar um teste de propriedade que gere 100 perguntas e nunca permita DML.
- Trocar SQLite por PostgreSQL e usar `SET TRANSACTION READ ONLY`.
- Criar um cache de recomendações por cliente com TTL.
