# 00 — Estudo de caso: RAG local

**Resultado:** um pipeline RAG mínimo, determinístico e avaliável, sem LLM e sem banco vetorial.
Você vai construir a base que todos os outros módulos reutilizam.

> **Analogia:** o LLM é um palestrante brilhante; o corpus são os arquivos da empresa. RAG é o
> bibliotecário que localiza as fichas certas e as coloca sobre a mesa antes da resposta.

## Arquitetura

```text
data/*.md → carregar → chunking → embeddings → índice em memória
                                              ↓
pergunta ───────────────────────────────> busca top-k → contexto + citações
                                              ↓
                                    resposta extrativa / abstenção
```

Nesta versão, o “gerador” é extrativo: ele escolhe frases dos trechos recuperados. Isso torna o
comportamento observável. Na etapa 0.4 você pode plugar Ollama/OpenAI, mas o contrato permanece.

## Micro-etapas

| ID | Tempo | Objetivo | Arquivo | Validação |
|---|---:|---|---|---|
| 0.1 | 20 | Carregar o corpus e dividir em chunks com overlap | `src/rag.py` | todo chunk ≤ 450 chars, sem palavra cortada |
| 0.2 | 25 | Gerar embeddings hashing determinísticos e indexar | `src/rag.py` | vetor unitário e índice com N chunks |
| 0.3 | 20 | Buscar top-k por similaridade + léxico | `src/rag.py` | 5 perguntas com fonte correta no top-3 |
| 0.4 | 25 | Montar contexto, citar fontes e abster | `src/rag.py` | resposta sem fonte é inválida; fora do corpus abstém |
| 0.5 | 30 | Medir hit@3, citação e abstenção | `solucao/evaluate.py` | relatório com métricas e casos de falha |

**Tempo total:** 2h00.

### Conceito-chave e tarefa prática por etapa

| ID | Conceito-chave | Tarefa prática |
|---|---|---|
| 0.1 | Chunk é a unidade de recuperação; overlap protege a fronteira. | Implementar janela de palavras em `chunk_text`. |
| 0.2 | Embedding é um mapa de proximidade, não um banco de fatos. | Gerar hashing L2 e indexar chunks de forma alinhada. |
| 0.3 | Recall (achar) e precisão (rankear) são métricas diferentes. | Implementar score híbrido e top-k. |
| 0.4 | Groundedness exige evidência, citação e direito de abster. | Selecionar frases, citar fontes e aplicar threshold. |
| 0.5 | Sem avaliação, você tem apenas uma demo. | Rodar o golden set e explicar cada falha. |

## Como executar

```bash
cd 00_estudo_de_caso_rag_local

# 1. Seu esqueleto: mostra o corpus e o TODO atual
python3 src/main.py

# 2. Referência funcional (compare só depois de tentar)
python3 solucao/run_demo.py

# 3. Avaliação
python3 solucao/evaluate.py

# 4. Testes da referência
python3 -m unittest discover -s tests -v
```

## O que implementar

Abra `src/rag.py` e siga os IDs:

- `# TODO(0.1)` em `chunk_text`: janela por palavras, máximo de 450 chars, overlap de 80.
- `# TODO(0.2)` em `embed_text` e `RAGIndex.index`: bag-of-words com hashing, 256 dimensões, L2.
- `# TODO(0.3)` em `RAGIndex.search`: cosseno + sobreposição lexical, ordenação e top-k.
- `# TODO(0.4)` em `RAGIndex.answer`: selecionar frases, citar `[fonte]` e abster sob baixo score.

### Dicas

1. **Chunking:** prefira cortar em limites de palavras. O overlap existe para não perder uma frase
   que ficou na fronteira.
2. **Embedding determinístico:** `hashlib.blake2b(token)` é estável entre execuções. Use o hash para
   escolher uma dimensão e o sinal. Normalize no final.
3. **Score híbrido:** `0.7 * cosseno + 0.3 * interseção_de_tokens` costuma bastar neste corpus.
4. **Abstenção:** se o melhor score for baixo, responda “não encontrei evidência suficiente”.
5. **Citação:** a fonte deve vir do `Chunk`, não do texto gerado.

## Dados

| Arquivo | Conteúdo | Fatos-âncora |
|---|---|---|
| `politica_ferias.md` | RH | 30 dias, aviso de 15 dias, venda de 5 dias |
| `incidentes_suporte.md` | operações | P1: 15 min de resposta / 4h de mitigação |
| `manutencao_preditiva.md` | engenharia | vibração > 7,5 mm/s, precisão 0,89 |
| `arquitetura_edge.md` | arquitetura | MQTT, buffer 72h, nuvem |
| `seguranca_lgpd.md` | segurança | criptografia, retenção, DPO |

As perguntas do golden set estão em `data/perguntas.jsonl`. Duas são deliberadamente fora do corpus.

## Critério de conclusão

- [ ] `python3 solucao/evaluate.py` mostra `hit@3 >= 0.8` e abstenção correta para as 2 perguntas fora do corpus.
- [ ] Você explica a diferença entre recall e precisão neste corpus.
- [ ] Toda resposta do seu pipeline tem fonte ou é uma abstenção explícita.
- [ ] Você sabe por que o embedding é determinístico e o que mudaria com um modelo real.

## Extensões (15–30 min)

- Troque o embedding por Ollama (`nomic-embed-text`) e compare o hit@3.
- Adicione um reranker lexical simples sobre os top-8.
- Meça latência de indexação e busca com `time.perf_counter()`.
- Aumente o chunk para 900 chars e explique o efeito no golden set.
