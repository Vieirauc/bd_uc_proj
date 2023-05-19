DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

CREATE TABLE account (
	id		 BIGSERIAL NOT NULL,
	username	 VARCHAR(512) NOT NULL,
	email	 VARCHAR(512) NOT NULL,
	password_hash CHAR(255) NOT NULL,
	address	 VARCHAR(512),
	PRIMARY KEY(id)
);

CREATE TABLE publisher (
	id SERIAL NOT NULL,
	name VARCHAR(512) NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE administrator (
	account_id BIGINT NOT NULL,
	PRIMARY KEY(account_id)
);

CREATE TABLE artist (
	artistic_name VARCHAR(512) NOT NULL,
	publisher_id	 INTEGER NOT NULL,
	account_id	 BIGINT NOT NULL,
	PRIMARY KEY(account_id)
);

CREATE TABLE consumer (
	premium		 BOOL DEFAULT False,
	top10_id INTEGER NOT NULL,
	account_id		 BIGINT NOT NULL,
	PRIMARY KEY(account_id)
);

CREATE TABLE playlist (
	isprivate		 BOOL NOT NULL DEFAULT True,
	consumer_account_id BIGINT NOT NULL,
	compilation_id	 INTEGER NOT NULL,
	PRIMARY KEY(compilation_id)
);

CREATE TABLE song (
	ismn		 INTEGER NOT NULL,
	name		 VARCHAR(512) NOT NULL,
	release_date	 TIMESTAMP NOT NULL,
	genre		 VARCHAR(512) NOT NULL,
	duration		 INTEGER NOT NULL,
	artist_account_id BIGINT NOT NULL,
	publisher_id	 INTEGER NOT NULL,
	PRIMARY KEY(ismn)
);

CREATE SEQUENCE card_id_seq AS BIGINT START WITH 1 INCREMENT BY 1;
CREATE TABLE card (
	id			 BIGINT NOT NULL,
	limit_date		 TIMESTAMP NOT NULL,
	amount			 FLOAT(8) NOT NULL,
	issue_date		 TIMESTAMP NOT NULL,
	--consumer_account_id	 BIGINT NOT NULL,
	administrator_account_id BIGINT NOT NULL,
	PRIMARY KEY(id)
);
ALTER SEQUENCE card_id_seq OWNED BY card.id;

CREATE TABLE album (
	artist_account_id BIGINT NOT NULL,
	compilation_id	 INTEGER NOT NULL,
	PRIMARY KEY(compilation_id)
);

CREATE TABLE subscription (
	id			 SERIAL NOT NULL,
	start_date		 DATE NOT NULL,
	limit_date		 DATE NOT NULL,
	type		 SMALLINT NOT NULL,
	cost		 FLOAT(8) NOT NULL,
	datetime		 TIMESTAMP NOT NULL,
	card_id		 BIGINT NOT NULL,
	consumer_account_id BIGINT NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE comment (
	id			 SERIAL NOT NULL,
	body		 TEXT NOT NULL,
	datetime		 TIMESTAMP NOT NULL,
	song_ismn		 INTEGER NOT NULL,
	consumer_account_id BIGINT NOT NULL,
	comment_id		 INTEGER , --estava NOT NULL no codigo do onda
	PRIMARY KEY(id)
);

CREATE TABLE streaming (
    id             SERIAL NOT NULL,
    datetime         TIMESTAMP NOT NULL,
    consumer_account_id BIGINT NOT NULL,
    song_ismn         INTEGER NOT NULL,
    PRIMARY KEY(id)
);

CREATE TABLE compilation (
	id	 SERIAL NOT NULL,
	nome VARCHAR(512),
	PRIMARY KEY(id)
);

CREATE TABLE position (
	id		 SERIAL NOT NULL,
	position	 SMALLINT NOT NULL,
	song_ismn	 INTEGER NOT NULL,
	compilation_id INTEGER NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE artist_song (
	artist_account_id BIGINT,
	song_ismn	 INTEGER,
	PRIMARY KEY(artist_account_id,song_ismn)
);

ALTER TABLE account ADD UNIQUE (username, email);
ALTER TABLE account ADD CONSTRAINT email CHECK (email LIKE '%@%');
ALTER TABLE administrator ADD CONSTRAINT administrator_fk1 FOREIGN KEY (account_id) REFERENCES account(id);
ALTER TABLE artist ADD UNIQUE (artistic_name);
ALTER TABLE artist ADD CONSTRAINT artist_fk1 FOREIGN KEY (publisher_id) REFERENCES publisher(id);
ALTER TABLE artist ADD CONSTRAINT artist_fk2 FOREIGN KEY (account_id) REFERENCES account(id);
ALTER TABLE consumer ADD UNIQUE (top10_id);
ALTER TABLE consumer ADD CONSTRAINT consumer_fk1 FOREIGN KEY (top10_id) REFERENCES playlist(compilation_id);
ALTER TABLE consumer ADD CONSTRAINT consumer_fk2 FOREIGN KEY (account_id) REFERENCES account(id);
ALTER TABLE playlist ADD CONSTRAINT playlist_fk1 FOREIGN KEY (consumer_account_id) REFERENCES consumer(account_id);
ALTER TABLE playlist ADD CONSTRAINT playlist_fk2 FOREIGN KEY (compilation_id) REFERENCES compilation(id);
ALTER TABLE song ADD CONSTRAINT song_fk1 FOREIGN KEY (artist_account_id) REFERENCES artist(account_id);
ALTER TABLE song ADD CONSTRAINT song_fk2 FOREIGN KEY (publisher_id) REFERENCES publisher(id);
ALTER TABLE song ADD CONSTRAINT duration CHECK (duration > 0);
--ALTER TABLE card ADD CONSTRAINT card_fk1 FOREIGN KEY (consumer_account_id) REFERENCES consumer(account_id);
ALTER TABLE card ADD CONSTRAINT card_fk2 FOREIGN KEY (administrator_account_id) REFERENCES administrator(account_id);
ALTER TABLE card ADD CONSTRAINT amount CHECK (amount >= 0 AND amount <= 50); -- alterado do onda para "amount >= 0 AND amount <= 50"
ALTER TABLE album ADD CONSTRAINT album_fk1 FOREIGN KEY (artist_account_id) REFERENCES artist(account_id);
ALTER TABLE album ADD CONSTRAINT album_fk2 FOREIGN KEY (compilation_id) REFERENCES compilation(id);
ALTER TABLE subscription ADD CONSTRAINT subscription_fk1 FOREIGN KEY (card_id) REFERENCES card(id);
ALTER TABLE subscription ADD CONSTRAINT subscription_fk2 FOREIGN KEY (consumer_account_id) REFERENCES consumer(account_id);
ALTER TABLE subscription ADD CONSTRAINT cost CHECK (cost > 0);
ALTER TABLE comment ADD CONSTRAINT comment_fk1 FOREIGN KEY (song_ismn) REFERENCES song(ismn);
ALTER TABLE comment ADD CONSTRAINT comment_fk2 FOREIGN KEY (consumer_account_id) REFERENCES consumer(account_id);
ALTER TABLE comment ADD CONSTRAINT comment_fk3 FOREIGN KEY (comment_id) REFERENCES comment(id);
ALTER TABLE streaming ADD CONSTRAINT streaming_fk1 FOREIGN KEY (consumer_account_id) REFERENCES consumer(account_id);
ALTER TABLE streaming ADD CONSTRAINT streaming_fk2 FOREIGN KEY (song_ismn) REFERENCES song(ismn);
ALTER TABLE position ADD CONSTRAINT position_fk1 FOREIGN KEY (song_ismn) REFERENCES song(ismn);
ALTER TABLE position ADD CONSTRAINT position_fk2 FOREIGN KEY (compilation_id) REFERENCES compilation(id);
ALTER TABLE artist_song ADD CONSTRAINT artist_song_fk1 FOREIGN KEY (artist_account_id) REFERENCES artist(account_id);
ALTER TABLE artist_song ADD CONSTRAINT artist_song_fk2 FOREIGN KEY (song_ismn) REFERENCES song(ismn);

-- Altere a constraint consumer_fk1 para ser deferrable
ALTER TABLE consumer
    ALTER CONSTRAINT consumer_fk1
    DEFERRABLE INITIALLY DEFERRED;


CREATE FUNCTION pseudo_encrypt(VALUE bigint) returns bigint AS $$
DECLARE
	l1 bigint;
	l2 bigint;
	r1 bigint;
	r2 bigint;
	i bigint:=0;
BEGIN
	l1:= (VALUE >> 12) & (4096-1);
	r1:= VALUE & (4096-1);
 WHILE i < 3 LOOP
	l2 := r1;
	r2 := l1 # ((((1366 * r1 + 150889) % 714025) / 714025.0) * (4096-1))::bigint;
	l1 := l2;
	r1 := r2;
	i := i + 1;
 END LOOP;
 RETURN ((l1 << 12) + r1);
END;
$$ LANGUAGE plpgsql strict immutable;

CREATE FUNCTION bounded_pseudo_encrypt(VALUE bigint, min bigint, max bigint) returns bigint AS $$
BEGIN
  --loop
	--value := pseudo_encrypt(value);
	--exit when value <= max;
  --end loop;
  value:= pseudo_encrypt(value);
  value:= CAST((2147483647 - value) as FLOAT)/2147483647 * (max - min) + min;
  return value;
END
$$ LANGUAGE plpgsql strict immutable;

CREATE OR REPLACE FUNCTION updateTop10()
RETURNS TRIGGER 
AS
$$
DECLARE
    idvar INTEGER;
    higher_pos INTEGER = 0;

BEGIN
    SELECT compilation_id INTO idvar FROM playlist WHERE consumer_account_id = NEW.consumer_account_id AND compilation_id IN (SELECT id FROM compilation WHERE nome IS NULL);

    SELECT MAX(position) INTO higher_pos FROM position WHERE compilation_id = idvar;

    IF higher_pos IS NULL THEN higher_pos := 0; END IF;

    IF (
        SELECT COUNT(*) FROM position
        WHERE compilation_id = idvar
          AND song_ismn = NEW.song_ismn
    ) = 0 AND higher_pos < 10 THEN
        INSERT INTO position (position, song_ismn, compilation_id)
        VALUES (higher_pos + 1, NEW.song_ismn, idvar);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER updateTop10
AFTER INSERT
ON streaming
FOR EACH ROW
EXECUTE PROCEDURE updateTop10();

BEGIN TRANSACTION;

-- Insert entries into the 'account' table
INSERT INTO account (username, password_hash, email)
VALUES
    ('admin1', 'admin1pass', 'admin1@example.com'),
    ('admin2', 'admin2pass', 'admin2@example.com'),
    ('consumer1', 'consumer1pass', 'consumer1@example.com'),
    ('consumer2', 'consumer2pass', 'consumer2@example.com'),
    ('consumer3', 'consumer3pass', 'consumer3@example.com'),
    ('consumer4', 'consumer4pass', 'consumer4@example.com'),
    ('artist1', 'artist1pass', 'artist1@example.com'),
    ('artist2', 'artist2pass', 'artist2@example.com'),
    ('artist3', 'artist3pass', 'artist3@example.com'),
    ('artist4', 'artist4pass', 'artist4@example.com');

-- Insert entries into the 'publisher' table
INSERT INTO publisher (name)
VALUES
    ('Publisher A'),
    ('Publisher B'),
    ('Publisher C'),
    ('Publisher D'),
    ('Publisher E'),
    ('Publisher F'),
    ('Publisher G'),
    ('Publisher H'),
    ('Publisher I'),
    ('Publisher J');

-- Insert entries into the 'administrator' table
INSERT INTO administrator (account_id)
VALUES
    (1),
    (2);

-- Insert entries into the 'artist' table
INSERT INTO artist (artistic_name, publisher_id, account_id)
VALUES
    ('Artist 1', 1, 7),
    ('Artist 2', 2, 8),
    ('Artist 3', 3, 9),
    ('Artist 4', 4, 10);

-- Insert entries into the 'compilation' table
INSERT INTO compilation (nome)
VALUES
    ('Compilation 1'),
    ('Compilation 2'),
    ('Compilation 3'),
    ('Compilation 4'),
    ('Compilation 5'),
    ('Compilation 6'),
    ('Compilation 7'),
    ('Compilation 8'),
    ('Compilation 9'),
    ('Compilation 10');

-- Insert entries into the 'consumer' table (top10 constraint will only be checked after commit (INNITIALLY DEFERRED))
INSERT INTO consumer (top10_id, account_id)
VALUES

    (1, 3),
    (2, 4),
    (3, 5),
    (4, 6);
-- Insert entries into the 'playlist' table
INSERT INTO playlist (isprivate, consumer_account_id, compilation_id)
VALUES

    (true, 3, 1),
    (false, 4, 2),
    (true, 5, 3),
    (false, 6, 4),
    (true, 6, 5),
    (false, 5, 6),
    (true, 4, 7),
    (false, 3, 8);





-- Insert entries into the 'song' table
INSERT INTO song (ismn, name, release_date, genre, duration, artist_account_id, publisher_id)
VALUES
    (1, 'Song 1', '2022-01-01', 'Genre 1', 180, 7, 1),
    (2, 'Song 2', '2022-02-01', 'Genre 2', 200, 8, 2),
    (3, 'Song 3', '2022-03-01', 'Genre 3', 220, 9, 3),
    (4, 'Song 4', '2022-04-01', 'Genre 4', 240, 10, 4),
    (5, 'Song 5', '2022-05-01', 'Genre 5', 260, 7, 5),
    (6, 'Song 6', '2022-06-01', 'Genre 6', 280, 8, 6),
    (7, 'Song 7', '2022-07-01', 'Genre 7', 300, 7, 7),
    (8, 'Song 8', '2022-08-01', 'Genre 8', 320, 8, 8),
    (9, 'Song 9', '2022-09-01', 'Genre 9', 340, 9, 9),
    (10, 'Song 10', '2022-10-01', 'Genre 10', 360, 10, 10);
COMMIT;

INSERT INTO streaming (consumer_account_id, datetime, song_ismn)
VALUES (3, '2021-6-19', 1);

INSERT INTO streaming (consumer_account_id, datetime, song_ismn)
VALUES (3, '2021-6-17', 1);

INSERT INTO streaming (consumer_account_id, datetime, song_ismn)
VALUES (3, '2021-6-12', 1);

INSERT INTO streaming (consumer_account_id, datetime, song_ismn)
VALUES (3, '2021-6-17', 2);

INSERT INTO streaming (consumer_account_id, datetime, song_ismn)
VALUES (3, '2021-6-1', 2);

INSERT INTO streaming (consumer_account_id, datetime, song_ismn)
VALUES (3, '2021-7-17', 2);

INSERT INTO streaming (consumer_account_id, datetime, song_ismn)
VALUES (3, '2021-7-19', 2);


