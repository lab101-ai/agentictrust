-- init_workspan.sql
-- SQLite schema and sample data for Workspan Analytics DB (workspan_core)

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Drop existing tables to allow idempotent re-runs
-- ---------------------------------------------------------------------------
-- Drop tables in reverse FK dependency order
DROP TABLE IF EXISTS insight_actions;
DROP TABLE IF EXISTS insights;
DROP TABLE IF EXISTS partner_benchmarks;
DROP TABLE IF EXISTS partner_scores;
DROP TABLE IF EXISTS user_partner_access;
DROP TABLE IF EXISTS telemetry_metrics;
DROP TABLE IF EXISTS deal_attributes;
DROP TABLE IF EXISTS deals;
DROP TABLE IF EXISTS company_partner_map;
DROP TABLE IF EXISTS company_data_feeds;
DROP TABLE IF EXISTS etl_audit;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS partners;
DROP TABLE IF EXISTS user_profiles;
DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS benchmark_dimensions;

-- ---------------------------------------------------------------------------
-- Table definitions
-- ---------------------------------------------------------------------------

CREATE TABLE companies (
    company_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT  NOT NULL,
    hq_country   TEXT,
    industry     TEXT
);

CREATE TABLE company_data_feeds (
    feed_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    feed_type TEXT,
    schedule  TEXT,
    last_run_ts DATETIME,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE partners (
    partner_id INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_name    TEXT NOT NULL,
    ultimate_parent TEXT,
    hq_country      TEXT
);

CREATE TABLE company_partner_map (
    company_id INTEGER NOT NULL,
    partner_id INTEGER NOT NULL,
    company_partner_key TEXT,
    PRIMARY KEY (company_id, partner_id),
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    FOREIGN KEY (partner_id) REFERENCES partners(partner_id)
);

CREATE TABLE products (
    product_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    category     TEXT,
    company_id   INTEGER,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE user_profiles (
    profile_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT UNIQUE,
    first_name  TEXT,
    last_name   TEXT,
    company_id  INTEGER NOT NULL,
    role        TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

-- Workspan portal users (execs + sales; analysts removed)
-- Create companies first
INSERT INTO companies (company_name, hq_country, industry) VALUES
 ("Cisco",  "USA", "Technology"),
 ("Google", "USA", "Technology"),
 ("Meta",   "USA", "Technology");

-- Then add users
INSERT INTO user_profiles (profile_id, email, first_name, last_name, company_id, role) VALUES
 (1, "cmeyer@cisco.com",     "Carol",  "Meyer",   1, "executive"),
 (3, "epatel@cisco.com",     "Eve",    "Patel",   1, "executive"),
 (4, "gkim@cisco.com",       "Grace",  "Kim",     1, "sales"),
 (5, "hfu@cisco.com",        "Henry",  "Fu",      1, "sales"),
 (6, "gking@google.com",     "Gina",   "King",    2, "executive"),
 (7, "hyoung@google.com",    "Harold", "Young",   2, "executive"),
 (8, "idavis@google.com",    "Ivan",   "Davis",   2, "sales"),
 (9, "jroberts@meta.com",    "Julia",  "Roberts", 3, "executive"),
 (10,"kwright@meta.com",     "Kevin",  "Wright",  3, "executive"),
 (11,"lgreen@meta.com",      "Liam",   "Green",   3, "sales");



CREATE TABLE deals (
    deal_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id  INTEGER NOT NULL,
    partner_id  INTEGER NOT NULL,
    product_id  INTEGER NOT NULL,
    amount_usd  REAL,
    stage       TEXT,
    close_dt    DATE,
    owner_profile_id INTEGER NOT NULL,
    is_actionable INTEGER DEFAULT 0,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    FOREIGN KEY (partner_id) REFERENCES partners(partner_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (owner_profile_id) REFERENCES user_profiles(profile_id)
);

CREATE TABLE deal_attributes (
    deal_id    INTEGER NOT NULL,
    attr_name  TEXT NOT NULL,
    attr_value TEXT,
    PRIMARY KEY (deal_id, attr_name),
    FOREIGN KEY (deal_id) REFERENCES deals(deal_id)
);

CREATE TABLE telemetry_metrics (
    metric_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id  INTEGER NOT NULL,
    partner_id  INTEGER NOT NULL,
    metric_name TEXT,
    metric_value REAL,
    captured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    FOREIGN KEY (partner_id) REFERENCES partners(partner_id)
);

CREATE TABLE partner_scores (
    partner_id INTEGER NOT NULL,
    score_dt   DATE    NOT NULL,
    score_type TEXT    NOT NULL,
    company_id INTEGER NOT NULL,
    score_value REAL,
    PRIMARY KEY (partner_id, score_dt, score_type),
    FOREIGN KEY (partner_id) REFERENCES partners(partner_id),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE benchmark_dimensions (
    dimension_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dimension_name  TEXT,
    dimension_value TEXT
);

CREATE TABLE partner_benchmarks (
    dimension_id INTEGER NOT NULL,
    partner_id   INTEGER NOT NULL,
    metric_name  TEXT NOT NULL,
    company_id   INTEGER NOT NULL,
    partner_metric_value REAL,
    cohort_avg_value    REAL,
    variance            REAL,
    PRIMARY KEY (dimension_id, partner_id, metric_name),
    FOREIGN KEY (dimension_id) REFERENCES benchmark_dimensions(dimension_id),
    FOREIGN KEY (partner_id)   REFERENCES partners(partner_id),
    FOREIGN KEY (company_id)   REFERENCES companies(company_id)
);

CREATE TABLE insights (
    insight_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_id  INTEGER NOT NULL,
    company_id  INTEGER NOT NULL,
    insight_txt TEXT,
    severity    TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (partner_id) REFERENCES partners(partner_id),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE insight_actions (
    action_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_id  INTEGER NOT NULL,
    action_txt  TEXT,
    priority    TEXT,
    status      TEXT,
    FOREIGN KEY (insight_id) REFERENCES insights(insight_id)
);

CREATE TABLE user_partner_access (
    profile_id INTEGER NOT NULL,
    partner_id INTEGER NOT NULL,
    PRIMARY KEY (profile_id, partner_id),
    FOREIGN KEY (profile_id) REFERENCES user_profiles(profile_id),
    FOREIGN KEY (partner_id) REFERENCES partners(partner_id)
);

CREATE TABLE etl_audit (
    run_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id  INTEGER NOT NULL,
    feed_id     INTEGER,
    run_ts      DATETIME DEFAULT CURRENT_TIMESTAMP,
    records_ingested INTEGER,
    status      TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    FOREIGN KEY (feed_id) REFERENCES company_data_feeds(feed_id)
);

-- ---------------------------------------------------------------------------
-- Sample seed data
-- ---------------------------------------------------------------------------

-- Partners (reuse Cisco partner names for demo)
INSERT INTO partners (partner_name, ultimate_parent, hq_country) VALUES
 ("Acme Corp", NULL, "USA"),
 ("Globex",    NULL, "Canada");

-- Map Cisco company to its partners
INSERT INTO company_partner_map (company_id, partner_id, company_partner_key) VALUES
 (1, 1, "CRM123"),
 (1, 2, "CRM456");

-- Products (one shared demo product)
INSERT INTO products (product_name, category, company_id) VALUES
 ("Webex Suite", "Collaboration", NULL);

-- Deals across companies
INSERT INTO deals (company_id, partner_id, product_id, amount_usd, stage, close_dt, owner_profile_id, is_actionable) VALUES
  -- Cisco deals (company_id = 1)
 (1, 1, 1, 250000, "Negotiation", "2025-06-30", 4, 1),
 (1, 2, 1, 150000, "Proposal",    "2025-07-05", 5, 0),
 (1, 1, 1, 300000, "Qualified",   "2025-05-20", 4, 1),
 (1, 2, 1,  80000, "Prospecting", "2025-08-10", 5, 0),
 (1, 1, 1, 120000, "Negotiation", "2025-06-15", 4, 1),
 (1, 2, 1,  95000, "Closed Won",  "2025-03-18", 5, 0),
 (1, 1, 1, 175000, "Proposal",    "2025-09-01", 4, 1),
 (1, 2, 1, 110000, "Qualified",   "2025-06-25", 5, 0),
 (1, 1, 1, 400000, "Prospecting", "2025-09-12", 4, 0),
 (1, 2, 1, 130000, "Negotiation", "2025-07-30", 5, 1),
  -- Google deals (company_id = 2)
 (2, 1, 1, 100000, "Prospecting", "2025-07-15", 8, 0),
 (2, 1, 1, 180000, "Proposal",    "2025-08-05", 8, 1),
 (2, 1, 1, 220000, "Negotiation", "2025-06-28", 8, 1),
 (2, 1, 1,  90000, "Qualified",   "2025-05-30", 8, 0),
 (2, 1, 1,  75000, "Closed Won",  "2025-04-12", 8, 0),
 (2, 1, 1, 140000, "Proposal",    "2025-09-08", 8, 1),
 (2, 1, 1, 200000, "Negotiation", "2025-07-01", 8, 1),
 (2, 1, 1, 160000, "Prospecting", "2025-08-22", 8, 0),
 (2, 1, 1, 130000, "Qualified",   "2025-06-11", 8, 0),
 (2, 1, 1, 210000, "Negotiation", "2025-10-02", 8, 1),
 -- Meta deals (company_id = 3)
 (3, 2, 1,  75000, "Closed Won",  "2025-05-20", 11, 0),
 (3, 2, 1,  95000, "Prospecting", "2025-06-30", 11, 0),
 (3, 2, 1, 120000, "Negotiation", "2025-07-12", 11, 1),
 (3, 2, 1, 105000, "Proposal",    "2025-08-03", 11, 1),
 (3, 2, 1,  88000, "Qualified",   "2025-07-25", 11, 0),
 (3, 2, 1,  99000, "Negotiation", "2025-06-18", 11, 1),
 (3, 2, 1, 115000, "Proposal",    "2025-09-14", 11, 1),
 (3, 2, 1, 102000, "Prospecting", "2025-08-19", 11, 0),
 (3, 2, 1, 128000, "Negotiation", "2025-10-05", 11, 1),
 (3, 2, 1,  86000, "Qualified",   "2025-05-28", 11, 0);

-- Telemetry metrics
INSERT INTO telemetry_metrics (company_id, partner_id, metric_name, metric_value) VALUES
 (1, 1, "active_users", 120),
 (1, 2, "active_users", 80),
 (2, 1, "active_users", 200);

-- Partner scores
INSERT INTO partner_scores (partner_id, score_dt, score_type, company_id, score_value) VALUES
 (1, "2025-05-06", "adoption", 1, 75.0),
 (2, "2025-05-06", "adoption", 1, 60.0),
 (1, "2025-05-07", "adoption", 2, 82.5);

-- Partner access for sales users
INSERT INTO user_partner_access (profile_id, partner_id) VALUES
 (4, 1), (4, 2),
 (5, 1), (5, 2),
 (8, 1), (8, 2),
 (11,1), (11,2);

-- (companies already inserted above)
