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