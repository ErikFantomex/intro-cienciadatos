-- Apply this file explicitly to the existing MySQL instance after taking a backup.
-- It creates the new schema and intentionally leaves the old database untouched.
CREATE DATABASE IF NOT EXISTS crypto_db;
USE crypto_db;

CREATE TABLE IF NOT EXISTS cryptocurrencies (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    coin_id VARCHAR(100) NOT NULL UNIQUE,
    symbol VARCHAR(20),
    name VARCHAR(100),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS market_prices (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    cryptocurrency_id BIGINT NOT NULL,
    observed_at DATETIME NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'usd',
    price DECIMAL(30,10) NOT NULL,
    market_cap DECIMAL(36,2),
    total_volume DECIMAL(36,2),
    source VARCHAR(50) NOT NULL DEFAULT 'CoinGecko',
    ingested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_market_prices_cryptocurrency
        FOREIGN KEY (cryptocurrency_id) REFERENCES cryptocurrencies(id),
    CONSTRAINT uq_market_price_coin_time_currency
        UNIQUE (cryptocurrency_id, observed_at, currency),
    INDEX idx_market_prices_observed_at (observed_at),
    INDEX idx_market_prices_currency (currency),
    INDEX idx_market_prices_coin_observed_at (cryptocurrency_id, observed_at)
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    coin_id VARCHAR(100) NOT NULL,
    currency VARCHAR(10) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    records_received INT NOT NULL DEFAULT 0,
    records_stored INT NOT NULL DEFAULT 0,
    status VARCHAR(30) NOT NULL,
    error_message TEXT,
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME,
    INDEX idx_ingestion_runs_coin_id (coin_id),
    INDEX idx_ingestion_runs_status (status),
    INDEX idx_ingestion_runs_started_at (started_at)
);
