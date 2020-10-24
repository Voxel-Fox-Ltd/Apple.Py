CREATE TABLE IF NOT EXISTS guild_settings(
    guild_id BIGINT PRIMARY KEY,
    prefix VARCHAR(30),
    quote_channel_id BIGINT,
    automatic_nickname_update BOOLEAN DEFAULT FALSE,
    rainbow_line_autodelete BOOLEAN DEFAULT FALSE,
    leaderboard_message_url VARCHAR(150),
    dump_stackoverflow_answers BOOLEAN DEFAULT FALSE,
    nickname_banned_role_id BIGINT
);


CREATE TABLE IF NOT EXISTS user_settings(
    user_id BIGINT PRIMARY KEY,
    twitch_user_id VARCHAR(16),
    twitch_username VARCHAR(32),
    twitch_bearer_token VARCHAR(30),
    twitch_cursor VARCHAR(100)
);


CREATE TABLE IF NOT EXISTS user_quotes(
    quote_id VARCHAR(5) PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    timestamp TIMESTAMP NOT NULL
);


CREATE TABLE IF NOT EXISTS quote_aliases(
    alias VARCHAR(2000) PRIMARY KEY,
    quote_id VARCHAR(5) REFERENCES user_quotes(quote_id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS permanent_nicknames(
    guild_id BIGINT,
    user_id BIGINT,
    nickname VARCHAR(32),
    PRIMARY KEY (guild_id, user_id)
);


CREATE TABLE IF NOT EXISTS role_list(
    guild_id BIGINT,
    role_id BIGINT,
    key VARCHAR(50),
    value VARCHAR(50),
    PRIMARY KEY (guild_id, role_id, key)
);


CREATE TABLE IF NOT EXISTS channel_list(
    guild_id BIGINT,
    channel_id BIGINT,
    key VARCHAR(50),
    value VARCHAR(50),
    PRIMARY KEY (guild_id, channel_id, key)
);


CREATE TABLE IF NOT EXISTS user_points(
    guild_id BIGINT,
    user_id BIGINT,
    points INTEGER DEFAULT 0,
    PRIMARY KEY (guild_id, user_id)
);
