BEGIN TRANSACTION;

INSERT INTO regiao (id_regiao, nome) VALUES (1, 'América Latina');
INSERT INTO regiao (id_regiao, nome) VALUES (2, 'América do Norte');
INSERT INTO regiao (id_regiao, nome) VALUES (3, 'Europa');
INSERT INTO regiao (id_regiao, nome) VALUES (4, 'Oriente Médio');
INSERT INTO regiao (id_regiao, nome) VALUES (5, 'Ásia-Pacífico');

INSERT INTO pais (id_pais, nome, id_regiao) VALUES (1, 'Brasil', 1);
INSERT INTO pais (id_pais, nome, id_regiao) VALUES (2, 'Chile', 1);
INSERT INTO pais (id_pais, nome, id_regiao) VALUES (3, 'Colômbia', 1);
INSERT INTO pais (id_pais, nome, id_regiao) VALUES (4, 'Canadá', 2);
INSERT INTO pais (id_pais, nome, id_regiao) VALUES (5, 'Estados Unidos', 2);
INSERT INTO pais (id_pais, nome, id_regiao) VALUES (6, 'México', 2);
INSERT INTO pais (id_pais, nome, id_regiao) VALUES (7, 'Alemanha', 3);
INSERT INTO pais (id_pais, nome, id_regiao) VALUES (8, 'França', 3);
INSERT INTO pais (id_pais, nome, id_regiao) VALUES (9, 'Noruega', 3);
INSERT INTO pais (id_pais, nome, id_regiao) VALUES (10, 'Países Baixos', 3);
INSERT INTO pais (id_pais, nome, id_regiao) VALUES (11, 'Reino Unido', 3);
INSERT INTO pais (id_pais, nome, id_regiao) VALUES (12, 'Arábia Saudita', 4);
INSERT INTO pais (id_pais, nome, id_regiao) VALUES (13, 'Emirados Árabes Unidos', 4);
INSERT INTO pais (id_pais, nome, id_regiao) VALUES (14, 'Israel', 4);
INSERT INTO pais (id_pais, nome, id_regiao) VALUES (15, 'Austrália', 5);
INSERT INTO pais (id_pais, nome, id_regiao) VALUES (16, 'China', 5);
INSERT INTO pais (id_pais, nome, id_regiao) VALUES (17, 'Cingapura', 5);
INSERT INTO pais (id_pais, nome, id_regiao) VALUES (18, 'Coreia do Sul', 5);
INSERT INTO pais (id_pais, nome, id_regiao) VALUES (19, 'Japão', 5);

COMMIT;
