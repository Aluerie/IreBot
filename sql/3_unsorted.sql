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
    IF NOT EXISTS ttv_chatters (
        user_id TEXT PRIMARY KEY,
        name_lower TEXT NOT NULL
    );