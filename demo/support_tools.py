import os
import sys
from pathlib import Path
import sqlite3
from typing import Optional, List, Dict, Any
import uuid

# Ensure project root in path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sdk.client import AgenticTrustClient
from sdk.security.tool_security import secure_tool

# Register tools automatically on import using AgenticTrust client
OAUTH_SERVER_URL = os.getenv("OAUTH_SERVER_URL", "http://localhost:8000")
client = AgenticTrustClient(api_base=OAUTH_SERVER_URL, debug=False)

# SQLite demo DB
DB_FILE = Path(__file__).parent / "agentictrust_demo.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS partner (
    partner_id   TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    tier         TEXT CHECK(tier IN ('Gold','Silver','Bronze'))
);
CREATE TABLE IF NOT EXISTS deal (
    id           TEXT PRIMARY KEY,
    partner_id   TEXT NOT NULL,
    name         TEXT,
    next_step    TEXT,
    FOREIGN KEY (partner_id) REFERENCES partner(partner_id)
);
CREATE TABLE IF NOT EXISTS lci_telemetry (
    partner_id              TEXT PRIMARY KEY,
    adoption_score          INTEGER,
    weekly_active_users     INTEGER,
    feature_reports         INTEGER,
    feature_integrations    INTEGER,
    FOREIGN KEY (partner_id) REFERENCES partner(partner_id)
);
CREATE TABLE IF NOT EXISTS support_ticket (
    ticket_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_id   TEXT,
    issue        TEXT,
    status       TEXT DEFAULT 'open',
    created_at   TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (partner_id) REFERENCES partner(partner_id)
);
"""

SEED_SQL = """
INSERT OR IGNORE INTO partner VALUES ('EPLUS','EPlus','Gold');
INSERT OR IGNORE INTO deal VALUES
 ('D-001','EPLUS','Cloud Migration Suite','Send proposal'),
 ('D-002','EPLUS','Security Audit Package','Schedule demo');
INSERT OR IGNORE INTO lci_telemetry
(partner_id,adoption_score,weekly_active_users,feature_reports,feature_integrations)
VALUES ('EPLUS',87,134,78,41);
"""

def _ensure_db() -> None:
    if DB_FILE.exists():
        return
    with sqlite3.connect(DB_FILE) as cx:
        cx.executescript(SCHEMA_SQL)
        cx.executescript(SEED_SQL)
    print(f"[SETUP] SQLite demo DB created at {DB_FILE}")

def _conn():
    _ensure_db()
    return sqlite3.connect(DB_FILE, isolation_level=None)

# Define secured support tool
@secure_tool(
    name='support_demo_v2',
    description='Customer support endpoint for ticket management',
    category='support',
    permissions_required=['support:ticket.read', 'support:ticket.create'],
    auto_register=True,
    client=client
)
def support_tool(issue: str = None, action: str = None):
    """Handle customer support ticket requests
    
    Args:
        issue: A description of the customer issue to address
        action: Specific action to take on the ticket
        
    Returns:
        A response object with the result of the support request
    """
    # Log the parameters for debugging
    print(f"Support tool called with issue: {issue}, action: {action}")
    
    return {'response': f'Handling support request: {issue or action}'}

@secure_tool(
    name='actionable_deals',
    description='Retrieve actionable deals for a given partner',
    category='partner_data',
    permissions_required=['deals.read'],
    auto_register=True,
    client=client
)
def actionable_deals_tool(partner: str):  
    """Return actionable deals from SQLite."""
    print(f"[TOOL] actionable_deals called for partner={partner}")
    with _conn() as cx:
        rows = cx.execute(
            "SELECT id, name, next_step FROM deal WHERE partner_id = ?",
            (partner.upper(),)
        ).fetchall()
    deals = [dict(zip(('id', 'name', 'next_step'), r)) for r in rows]
    return {'partner': partner, 'deals': deals}

@secure_tool(
    name='lci_telemetry',
    description='Retrieve LCI telemetry insights for a partner',
    category='partner_data',
    permissions_required=['lci_telemetry.read'],
    auto_register=True,
    client=client
)
def lci_telemetry_tool(partner: str):  
    """Return LCI telemetry from SQLite."""
    print(f"[TOOL] lci_telemetry called for partner={partner}")
    with _conn() as cx:
        row = cx.execute(
            "SELECT adoption_score, weekly_active_users, feature_reports, feature_integrations FROM lci_telemetry WHERE partner_id = ?",
            (partner.upper(),)
        ).fetchone()
    if not row:
        return {'partner': partner, 'telemetry': None}
    adoption_score, wau, feature_reports, feature_integrations = row
    return {
        'partner': partner,
        'telemetry': {
            'adoption_score': adoption_score,
            'weekly_active_users': wau,
            'feature_usage': {
                'reports': feature_reports,
                'integrations': feature_integrations,
            },
        }
    }
