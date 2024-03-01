drop table if exists Crypto;
create table if not exists Crypto
(
    symbol          varchar(100),
    name            varchar(100),
    price_usd       real,
    market_cap_usd  real,
    market_cap_rank integer,
    snapshot_time   timestamp,
    PRIMARY KEY (symbol, snapshot_time)
);