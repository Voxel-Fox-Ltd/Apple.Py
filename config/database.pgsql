CREATE TABLE guild_settings(
    guild_id BIGINT PRIMARY KEY,
    prefix VARCHAR(30),
    quote_channel_id BIGINT,
    automatic_nickname_update BOOLEAN DEFAULT FALSE,
    rainbow_line_autodelete BOOLEAN DEFAULT FALSE,
    leaderboard_message_url VARCHAR(150),
    dump_stackoverflow_answers BOOLEAN DEFAULT FALSE
);


CREATE TABLE user_quotes(
    quote_id VARCHAR(5) PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    text TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL
);


CREATE TABLE quote_aliases(
    alias VARCHAR(2000) PRIMARY KEY,
    quote_id VARCHAR(5) REFERENCES user_quotes(quote_id) ON DELETE CASCADE
);


CREATE TABLE permanent_nicknames(
    guild_id BIGINT,
    user_id BIGINT,
    nickname VARCHAR(32),
    PRIMARY KEY (guild_id, user_id)
);


CREATE TABLE user_settings(
    user_id BIGINT PRIMARY KEY
);


CREATE TABLE role_list(
    guild_id BIGINT,
    role_id BIGINT,
    key VARCHAR(50),
    value VARCHAR(50),
    PRIMARY KEY (guild_id, role_id, key)
);


CREATE TABLE channel_list(
    guild_id BIGINT,
    channel_id BIGINT,
    key VARCHAR(50),
    value VARCHAR(50),
    PRIMARY KEY (guild_id, channel_id, key)
);


CREATE TABLE user_points(
    guild_id BIGINT,
    user_id BIGINT,
    points INTEGER DEFAULT 0,
    PRIMARY KEY (guild_id, user_id)
);
