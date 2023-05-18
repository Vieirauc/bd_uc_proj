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
	premium		 BOOL NOT NULL,
	playlist_compilation_id INTEGER NOT NULL,
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

CREATE TABLE card (
	id			 BIGINT NOT NULL,
	limit_date		 TIMESTAMP NOT NULL,
	amount			 FLOAT(8) NOT NULL,
	issue_date		 TIMESTAMP NOT NULL,
	consumer_account_id	 BIGINT NOT NULL,
	administrator_account_id BIGINT NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE album (
	artist_account_id BIGINT NOT NULL,
	compilation_id	 INTEGER NOT NULL,
	PRIMARY KEY(compilation_id)
);

CREATE TABLE subscripton (
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
	comment_id		 INTEGER NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE streaming (
	id			 SERIAL NOT NULL,
	streams		 INTEGER NOT NULL DEFAULT 0,
	consumer_account_id BIGINT NOT NULL,
	song_ismn		 INTEGER NOT NULL,
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
ALTER TABLE consumer ADD UNIQUE (playlist_compilation_id);
ALTER TABLE consumer ADD CONSTRAINT consumer_fk1 FOREIGN KEY (playlist_compilation_id) REFERENCES playlist(compilation_id);
ALTER TABLE consumer ADD CONSTRAINT consumer_fk2 FOREIGN KEY (account_id) REFERENCES account(id);
ALTER TABLE playlist ADD CONSTRAINT playlist_fk1 FOREIGN KEY (consumer_account_id) REFERENCES consumer(account_id);
ALTER TABLE playlist ADD CONSTRAINT playlist_fk2 FOREIGN KEY (compilation_id) REFERENCES compilation(id);
ALTER TABLE song ADD CONSTRAINT song_fk1 FOREIGN KEY (artist_account_id) REFERENCES artist(account_id);
ALTER TABLE song ADD CONSTRAINT song_fk2 FOREIGN KEY (publisher_id) REFERENCES publisher(id);
ALTER TABLE song ADD CONSTRAINT duration CHECK (duration > 0);
ALTER TABLE card ADD CONSTRAINT card_fk1 FOREIGN KEY (consumer_account_id) REFERENCES consumer(account_id);
ALTER TABLE card ADD CONSTRAINT card_fk2 FOREIGN KEY (administrator_account_id) REFERENCES administrator(account_id);
ALTER TABLE card ADD CONSTRAINT amount CHECK (amount > 0 AND amount < 50);
ALTER TABLE album ADD CONSTRAINT album_fk1 FOREIGN KEY (artist_account_id) REFERENCES artist(account_id);
ALTER TABLE album ADD CONSTRAINT album_fk2 FOREIGN KEY (compilation_id) REFERENCES compilation(id);
ALTER TABLE subscripton ADD CONSTRAINT subscripton_fk1 FOREIGN KEY (card_id) REFERENCES card(id);
ALTER TABLE subscripton ADD CONSTRAINT subscripton_fk2 FOREIGN KEY (consumer_account_id) REFERENCES consumer(account_id);
ALTER TABLE subscripton ADD CONSTRAINT cost CHECK (cost > 0);
ALTER TABLE comment ADD CONSTRAINT comment_fk1 FOREIGN KEY (song_ismn) REFERENCES song(ismn);
ALTER TABLE comment ADD CONSTRAINT comment_fk2 FOREIGN KEY (consumer_account_id) REFERENCES consumer(account_id);
ALTER TABLE comment ADD CONSTRAINT comment_fk3 FOREIGN KEY (comment_id) REFERENCES comment(id);
ALTER TABLE streaming ADD CONSTRAINT streaming_fk1 FOREIGN KEY (consumer_account_id) REFERENCES consumer(account_id);
ALTER TABLE streaming ADD CONSTRAINT streaming_fk2 FOREIGN KEY (song_ismn) REFERENCES song(ismn);
ALTER TABLE position ADD CONSTRAINT position_fk1 FOREIGN KEY (song_ismn) REFERENCES song(ismn);
ALTER TABLE position ADD CONSTRAINT position_fk2 FOREIGN KEY (compilation_id) REFERENCES compilation(id);
ALTER TABLE artist_song ADD CONSTRAINT artist_song_fk1 FOREIGN KEY (artist_account_id) REFERENCES artist(account_id);
ALTER TABLE artist_song ADD CONSTRAINT artist_song_fk2 FOREIGN KEY (song_ismn) REFERENCES song(ismn);

INSERT INTO publisher (name) VALUES ('Think Music Records');