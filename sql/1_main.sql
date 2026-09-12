/* 
SQL Tables Schema for IreBot

Notes
-----
1. Table names used for IreBot should start with `ttv_` to differentiate them from other tables in the database that are used
by AluBot.
-*/
CREATE TABLE
    /* Twitch Oauth Tokens */
    IF NOT EXISTS ttv_tokens (
        user_id TEXT PRIMARY KEY,
        token TEXT NOT NULL,
        refresh TEXT NOT NULL
    );

CREATE TABLE
    /* Tags */
    IF NOT EXISTS ttv_tags (
        tag_name TEXT PRIMARY KEY,
        tag_content TEXT NOT NULL
    );

CREATE TABLE
    /* Cycling Emote Rewards */
    IF NOT EXISTS ttv_cycling_emote_rewards (
        streamer_id TEXT PRIMARY KEY,
        reward_id TEXT NOT NULL,
        emote_limit INT NOT NULL
    );

CREATE TABLE
    /* Cycling Emotes */
    IF NOT EXISTS ttv_cycling_emotes (
        id SERIAL PRIMARY KEY,
        emote_id TEXT NOT NULL,
        streamer_id TEXT NOT NULL,
        emote_set_id TEXT NOT NULL,
        added_at TIMESTAMPTZ DEFAULT (NOW () AT TIME zone 'utc'),
        requested_by TEXT NOT NULL -- twitch_id string;
    );

CREATE TABLE
    /* First Chatter Channel Reward Redeems
    
    Contains records of how many times a person redeemed 'First' channel reward
    for streamers in the database. 
     */
    IF NOT EXISTS ttv_first_chatter_redeems (
        user_id TEXT,
        streamer_id TEXT,
        PRIMARY KEY (user_id, streamer_id),
        first_times INT DEFAULT (1)
    );

CREATE TABLE
    /* First Chatter Channel Rewards 
    
    Contains relation between streamers and their 'First' Channel Reward, if they have it set up.
     */
    IF NOT EXISTS ttv_first_chatter_rewards (
        streamer_id TEXT PRIMARY KEY,
        reward_id TEXT NOT NULL,
        original_title TEXT
    );