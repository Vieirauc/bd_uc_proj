INSERT INTO publisher (name)
VALUES ('Think Music Records');

INSERT INTO publisher (name)
VALUES ('Make More Music');

INSERT INTO account (username, password_hash, email)
VALUES ('admincards', 'cards21', 'admin@cards.com');

BEGIN TRANSACTION;
INSERT INTO consumer (premium, NULL, account_id)



--INSERT INTO administrator (account_id) VALUES ((SELECT id FROM account WHERE username = 'admincards'));

--INSERT INTO card (id, limit_date, amount, issue_date, consumer_account_id, administrator_account_id)
--VALUES (1, '2023-6-26', 20, '2023-5-19', 1, 1);

-- Inserir dados na tabela account
INSERT INTO account (username, password_hash, email)
VALUES ('mizzymiles', 'miles21', 'mizzy@miles.com');

INSERT INTO account (username, password_hash, email)
VALUES ('gsonwastaken', 'wbg123', 'g@son.com');

-- Obter o ID da conta inserida
-- No PostgreSQL, podemos usar a cláusula RETURNING para retornar o ID gerado automaticamente
-- Se você estiver usando um banco de dados diferente, consulte a documentação para obter a sintaxe correta
INSERT INTO artist (artistic_name, publisher_id, account_id)
VALUES ('Mizzy Miles', 2, (SELECT id FROM account WHERE username = 'mizzymiles'));

INSERT INTO artist (artistic_name, publisher_id, account_id)
VALUES ('GSon', 2, (SELECT id FROM account WHERE username = 'gsonwastaken'));

INSERT INTO song (ismn, name, release_date, genre, duration, artist_account_id, publisher_id)
VALUES (1, 'Europa', '2021-6-19', 'Pop', 180, 2, 2);

INSERT INTO song (ismn, name, release_date, genre, duration, artist_account_id, publisher_id)
VALUES (2, 'Voar', '2021-5-19', 'Hip-Pop', 180, 3, 2);

INSERT INTO streaming (consumer_account_id, datetime, song_ismn)
VALUES (1, '2021-6-19', 1);

INSERT INTO streaming (consumer_account_id, datetime, song_ismn)
VALUES (1, '2021-6-17', 1);

INSERT INTO streaming (consumer_account_id, datetime, song_ismn)
VALUES (1, '2021-6-12', 1);

INSERT INTO streaming (consumer_account_id, datetime, song_ismn)
VALUES (1, '2021-6-17', 2);

INSERT INTO streaming (consumer_account_id, datetime, song_ismn)
VALUES (1, '2021-6-1', 2);

INSERT INTO streaming (consumer_account_id, datetime, song_ismn)
VALUES (1, '2021-7-17', 2);