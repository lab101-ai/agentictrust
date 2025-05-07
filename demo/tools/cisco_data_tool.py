import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Database file configuration (consistent with cisco_app.py)
ROOT_DIR = Path(__file__).resolve().parent.parent  # demo/
DATA_DIR = ROOT_DIR / "data"
DB_FILE = DATA_DIR / "cisco_ops.db"

def init_db_from_sql_file(sql_file_path: str):
    """Initializes/Re-initializes the database from a given SQL script file."""
    print(f"DB_FILE absolute path: {DB_FILE.resolve()}")
    print(f"DB_FILE exists: {os.path.exists(DB_FILE)}")
    print(f"DATA_DIR absolute path: {DATA_DIR.resolve()}")
    print(f"DATA_DIR exists: {os.path.exists(DATA_DIR)}")
    
    if os.path.exists(DB_FILE):
        try:
            print(f"Removing existing database file: {DB_FILE}")
            os.remove(DB_FILE)
            print("Database file successfully removed")
        except OSError as e:
            print(f"Error removing database file {DB_FILE}: {e}")
            # Consider if error propagation is needed
    
    db_dir = os.path.dirname(DB_FILE)
    if not os.path.exists(db_dir):
        try:
            print(f"Creating database directory: {db_dir}")
            os.makedirs(db_dir)
            print(f"Successfully created database directory: {db_dir}")
        except OSError as e:
            print(f"Error creating directory {db_dir}: {e}")
            return # Cannot proceed if directory creation fails

    print(f"Connecting to SQLite database: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        print(f"Reading SQL script from file: {sql_file_path}")
        with open(sql_file_path, 'r') as f:
            sql_script = f.read()
        print("Executing SQL script...")
        cursor.executescript(sql_script)
        conn.commit()
        print(f"Database {DB_FILE} initialized successfully from {sql_file_path}.")
    except Exception as e:
        print(f"Error initializing database from {sql_file_path}: {e}")
    finally:
        conn.close()
        print("Database connection closed")

# --- Database Connection Utility ---
def get_db_connection() -> sqlite3.Connection:
    """Establishes a connection to the SQLite database."""
    if not os.path.exists(DB_FILE):
        print(f"Warning: Database file {DB_FILE} does not exist when trying to connect!")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

# --- Tool Functions ---

def get_all_partners() -> List[Dict[str, Any]]:
    """Retrieves all partners from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT partner_id, partner_name, partner_tier, country, industry, crm_account_id FROM partners ORDER BY partner_name")
    partners = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return partners

def get_all_products() -> List[Dict[str, Any]]:
    """Retrieves all products from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, product_name, segment, family FROM products ORDER BY product_name")
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products

def get_all_deals(limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieves deals, joining with partner and user information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT
            d.deal_id,
            p.partner_name,
            pr.product_name,
            d.amount_usd,
            d.stage,
            d.close_dt,
            u.email AS owner_email,
            d.is_actionable
        FROM deals d
        JOIN partners p ON d.partner_id = p.partner_id
        JOIN products pr ON d.product_id = pr.product_id
        JOIN users u ON d.owner_user_id = u.user_id
        ORDER BY d.deal_id DESC
        LIMIT ?
    """
    cursor.execute(query, (limit,))
    deals = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return deals

def get_deal_summary_analytics() -> Dict[str, Any]:
    """Calculates summary analytics for deals."""
    conn = get_db_connection()
    cursor = conn.cursor()

    total_deals, total_amount = cursor.execute(
        "SELECT COUNT(*), COALESCE(SUM(amount_usd), 0) FROM deals"
    ).fetchone()

    stage_counts_raw = cursor.execute(
        "SELECT stage, COUNT(*) as count FROM deals GROUP BY stage"
    ).fetchall()
    stage_counts = {row['stage']: row['count'] for row in stage_counts_raw}

    conn.close()
    return {
        "total_deals": total_deals,
        "total_amount": total_amount,
        "stage_counts": stage_counts,
    }

def get_all_users() -> List[Dict[str, Any]]:
    """Retrieves all users from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, email, first_name, last_name, department FROM users ORDER BY email")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users

def get_owner_performance() -> Dict[str, List[Dict[str, Any]]]:
    """Retrieves deal performance metrics grouped by owner."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get all unique stages for initializing the stage map
    stage_counts_raw = cursor.execute("SELECT DISTINCT stage FROM deals").fetchall()
    all_stages_list = sorted([row['stage'] for row in stage_counts_raw])

    query = """
        SELECT
            u.user_id,
            u.first_name,
            u.last_name,
            u.email,
            d.stage,
            COUNT(d.deal_id) AS stage_deal_count,
            SUM(d.amount_usd) AS stage_total_amount
        FROM deals d
        JOIN users u ON d.owner_user_id = u.user_id
        GROUP BY u.user_id, u.first_name, u.last_name, u.email, d.stage
        ORDER BY u.first_name, u.last_name, d.stage
    """
    cursor.execute(query)
    
    owner_performance_map: Dict[int, Dict[str, Any]] = {}

    for row_data in cursor.fetchall():
        row = dict(row_data) # Convert sqlite3.Row to dict
        user_id = row['user_id']
        
        if user_id not in owner_performance_map:
            owner_performance_map[user_id] = {
                'owner_name': f"{row['first_name']} {row['last_name']} ({row['email']})",
                'total_amount': 0.0,
                'stages': {s_name: 0 for s_name in all_stages_list},
                'total_deals': 0
            }
        
        owner_performance_map[user_id]['stages'][row['stage']] = row['stage_deal_count']
        owner_performance_map[user_id]['total_amount'] += (row['stage_total_amount'] or 0.0)
        owner_performance_map[user_id]['total_deals'] += row['stage_deal_count']

    processed_owner_performance = sorted(list(owner_performance_map.values()), key=lambda x: x['owner_name'])
    
    conn.close()
    return {
        "owner_performance": processed_owner_performance,
        "all_stages_list": all_stages_list
    }


# --- Additional Helper/CRUD functions based on schema ---

def get_partner_by_id(partner_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a specific partner by their ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM partners WHERE partner_id = ?", (partner_id,))
    partner_row = cursor.fetchone()
    conn.close()
    return dict(partner_row) if partner_row else None

def get_deals_by_partner_id(partner_id: int) -> List[Dict[str, Any]]:
    """Retrieves all deals associated with a specific partner ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT d.*, pr.product_name, u.email as owner_email
        FROM deals d
        JOIN products pr ON d.product_id = pr.product_id
        JOIN users u ON d.owner_user_id = u.user_id
        WHERE d.partner_id = ?
        ORDER BY d.close_dt DESC
    """
    cursor.execute(query, (partner_id,))
    deals = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return deals

def get_deal_notes(deal_id: int) -> List[Dict[str, Any]]:
    """Retrieves all notes for a specific deal."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT dn.note_id, dn.note_txt, u.email as author_email, dn.created_at
        FROM deal_notes dn
        JOIN users u ON dn.user_id = u.user_id
        WHERE dn.deal_id = ?
        ORDER BY dn.created_at DESC
    """
    cursor.execute(query, (deal_id,))
    notes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return notes

def add_deal_note(deal_id: int, user_id: int, note_text: str) -> int:
    """Adds a new note to a deal and returns the new note's ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO deal_notes (deal_id, user_id, note_txt) VALUES (?, ?, ?)",
        (deal_id, user_id, note_text)
    )
    conn.commit()
    new_note_id = cursor.lastrowid
    conn.close()
    return new_note_id

def get_deal_actions(deal_id: int) -> List[Dict[str, Any]]:
    """Retrieves all actions for a specific deal."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT da.action_id, da.action_txt, u.email as owner_email, da.due_dt, da.status
        FROM deal_actions da
        LEFT JOIN users u ON da.owner_user_id = u.user_id
        WHERE da.deal_id = ?
        ORDER BY da.due_dt
    """
    cursor.execute(query, (deal_id,))
    actions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return actions

# Example usage (optional, for testing)
if __name__ == '__main__':
    print("--- All Partners ---")
    for p in get_all_partners():
        print(p)

    print("\n--- All Products ---")
    for p in get_all_products():
        print(p)

    print("\n--- All Deals (Limit 5) ---")
    for d in get_all_deals(limit=5):
        print(d)

    print("\n--- Deal Summary Analytics ---")
    print(get_deal_summary_analytics())

    print("\n--- All Users ---")
    for u in get_all_users():
        print(u)

    print("\n--- Owner Performance ---")
    owner_perf_data = get_owner_performance()
    print(f"All Stages: {owner_perf_data['all_stages_list']}")
    for op in owner_perf_data['owner_performance']:
        print(op)
    
    print("\n--- Partner by ID (1) ---")
    print(get_partner_by_id(1))

    print("\n--- Deals for Partner ID (1) ---")
    for d_p in get_deals_by_partner_id(1):
        print(d_p)

    print("\n--- Deal Notes for Deal ID (1) ---")
    # Add a sample note first if DB is fresh
    # test_user_id = get_all_users()[0]['user_id'] # Get first user's ID for testing
    # add_deal_note(1, test_user_id, "This is a test note added by cisco_data_tool.py")
    for note in get_deal_notes(1):
        print(note)

    print("\n--- Deal Actions for Deal ID (1) ---")
    # Sample data for deal_actions might be needed in init_cisco.sql for this to show results
    for action in get_deal_actions(1):
        print(action)
