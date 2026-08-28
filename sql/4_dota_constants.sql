/* 
SQL Tables Schema for Dota Constants

This file is separate because the tables for this are used by both IreBot and AluBot.
-*/
CREATE TABLE
    /* Dota Constants Items */
    IF NOT EXISTS dota_constants_items (
        item_id INT PRIMARY KEY,
        display_name TEXT NOT NULL
    );