-- Inicialização opcional do pgvector (perfil pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documentos (
    id          TEXT PRIMARY KEY,
    fonte       TEXT NOT NULL,
    titulo      TEXT NOT NULL,
    conteudo    TEXT NOT NULL,
    embedding   vector(768),
    criado_em   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS documentos_embedding_idx
    ON documentos USING hnsw (embedding vector_cosine_ops);
