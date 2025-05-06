## 1. Tool Catalogue

| Tool Function (Python)  | Purpose                               | Required Scope(s)                                   | Typical Caller                             |
| ----------------------- | ------------------------------------- | --------------------------------------------------- | ------------------------------------------ |
| `support_tool`          | Create / read support tickets         | `support.ticket.read`, `support.ticket.create`      | Internal & external users, internal agents |
| `actionable_deals_tool` | List actionable deals for partner *P* | `deals.read`                                        | Delegated agents (PXP → Workspan)          |
| `lci_telemetry_tool`    | Fetch LCI telemetry for partner *P*   | `lci_telemetry.read`                                | Same as above                              |
| `partner_profile_tool`  | Read / update partner profile         | `partner.profile.read`, `partner.profile.update`    | Internal agents, admin users               |
| `agent_registry_tool`   | Register / suspend agents             | `agent.registry.register`, `agent.registry.suspend` | Platform operators, CI pipelines           |
| `token_exchange_tool`   | Perform OAuth‑style token exchange    | `token.exchange`                                    | Any agent performing a delegated hop       |
| `audit_log_tool`        | Query immutable audit records         | `audit_log.read`                                    | Break‑glass auditors                       |
| `metrics_export_tool`   | Export aggregated metrics             | `metrics.export`                                    | System reports / cron jobs                 |

Use the same `@secure_tool` decorator pattern you already adopted; just change the `name`, `permissions_required`, and business logic.

---

## 2. Minimal SQLite Schema

```sql
-- file: schema.sql
CREATE TABLE partner (
    partner_id   TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    tier         TEXT CHECK(tier IN ('Gold','Silver','Bronze'))
);

CREATE TABLE deal (
    id           TEXT PRIMARY KEY,
    partner_id   TEXT NOT NULL,
    name         TEXT,
    next_step    TEXT,
    FOREIGN KEY (partner_id) REFERENCES partner(partner_id)
);

CREATE TABLE lci_telemetry (
    partner_id              TEXT PRIMARY KEY,
    adoption_score          INTEGER,
    weekly_active_users     INTEGER,
    feature_reports         INTEGER,
    feature_integrations    INTEGER,
    FOREIGN KEY (partner_id) REFERENCES partner(partner_id)
);

CREATE TABLE support_ticket (
    ticket_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_id   TEXT,
    issue        TEXT,
    status       TEXT DEFAULT 'open',
    created_at   TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (partner_id) REFERENCES partner(partner_id)
);
```

**Seed data**

```sql
INSERT INTO partner VALUES ('EPLUS','EPlus','Gold');
INSERT INTO deal VALUES
 ('D-001','EPLUS','Cloud Migration Suite','Send proposal'),
 ('D-002','EPLUS','Security Audit Package','Schedule demo');

INSERT INTO lci_telemetry
(partner_id,adoption_score,weekly_active_users,feature_reports,feature_integrations)
VALUES ('EPLUS',87,134,78,41);
```

Run:

```bash
sqlite3 agentictrust_demo.db < schema.sql
```

Store `agentictrust_demo.db` where your tools can open it read‑only (or read‑write for ticket creation).

---

## 3. Example Tool Implementation with SQLite

```python
import sqlite3
from pathlib import Path
from sdk.security.tool_security import secure_tool
from sdk.client import AgenticTrustClient

DB_FILE = Path(__file__).parent / "agentictrust_demo.db"
OAUTH_SERVER_URL = os.getenv("OAUTH_SERVER_URL", "http://localhost:8000")
client = AgenticTrustClient(api_base=OAUTH_SERVER_URL)

def _conn():
    # always open a short‑lived connection; WAL mode is fine for demo loads
    return sqlite3.connect(DB_FILE, isolation_level=None)

@secure_tool(
    name='actionable_deals',
    description='Retrieve actionable deals for a given partner',
    category='partner_data',
    permissions_required=['deals.read'],
    auto_register=True,
    client=client,
)
def actionable_deals_tool(partner: str):
    with _conn() as cx:
        rows = cx.execute(
            "SELECT id, name, next_step FROM deal WHERE partner_id = ?",
            (partner.upper(),)
        ).fetchall()
    deals = [dict(zip(('id','name','next_step'), r)) for r in rows]
    return {'partner': partner, 'deals': deals}

@secure_tool(
    name='support_ticket_create',
    description='Create a new support ticket for a partner',
    category='support',
    permissions_required=['support.ticket.create'],
    auto_register=True,
    client=client,
)
def support_ticket_create_tool(partner: str, issue: str):
    with _conn() as cx:
        cx.execute(
            "INSERT INTO support_ticket (partner_id, issue) VALUES (?, ?)",
            (partner.upper(), issue)
        )
        ticket_id = cx.execute("SELECT last_insert_rowid()").fetchone()[0]
    return {'ticket_id': ticket_id, 'status': 'open'}
```

Pattern:

* open the DB,
* run a scoped query,
* return dict/JSON,
* rely on the decorator to verify scopes **before** execution.

---

## 4. Policy Stub (OPA/Rego)

```rego
package agentictrust.tools

default allow = false

# ── deals.read ──────────────────────────────────────────────
allow {
    input.tool == "actionable_deals"
    input.requested_scopes == {"deals.read"}
    partner_allowed(input)
}

# ── support.ticket.create ───────────────────────────────────
allow {
    input.tool == "support_ticket_create"
    "support.ticket.create" in input.requested_scopes
    user_type_allowed(input)          # internal_user OR external_user
    partner_allowed(input)
}

# helper: ensures caller’s partner claim matches argument
partner_allowed(input) {
    input.token.claims.partner_id == upper(input.args.partner)
}

# helper: basic actor‑type allowlist
user_type_allowed(input) {
    input.token.claims.actor_type == "user-internal"
} else {
    input.token.claims.actor_type == "user-external"
}
```

*The decorator passes `input` (tool name, args, token, requested scopes) to the PDP; the PDP returns `allow=true/false`.*

---

### How to Extend

1. **Add a table** → create a new tool → give it a new scope string.
2. **Update the Rego** with a new `allow { … }` rule.
3. **Run your positive/negative scenario tests** (you already listed them earlier) in CI.

This gives you a working end‑to‑end skeleton: *SQLite data store ➜ secured tool functions ➜ fine‑grained scopes ➜ policy enforcement*.  Expand tables, tools, and scopes as your surface area grows.
