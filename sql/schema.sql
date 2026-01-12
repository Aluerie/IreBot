/* 
SQL Tables Schema for IreBot

Notes
-----
1. Table names here should start with `ttv_` to differentiate them from other tables in the database because 
the db is with my discord bot (so they both have access to the same data, i.e. my dota match history).
-*/
CREATE TABLE
    /* Twitch Oauth Tokens */
    IF NOT EXISTS ttv_tokens (
        user_id TEXT PRIMARY KEY,
        token TEXT NOT NULL,
        refresh TEXT NOT NULL,
        display TEXT,
        active BOOLEAN,
    );

CREATE TABLE
    IF NOT EXISTS ttv_chat_commands (
        command_name TEXT NOT NULL,
        content TEXT NOT NULL,
        streamer_id TEXT NOT NULL,
        PRIMARY KEY (streamer_id, command_name)
    );

CREATE TABLE
    IF NOT EXISTS ttv_counters (
        name TEXT NOT NULL PRIMARY KEY,
        VALUE BIGINT DEFAULT (0)
    );

CREATE TABLE
    IF NOT EXISTS ttv_first_redeems (
        user_id TEXT PRIMARY KEY,
        user_name TEXT NOT NULL,
        first_times BIGINT DEFAULT (1)
    );

CREATE TABLE
    IF NOT EXISTS ttv_dota_streamers (
        account_id BIGINT PRIMARY KEY,
        twitch_id TEXT NOT NULL,
        twitch_name TEXT NOT NULL,
        mmr INT DEFAULT (0),
        medal TEXT DEFAULT 'Unknown'
    );

CREATE TABLE
    IF NOT EXISTS ttv_dota_matches (
        match_id BIGINT NOT NULL,
        account_id BIGINT NOT NULL,
        PRIMARY KEY (match_id, account_id),
        hero_id INT NOT NULL,
        start_time TIMESTAMPTZ DEFAULT (NOW () AT TIME zone 'utc'),
        -- duration INTERVAL NOT NULL,
        -- kda TEXT NOT NULL,
        lobby_type INT NOT NULL,
        game_mode INT NOT NULL,
        team INT,
        outcome INT NOT NULL,
        CONSTRAINT fk_account FOREIGN KEY (account_id) REFERENCES ttv_dota_streamers (account_id) ON DELETE CASCADE
    );

CREATE TABLE
    IF NOT EXISTS ttv_stream_titles (
        title TEXT NOT NULL PRIMARY KEY,
        edit_time TIMESTAMPTZ DEFAULT (NOW () AT TIME zone 'utc')
    );

CREATE TABLE
    IF NOT EXISTS ttv_chatters (
        user_id TEXT PRIMARY KEY,
        name_lower TEXT NOT NULL
    );