PRAGMA foreign_keys = OFF;
DROP TABLE IF EXISTS avaliacoes;
DROP TABLE IF EXISTS itens_pedido;
DROP TABLE IF EXISTS pedidos;
DROP TABLE IF EXISTS produtos;
DROP TABLE IF EXISTS clientes;
DROP TABLE IF EXISTS categorias;

CREATE TABLE categorias (
  id INTEGER PRIMARY KEY,
  nome TEXT NOT NULL UNIQUE
);

CREATE TABLE produtos (
  id INTEGER PRIMARY KEY,
  nome TEXT NOT NULL,
  categoria_id INTEGER NOT NULL REFERENCES categorias(id),
  preco REAL NOT NULL CHECK (preco >= 0),
  estoque INTEGER NOT NULL CHECK (estoque >= 0),
  descricao TEXT NOT NULL,
  ativo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE clientes (
  id INTEGER PRIMARY KEY,
  nome TEXT NOT NULL,
  cidade TEXT NOT NULL,
  segmento TEXT NOT NULL
);

CREATE TABLE pedidos (
  id INTEGER PRIMARY KEY,
  cliente_id INTEGER NOT NULL REFERENCES clientes(id),
  data TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pago', 'pendente', 'cancelado')),
  total REAL NOT NULL CHECK (total >= 0)
);

CREATE TABLE itens_pedido (
  pedido_id INTEGER NOT NULL REFERENCES pedidos(id),
  produto_id INTEGER NOT NULL REFERENCES produtos(id),
  quantidade INTEGER NOT NULL CHECK (quantidade > 0),
  preco_unitario REAL NOT NULL CHECK (preco_unitario >= 0),
  PRIMARY KEY (pedido_id, produto_id)
);

CREATE TABLE avaliacoes (
  id INTEGER PRIMARY KEY,
  produto_id INTEGER NOT NULL REFERENCES produtos(id),
  cliente_id INTEGER NOT NULL REFERENCES clientes(id),
  nota INTEGER NOT NULL CHECK (nota BETWEEN 1 AND 5),
  comentario TEXT NOT NULL
);

INSERT INTO categorias (id, nome) VALUES
  (1, 'Áudio'),
  (2, 'Periféricos'),
  (3, 'Casa Inteligente'),
  (4, 'Acessórios');

INSERT INTO produtos (id, nome, categoria_id, preco, estoque, descricao, ativo) VALUES
  (1, 'Fone Bluetooth Aurora', 1, 249.90, 40, 'Fone over-ear com cancelamento de ruído e 30h de bateria.', 1),
  (2, 'Caixa de Som Mini', 1, 189.90, 25, 'Caixa portátil à prova d''água, 12h de bateria.', 1),
  (3, 'Teclado Mecânico Klack', 2, 349.00, 15, 'Teclado ABNT2 com switches táteis e iluminação branca.', 1),
  (4, 'Mouse Sem Fio Ponto', 2, 129.90, 60, 'Mouse ergonômico silencioso com receptor USB.', 1),
  (5, 'Monitor 24 Polegadas', 2, 899.00, 8, 'Monitor IPS full HD com saída HDMI e DisplayPort.', 1),
  (6, 'Lâmpada Inteligente Lume', 3, 79.90, 100, 'Lâmpada Wi-Fi com 16 milhões de cores e rotinas.', 1),
  (7, 'Tomada Inteligente Plug', 3, 89.90, 35, 'Tomada Wi-Fi com medição de consumo e timer.', 1),
  (8, 'Hub USB-C 7 em 1', 4, 159.90, 20, 'Hub com HDMI, leitor SD e três portas USB.', 1),
  (9, 'Suporte Notebook Alfa', 4, 119.90, 44, 'Suporte de alumínio ajustável para notebooks de 11 a 17".', 1),
  (10, 'Webcam Full HD Foco', 2, 299.90, 12, 'Webcam 1080p com microfone duplo e tampa de privacidade.', 1);

INSERT INTO clientes (id, nome, cidade, segmento) VALUES
  (1, 'Ana Prado', 'São Paulo', 'consumidor'),
  (2, 'Bruno Lima', 'Curitiba', 'consumidor'),
  (3, 'Carla Nunes', 'Recife', 'pequena empresa'),
  (4, 'Diego Souza', 'Belo Horizonte', 'consumidor'),
  (5, 'Elisa Rocha', 'Porto Alegre', 'pequena empresa');

INSERT INTO pedidos (id, cliente_id, data, status, total) VALUES
  (1001, 1, '2026-01-05', 'pago', 379.80),
  (1002, 2, '2026-01-08', 'pago', 538.90),
  (1003, 3, '2026-01-10', 'pago', 249.70),
  (1004, 1, '2026-01-12', 'pago', 279.80),
  (1005, 4, '2026-01-15', 'pendente', 1198.90),
  (1006, 2, '2026-01-18', 'pago', 329.80),
  (1007, 5, '2026-01-20', 'pago', 289.80),
  (1008, 3, '2026-01-22', 'cancelado', 189.90),
  (1009, 4, '2026-01-25', 'pago', 648.90),
  (1010, 1, '2026-01-28', 'pago', 209.80),
  (1011, 5, '2026-02-02', 'pago', 539.70),
  (1012, 2, '2026-02-05', 'pago', 269.80);

INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES
  (1001, 1, 1, 249.90),
  (1001, 4, 1, 129.90),
  (1002, 3, 1, 349.00),
  (1002, 2, 1, 189.90),
  (1003, 6, 2, 79.90),
  (1003, 7, 1, 89.90),
  (1004, 8, 1, 159.90),
  (1004, 9, 1, 119.90),
  (1005, 5, 1, 899.00),
  (1005, 10, 1, 299.90),
  (1006, 1, 1, 249.90),
  (1006, 6, 1, 79.90),
  (1007, 4, 1, 129.90),
  (1007, 8, 1, 159.90),
  (1008, 2, 1, 189.90),
  (1009, 3, 1, 349.00),
  (1009, 10, 1, 299.90),
  (1010, 7, 1, 89.90),
  (1010, 9, 1, 119.90),
  (1011, 1, 1, 249.90),
  (1011, 4, 1, 129.90),
  (1011, 8, 1, 159.90),
  (1012, 2, 1, 189.90),
  (1012, 6, 1, 79.90);

INSERT INTO avaliacoes (id, produto_id, cliente_id, nota, comentario) VALUES
  (1, 1, 1, 5, 'Excelente isolamento de ruído.'),
  (2, 1, 5, 4, 'Bateria dura o dia inteiro.'),
  (3, 2, 2, 4, 'Boa para viagens, graves razoáveis.'),
  (4, 3, 2, 5, 'Teclado firme e confortável.'),
  (5, 4, 1, 4, 'Silencioso e preciso.'),
  (6, 5, 4, 3, 'Boa imagem, base pouco ajustável.'),
  (7, 6, 3, 5, 'Fácil de configurar.'),
  (8, 7, 3, 4, 'Mede o consumo corretamente.'),
  (9, 8, 1, 5, 'Resolveu todas as portas do notebook.'),
  (10, 9, 1, 4, 'Bom acabamento.'),
  (11, 10, 4, 4, 'Microfone melhor que o esperado.'),
  (12, 3, 4, 4, 'Ótimo custo-benefício.'),
  (13, 6, 2, 4, 'Cor bonita e app estável.');
