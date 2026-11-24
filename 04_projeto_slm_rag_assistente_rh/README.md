# 04 — SLM + RAG + assistente de RH

**Resultado:** um assistente de triagem de currículos que anonimiza PII, pontua aderência à vaga,
mostra evidências, gera entrevista estruturada e audita disparidades — sem tomar decisão final.

> **Analogia:** o assistente é um recrutador júnior muito organizado. Ele lê as fichas, marca
> evidências com grifo, prepara perguntas e aponta lacunas. A contratação continua sendo uma
> decisão humana, documentada e auditável.

## Arquitetura

```text
currículos brutos
   └─> anonimização (nome/e-mail/telefone/gênero/idade fora do score)
         └─> matching por critérios ponderados
               ├─> score 0–100 + evidências + lacunas
               ├─> 5 perguntas de entrevista
               └─> auditoria de taxa de seleção por grupo sintético
```

## Micro-etapas

| ID | Tempo | Objetivo | Arquivo | Validação |
|---|---:|---|---|---|
| 4.1 | 25 | Carregar RH e remover PII | `src/rh_rag.py` | nome/e-mail/telefone ausentes no objeto de matching |
| 4.2 | 20 | Definir critérios e pesos | `src/rh_rag.py` | pesos somam 1,0; sem atributos protegidos |
| 4.3 | 30 | Pontuar candidatos | `src/rh_rag.py` | score 0–100 determinístico |
| 4.4 | 25 | Explicar com evidências | `src/rh_rag.py` | cada critério tem evidência ou lacuna |
| 4.5 | 20 | Gerar entrevista estruturada | `src/rh_rag.py` | 5 perguntas ligadas a critérios |
| 4.6 | 30 | Auditar viés e emitir relatório | `solucao/evaluate.py` | taxa de seleção por grupo sintético |

**Tempo total:** 2h30.

### Conceito-chave e tarefa prática por etapa

| ID | Conceito-chave | Tarefa prática |
|---|---|---|
| 4.1 | Anonimizar é remover do objeto de decisão, não só esconder o nome. | Implementar whitelist de campos. |
| 4.2 | Critérios e pesos tornam o score auditável. | Validar soma 1,0 e proibir atributos protegidos. |
| 4.3 | Matching é cobertura de evidências, não intuição. | Pontuar habilidades, termos e experiência. |
| 4.4 | Explicabilidade exige fonte observável por critério. | Produzir evidências e lacunas. |
| 4.5 | Entrevista estruturada reduz improviso e viés. | Gerar 5 perguntas ligadas a critérios. |
| 4.6 | Auditoria expõe disparidade; não corrige sozinha. | Calcular taxa de seleção por grupo. |

## Como executar

```bash
cd 04_projeto_slm_rag_assistente_rh
python3 src/main.py
python3 solucao/run_demo.py
python3 solucao/evaluate.py
python3 -m unittest discover -s tests -v
```

## O que implementar

- `# TODO(4.1)` em `anonimizar_candidato`: whitelist de campos, nunca “esconder” PII em texto livre.
- `# TODO(4.2)` em `validar_vaga`: pesos, critérios e proibição de atributos protegidos.
- `# TODO(4.3)` em `pontuar_candidato`: cobertura de termos + nível de habilidade + experiência.
- `# TODO(4.4)` em `evidencias`: trecho/fonte para cada ponto e lacunas explícitas.
- `# TODO(4.5)` em `gerar_perguntas`: 5 perguntas comportamentais/técnicas ligadas aos critérios.
- `# TODO(4.6)` em `auditar_vies`: taxa de seleção por grupo, sem ajustar score automaticamente.

### Dicas

1. **Anonimizar não é substituir o nome por “X”.** Remova também e-mail, telefone e qualquer
   atributo protegido do objeto usado no matching.
2. **Não use gênero, idade, cidade ou nome** como features. Se usar, você precisa provar a
   necessidade, legalidade e ausência de proxy — o padrão do curso é não usar.
3. **Pesos somam 1,0.** Isso torna o score interpretável e comparável.
4. **Evidência** é uma frase ou habilidade observável, não uma impressão (“parece bom”).
5. **Auditoria não é cota automática.** Ela expõe disparidades para revisão humana.

## Dados

| Arquivo | Conteúdo |
|---|---|
| `data/vaga.json` | vaga fictícia de Engenheiro(a) de IA Sênior, critérios e pesos |
| `data/curriculos.json` | 6 currículos sintéticos, com grupos apenas para auditoria |

> Os currículos incluem gênero e faixa etária **somente** para o exercício de auditoria. Eles não
> podem entrar no score. Nenhum dado é real.

## Critério de conclusão

- [ ] O objeto de matching não contém `nome`, `email`, `telefone`, `genero` ou `faixa_etaria`.
- [ ] Pesos da vaga somam 1,0 e há pelo menos 5 critérios.
- [ ] Cada resultado tem 5 perguntas e evidências para todos os critérios avaliados.
- [ ] Mudar gênero/idade de um currículo **não altera** o score.
- [ ] O relatório mostra taxa de seleção por grupo e uma limitação do experimento.
- [ ] Você explica por que remover o atributo não elimina necessariamente o viés.

## Extensões

- Use um SLM para redigir perguntas a partir das evidências e avalie groundedness.
- Adicione um teste de proxy: cidade/categoria de formação não deve mudar o score sem justificativa.
- Crie um “cartão de modelo” com finalidade, dados, métricas, riscos e revisão humana.
- Adicione revisão por pares e um canal de contestação do candidato.
- Meça justiça por equalized odds em um dataset sintético maior (sem usar dados reais).
