INSERT INTO publisher (name)
VALUES ('Think Music Records');

INSERT INTO publisher (name)
VALUES ('Make More Music');

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
