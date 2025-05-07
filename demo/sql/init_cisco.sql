-- init_cisco.sql
-- SQLite schema and sample data for Cisco Operational DB (cisco_ops)

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Drop existing tables to allow the script to be re-run idempotently
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS partner_region_map;
DROP TABLE IF EXISTS adoption_components;
DROP TABLE IF EXISTS adoption_scores;
DROP TABLE IF EXISTS lci_telemetry;
DROP TABLE IF EXISTS deal_notes;
DROP TABLE IF EXISTS deal_actions;
DROP TABLE IF EXISTS deals;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS contacts;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS region_dim;
DROP TABLE IF EXISTS partners;
DROP TABLE IF EXISTS etl_runs;

-- ---------------------------------------------------------------------------
-- Table definitions
-- ---------------------------------------------------------------------------

CREATE TABLE partners (
    partner_id INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_name     TEXT NOT NULL,
    partner_tier     TEXT,
    country          TEXT,
    industry         TEXT,
    crm_account_id   TEXT
);

CREATE TABLE contacts (
    contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_id INTEGER NOT NULL,
    first_name TEXT,
    last_name  TEXT,
    email      TEXT UNIQUE,
    role       TEXT,
    FOREIGN KEY (partner_id) REFERENCES partners(partner_id)
);

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT UNIQUE,
    first_name  TEXT,
    last_name   TEXT,
    department  TEXT
);

CREATE TABLE products (
    product_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    segment      TEXT,
    family       TEXT
);

CREATE TABLE deals (
    deal_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_id  INTEGER NOT NULL,
    product_id  INTEGER NOT NULL,
    amount_usd  REAL,
    stage       TEXT,
    close_dt    DATE,
    owner_user_id INTEGER NOT NULL,
    is_actionable INTEGER DEFAULT 0,
    FOREIGN KEY (partner_id) REFERENCES partners(partner_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (owner_user_id) REFERENCES users(user_id)
);

CREATE TABLE deal_notes (
    note_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id   INTEGER NOT NULL,
    user_id   INTEGER NOT NULL,
    note_txt  TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (deal_id) REFERENCES deals(deal_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE lci_telemetry (
    telemetry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_id   INTEGER NOT NULL,
    metric_name  TEXT,
    metric_value REAL,
    captured_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (partner_id) REFERENCES partners(partner_id)
);

CREATE TABLE adoption_scores (
    partner_id  INTEGER NOT NULL,
    score_dt    DATE    NOT NULL,
    score_value REAL,
    score_breakdown_json TEXT,
    PRIMARY KEY (partner_id, score_dt),
    FOREIGN KEY (partner_id) REFERENCES partners(partner_id)
);

CREATE TABLE adoption_components (
    partner_id     INTEGER NOT NULL,
    component_id   INTEGER NOT NULL,
    score_dt       DATE    NOT NULL,
    component_name TEXT,
    component_score REAL,
    PRIMARY KEY (partner_id, component_id, score_dt),
    FOREIGN KEY (partner_id, score_dt) REFERENCES adoption_scores(partner_id, score_dt)
);

CREATE TABLE deal_actions (
    action_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id      INTEGER NOT NULL,
    action_txt   TEXT,
    owner_user_id INTEGER,
    due_dt       DATE,
    status       TEXT,
    FOREIGN KEY (deal_id)      REFERENCES deals(deal_id),
    FOREIGN KEY (owner_user_id) REFERENCES users(user_id)
);

CREATE TABLE region_dim (
    region_id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_name        TEXT,
    geo_hierarchy_json TEXT
);

CREATE TABLE partner_region_map (
    partner_id INTEGER NOT NULL,
    region_id  INTEGER NOT NULL,
    PRIMARY KEY (partner_id, region_id),
    FOREIGN KEY (partner_id) REFERENCES partners(partner_id),
    FOREIGN KEY (region_id)  REFERENCES region_dim(region_id)
);

CREATE TABLE etl_runs (
    run_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_name    TEXT,
    run_ts       DATETIME DEFAULT CURRENT_TIMESTAMP,
    records_sent INTEGER,
    status       TEXT
);

-- ---------------------------------------------------------------------------
-- Sample seed data
-- ---------------------------------------------------------------------------

INSERT INTO partners (partner_name, partner_tier, country, industry, crm_account_id)
VALUES
 ("Acme Corp",  "Gold",   "USA",    "Manufacturing", "CRM123"),
 ("Globex",     "Silver", "Canada", "Technology",    "CRM456");

INSERT INTO users (email, first_name, last_name, department) VALUES
 ("asmith@cisco.com",    "Alice",  "Smith",  "Sales"),
 ("bjones@cisco.com",    "Bob",    "Jones",  "Marketing"),
 ("cmeyer@cisco.com",    "Carol",  "Meyer",  "Executive"),
 ("dnguyen@cisco.com",   "David",  "Nguyen", "Executive"),
 ("epatel@cisco.com",    "Eve",    "Patel",  "Executive"),
 ("flee@cisco.com",      "Frank",  "Lee",    "Strategy"),
 ("gkim@cisco.com",      "Grace",  "Kim",    "Sales"),
 ("hfu@cisco.com",       "Henry",  "Fu",     "Sales"),
 ("ichen@cisco.com",     "Ivy",    "Chen",   "Marketing"),
 ("jbrown@cisco.com",    "Jack",   "Brown",  "Support");

INSERT INTO products (product_name, segment, family) VALUES
 ("Cisco SecureX", "Security",      "SecureX"),
 ("Cisco Webex",   "Collaboration", "Webex");

INSERT INTO deals (partner_id, product_id, amount_usd, stage, close_dt, owner_user_id, is_actionable) VALUES
 (1, 1, 250000, "Negotiation", "2025-06-30", 7, 1),
 (1, 2, 180000, "Proposal",    "2025-07-10", 8, 0),
 (2, 1,  90000, "Prospecting", "2025-07-25", 7, 0),
 (2, 2,  50000, "Closed Won",  "2025-04-15", 8, 0),
 (1, 1, 300000, "Qualified",   "2025-05-20", 7, 1),
 (2, 2, 120000, "Negotiation", "2025-06-05", 8, 1),
 (1, 2,  95000, "Closed Won",  "2025-03-18", 7, 0),
 (2, 1,  60000, "Proposal",    "2025-08-01", 8, 1),
 (1, 1, 400000, "Prospecting", "2025-09-12", 7, 0),
 (2, 2, 110000, "Qualified",   "2025-06-22", 8, 1);

INSERT INTO deal_notes (deal_id, user_id, note_txt) VALUES
 (1, 1, "Need executive approval"),
 (2, 2, "Deal closed successfully");

INSERT INTO region_dim (region_name, geo_hierarchy_json) VALUES
 ("North America", '{"continent":"North America"}');

INSERT INTO partner_region_map (partner_id, region_id) VALUES
 (1, 1),
 (2, 1);
