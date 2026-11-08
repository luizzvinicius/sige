PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS regiao (
    id_regiao INTEGER PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS pais (
    id_pais INTEGER PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE,
    id_regiao INTEGER NOT NULL,
    FOREIGN KEY (id_regiao) REFERENCES regiao (id_regiao)
);

CREATE TABLE IF NOT EXISTS cliente (
    id_cliente INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    idade INTEGER,
    genero TEXT,
    escolaridade TEXT,
    cidade TEXT
);

CREATE TABLE IF NOT EXISTS carro (
    id_carro INTEGER PRIMARY KEY,
    ano INTEGER NOT NULL,
    modelo TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS preco_carro (
    id_carro INTEGER NOT NULL,
    id_pais INTEGER NOT NULL,
    preco NUMERIC NOT NULL,
    ano_referencia INTEGER NOT NULL,
    PRIMARY KEY (id_carro, id_pais, ano_referencia),
    FOREIGN KEY (id_carro) REFERENCES carro (id_carro),
    FOREIGN KEY (id_pais) REFERENCES pais (id_pais)
);

CREATE TABLE IF NOT EXISTS pedido (
    id_pedido TEXT PRIMARY KEY,
    id_cliente INTEGER NOT NULL,
    data_pedido DATE NOT NULL,
    id_pais INTEGER NOT NULL,
    total NUMERIC NOT NULL,
    avaliacao_cliente NUMERIC,
    FOREIGN KEY (id_cliente) REFERENCES cliente (id_cliente),
    FOREIGN KEY (id_pais) REFERENCES pais (id_pais)
);

CREATE TABLE IF NOT EXISTS item_pedido (
    id_item_pedido INTEGER PRIMARY KEY,
    id_pedido TEXT NOT NULL,
    id_carro INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    preco_item NUMERIC NOT NULL,
    desconto NUMERIC NOT NULL DEFAULT 0,
    FOREIGN KEY (id_pedido) REFERENCES pedido (id_pedido),
    FOREIGN KEY (id_carro) REFERENCES carro (id_carro)
);

CREATE TABLE IF NOT EXISTS historico_descontos (
    ano_referencia INTEGER NOT NULL,
    id_pais INTEGER NOT NULL,
    id_carro INTEGER NOT NULL,
    desconto_medio NUMERIC NOT NULL,
    PRIMARY KEY (ano_referencia, id_pais, id_carro),
    FOREIGN KEY (id_pais) REFERENCES pais (id_pais),
    FOREIGN KEY (id_carro) REFERENCES carro (id_carro)
);

CREATE INDEX IF NOT EXISTS idx_pais_id_regiao
    ON pais (id_regiao);

CREATE INDEX IF NOT EXISTS idx_preco_carro_id_pais_ano
    ON preco_carro (id_pais, ano_referencia);

CREATE INDEX IF NOT EXISTS idx_pedido_id_cliente
    ON pedido (id_cliente);

CREATE INDEX IF NOT EXISTS idx_pedido_id_pais_data
    ON pedido (id_pais, data_pedido);

CREATE INDEX IF NOT EXISTS idx_pedido_data_pedido
    ON pedido (data_pedido);

CREATE INDEX IF NOT EXISTS idx_item_pedido_id_pedido
    ON item_pedido (id_pedido);

CREATE INDEX IF NOT EXISTS idx_item_pedido_id_carro
    ON item_pedido (id_carro);

CREATE INDEX IF NOT EXISTS idx_historico_descontos_pais_carro_ano
    ON historico_descontos (id_pais, id_carro, ano_referencia);

CREATE INDEX IF NOT EXISTS idx_historico_descontos_carro
    ON historico_descontos (id_carro);
