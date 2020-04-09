CREATE TABLE guild_settings(
    guild_id BIGINT PRIMARY KEY,
    prefix VARCHAR(30),
    quote_channel_id BIGINT
);


CREATE TABLE user_quotes(
    quote_id VARCHAR(5) PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    text TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL
);


CREATE TABLE permanent_nicknames(
    guild_id BIGINT,
    user_id BIGINT,
    nickname VARCHAR(32),
    PRIMARY KEY (guild_id, user_id)
);
