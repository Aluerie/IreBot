CREATE TABLE
    IF NOT EXISTS ttv_counters (
        name TEXT NOT NULL PRIMARY KEY,
        VALUE BIGINT DEFAULT (0)
    );

CREATE TABLE
    IF NOT EXISTS ttv_chatters (
        user_id TEXT PRIMARY KEY,
        name_lower TEXT NOT NULL
    );