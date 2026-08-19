-- Modèle en étoile du Data Warehouse (Jalon 4).
-- Tables et grain conformes à docs/data_dictionary.md.
-- Contraintes alignées sur docs/data_quality.md (AGENTS.md §4 : closing_stock = opening_stock + stock_in - quantity_sold).
--
-- IMPORTANT : les customer_id (UCI) et les visitorid (RetailRocket, table
-- fact_web_events) sont des espaces d'identifiants distincts, jamais fusionnés
-- par une contrainte de clé étrangère commune (cf. docs/data_dictionary.md,
-- "Note sur les espaces d'identifiants").

DROP TABLE IF EXISTS fact_web_events CASCADE;
DROP TABLE IF EXISTS fact_inventory CASCADE;
DROP TABLE IF EXISTS fact_sales CASCADE;
DROP TABLE IF EXISTS dim_promotion CASCADE;
DROP TABLE IF EXISTS dim_product CASCADE;
DROP TABLE IF EXISTS dim_customer CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;

CREATE TABLE dim_customer (
    customer_id         VARCHAR(20) PRIMARY KEY,
    age                 SMALLINT,
    gender              VARCHAR(10),
    city                VARCHAR(100),
    registration_date   TIMESTAMP
);

CREATE TABLE dim_product (
    product_id          VARCHAR(20) PRIMARY KEY,
    product_name        TEXT,
    category            VARCHAR(100),
    subcategory         VARCHAR(100),
    brand               VARCHAR(100),
    cost_price          NUMERIC(12, 2) CHECK (cost_price >= 0),
    base_price          NUMERIC(12, 2) CHECK (base_price >= 0),
    current_price        NUMERIC(12, 2) CHECK (current_price >= 0)
);

CREATE TABLE dim_date (
    date_id     INTEGER PRIMARY KEY,
    date        DATE NOT NULL,
    year        SMALLINT NOT NULL,
    month       SMALLINT NOT NULL,
    day         SMALLINT NOT NULL,
    weekday     SMALLINT NOT NULL,
    is_weekend  BOOLEAN NOT NULL
);

CREATE TABLE dim_promotion (
    promotion_id        VARCHAR(20) PRIMARY KEY,
    product_id          VARCHAR(20) NOT NULL REFERENCES dim_product(product_id),
    start_date          TIMESTAMP,
    end_date            TIMESTAMP,
    discount_percentage NUMERIC(5, 4) CHECK (discount_percentage >= 0 AND discount_percentage <= 1)
);

CREATE TABLE fact_sales (
    sale_id     BIGSERIAL PRIMARY KEY,
    order_id    VARCHAR(20) NOT NULL,
    customer_id VARCHAR(20) NOT NULL REFERENCES dim_customer(customer_id),
    product_id  VARCHAR(20) NOT NULL REFERENCES dim_product(product_id),
    date_id     INTEGER NOT NULL REFERENCES dim_date(date_id),
    quantity    INTEGER NOT NULL CHECK (quantity > 0),
    unit_price  NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
    discount    NUMERIC(5, 4) NOT NULL DEFAULT 0 CHECK (discount >= 0 AND discount <= 1),
    revenue     NUMERIC(14, 2) NOT NULL CHECK (revenue >= 0),
    cost        NUMERIC(14, 2) NOT NULL,
    margin      NUMERIC(14, 2) NOT NULL
    -- margin = revenue - cost : vérifié par l'ETL et les tests Pytest (tests/test_transformation.py),
    -- pas en CHECK SQL pour éviter les faux négatifs liés à l'arrondi flottant Python -> NUMERIC.
);

CREATE TABLE fact_inventory (
    product_id      VARCHAR(20) NOT NULL REFERENCES dim_product(product_id),
    date_id         INTEGER NOT NULL REFERENCES dim_date(date_id),
    opening_stock   INTEGER NOT NULL CHECK (opening_stock >= 0),
    stock_in        INTEGER NOT NULL CHECK (stock_in >= 0),
    quantity_sold   INTEGER NOT NULL CHECK (quantity_sold >= 0),
    closing_stock   INTEGER NOT NULL CHECK (closing_stock >= 0),
    PRIMARY KEY (product_id, date_id)
    -- closing_stock = opening_stock + stock_in - quantity_sold : vérifié par l'ETL et les tests
    -- Pytest (AGENTS.md §4), pas en CHECK SQL pour rester cohérent avec fact_sales ci-dessus.
);

-- fact_web_events : RetailRocket, espace d'identifiants indépendant (voir note en tête de fichier).
-- Pas de clé étrangère vers dim_customer/dim_product (visitorid/itemid ≠ customer_id/product_id UCI).
CREATE TABLE fact_web_events (
    event_id    VARCHAR(50) PRIMARY KEY,
    visitor_id  VARCHAR(20) NOT NULL,
    item_id     VARCHAR(20) NOT NULL,
    session_id  VARCHAR(50),
    event_type  VARCHAR(20) NOT NULL CHECK (event_type IN ('view', 'add_to_cart', 'remove_from_cart', 'purchase')),
    event_time  TIMESTAMP NOT NULL
);

CREATE INDEX idx_fact_sales_customer ON fact_sales(customer_id);
CREATE INDEX idx_fact_sales_product ON fact_sales(product_id);
CREATE INDEX idx_fact_sales_date ON fact_sales(date_id);
CREATE INDEX idx_fact_web_events_visitor ON fact_web_events(visitor_id);
CREATE INDEX idx_fact_web_events_item ON fact_web_events(item_id);
CREATE INDEX idx_fact_web_events_time ON fact_web_events(event_time);
