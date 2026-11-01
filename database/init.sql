-- Migration inicial: estrutura de produtos, vendas e itens de venda + carga de exemplo.
-- Relação N:N entre venda e produto resolvida por item_venda.

DROP TABLE IF EXISTS item_venda;
DROP TABLE IF EXISTS venda;
DROP TABLE IF EXISTS produto;

CREATE TABLE produto (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    nome  TEXT NOT NULL,
    valor REAL NOT NULL CHECK (valor >= 0)
);

CREATE TABLE venda (
    id_venda    INTEGER PRIMARY KEY AUTOINCREMENT,
    data_venda  DATE NOT NULL,
    valor_total REAL NOT NULL CHECK (valor_total >= 0)
);

CREATE TABLE item_venda (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    id_venda       INTEGER NOT NULL REFERENCES venda (id_venda) ON DELETE CASCADE,
    id_produto     INTEGER NOT NULL REFERENCES produto (id),
    quantidade     INTEGER NOT NULL CHECK (quantidade > 0),
    valor_unitario REAL NOT NULL CHECK (valor_unitario >= 0),
    UNIQUE (id_venda, id_produto)
);

CREATE INDEX idx_venda_data ON venda (data_venda);
CREATE INDEX idx_item_venda_venda ON item_venda (id_venda);
CREATE INDEX idx_item_venda_produto ON item_venda (id_produto);

-- Carga de produtos
INSERT INTO produto (id, nome, valor) VALUES
    (1, 'Camiseta Básica',      59.90),
    (2, 'Calça Jeans',          189.90),
    (3, 'Tênis Esportivo',      349.90),
    (4, 'Boné Aba Curva',       49.90),
    (5, 'Jaqueta Corta-Vento',  279.90),
    (6, 'Meia Esportiva (par)', 19.90);

-- Carga de vendas (datas relativas a hoje, para o filtro padrão do dashboard sempre ter dados)
INSERT INTO venda (id_venda, data_venda, valor_total) VALUES
    (1,  date('now', '-1 day'),  389.70),
    (2,  date('now', '-3 days'), 169.70),
    (3,  date('now', '-5 days'), 249.60),
    (4,  date('now', '-7 days'), 629.80),
    (5,  date('now', '-8 days'), 99.80),
    (6,  date('now', '-12 days'), 249.80),
    (7,  date('now', '-15 days'), 719.70),
    (8,  date('now', '-18 days'), 279.90),
    (9,  date('now', '-22 days'), 429.70),
    (10, date('now', '-25 days'), 79.60),
    (11, date('now', '-28 days'), 179.70),
    (12, date('now', '-35 days'), 629.80),
    (13, date('now', '-45 days'), 189.90);

-- Carga dos itens de cada venda (soma dos itens = valor_total da venda)
INSERT INTO item_venda (id_venda, id_produto, quantidade, valor_unitario) VALUES
    (1,  3, 1, 349.90),
    (1,  6, 2, 19.90),
    (2,  1, 2, 59.90),
    (2,  4, 1, 49.90),
    (3,  2, 1, 189.90),
    (3,  6, 3, 19.90),
    (4,  5, 1, 279.90),
    (4,  3, 1, 349.90),
    (5,  4, 2, 49.90),
    (6,  1, 1, 59.90),
    (6,  2, 1, 189.90),
    (7,  3, 2, 349.90),
    (7,  6, 1, 19.90),
    (8,  5, 1, 279.90),
    (9,  2, 2, 189.90),
    (9,  4, 1, 49.90),
    (10, 6, 4, 19.90),
    (11, 1, 3, 59.90),
    (12, 3, 1, 349.90),
    (12, 5, 1, 279.90),
    (13, 2, 1, 189.90);
