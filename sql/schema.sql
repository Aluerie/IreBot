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
    );

CREATE TABLE
    IF NOT EXISTS ttv_streamers (
        user_id TEXT PRIMARY KEY,
        display_name TEXT,
        active BOOLEAN DEFAULT (TRUE)
    );

CREATE TABLE
    IF NOT EXISTS ttv_dota_accounts (
        friend_id BIGINT PRIMARY KEY, -- steam32id (friend id) format;
        display_name TEXT NOT NULL,
        steam64_id BIGINT,
        estimated_mmr INT DEFAULT (0),
        medal TEXT DEFAULT 'Unknown',
        twitch_id TEXT NOT NULL,
        CONSTRAINT fk_twitch_id FOREIGN KEY (twitch_id) REFERENCES ttv_streamers (user_id) ON DELETE CASCADE,
    );

CREATE TABLE
    IF NOT EXISTS ttv_dota_completed_matches (
        match_id BIGINT PRIMARY KEY,
        start_time TIMESTAMPTZ DEFAULT (NOW () AT TIME zone 'utc'),
        lobby_type INT NOT NULL,
        game_mode INT NOT NULL,
        outcome INT NOT NULL -- Dire or Radiant, independent of players (this table has no player relation)
    );

CREATE TABLE
    IF NOT EXISTS ttv_dota_completed_match_players (
        friend_id BIGINT NOT NULL,
        match_id BIGINT NOT NULL,
        PRIMARY KEY (friend_id, match_id),
        hero_id INT NOT NULL,
        is_radiant BOOLEAN NOT NULL,
        abandon BOOLEAN NOT NULL,
        CONSTRAINT fk_account FOREIGN KEY (friend_id) REFERENCES ttv_dota_accounts (friend_id) ON DELETE CASCADE,
        CONSTRAINT fk_match FOREIGN KEY (match_id) REFERENCES ttv_dota_completed_matches (match_id) ON DELETE CASCADE
    );