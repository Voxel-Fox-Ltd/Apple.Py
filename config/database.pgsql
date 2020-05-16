CREATE TABLE guild_settings(
    guild_id BIGINT PRIMARY KEY,
    prefix VARCHAR(30),
    quote_channel_id BIGINT,
    automatic_nickname_update BOOLEAN DEFAULT FALSE
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


CREATE TABLE paypal_purchases(
    id VARCHAR(64) NOT NULL PRIMARY KEY,
    customer_id VARCHAR(18),
    item_name VARCHAR(200) NOT NULL,
    option_selection VARCHAR(200),
    payment_amount INTEGER NOT NULL,
    discord_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    checkout_complete_timestamp TIMESTAMP
);
