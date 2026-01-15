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
    IF NOT EXISTS ttv_stream_titles (
        title TEXT NOT NULL PRIMARY KEY,
        edit_time TIMESTAMPTZ DEFAULT (NOW () AT TIME zone 'utc')
    );

CREATE TABLE
    IF NOT EXISTS ttv_chatters (
        user_id TEXT PRIMARY KEY,
        name_lower TEXT NOT NULL
    );