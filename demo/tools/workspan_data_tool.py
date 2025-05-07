import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Database file configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # demo/
DATA_DIR = PROJECT_ROOT / "data"
DB_NAME = 'workspan_core.db'
DB_PATH = DATA_DIR / DB_NAME

# --- Database Connection Utility ---
def get_db_connection() -> sqlite3.Connection:
    """Establishes a connection to the SQLite database."""
    if not os.path.exists(DB_PATH):
        print(f"Warning: Database file {DB_PATH} does not exist when trying to connect!")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

# --- Core Data Access Functions ---

def get_all_companies() -> List[Dict[str, Any]]:
    """Retrieves all companies from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT company_id, company_name, hq_country, industry FROM companies ORDER BY company_name")
    companies = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return companies

def get_all_partners() -> List[Dict[str, Any]]:
    """Retrieves all partners from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT partner_id, partner_name, ultimate_parent, hq_country FROM partners ORDER BY partner_name")
    partners = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return partners

def get_all_deals(limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieves deals with related company, partner, product, and owner information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT d.deal_id, d.amount_usd, d.stage, d.close_dt, d.is_actionable,
           c.company_name, p.partner_name, pr.product_name, u.email as owner_email
    FROM deals d
    JOIN companies c ON d.company_id = c.company_id
    JOIN partners p ON d.partner_id = p.partner_id
    JOIN products pr ON d.product_id = pr.product_id
    JOIN user_profiles u ON d.owner_profile_id = u.profile_id
    ORDER BY d.deal_id DESC
    LIMIT ?
    """
    cursor.execute(query, (limit,))
    deals = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return deals

def get_user_profiles() -> List[Dict[str, Any]]:
    """Retrieves all user profiles with company information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT u.profile_id, u.email, u.first_name, u.last_name, u.role,
           c.company_name, c.company_id
    FROM user_profiles u
    JOIN companies c ON u.company_id = c.company_id
    ORDER BY u.email
    """
    cursor.execute(query)
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users

def get_partner_insights(partner_id: int) -> List[Dict[str, Any]]:
    """Retrieves all insights for a specific partner."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT i.insight_id, i.insight_txt, i.severity, i.created_at,
           c.company_name, p.partner_name
    FROM insights i
    JOIN companies c ON i.company_id = c.company_id
    JOIN partners p ON i.partner_id = p.partner_id
    WHERE i.partner_id = ?
    ORDER BY i.created_at DESC
    """
    cursor.execute(query, (partner_id,))
    insights = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return insights

def get_partner_benchmarks(partner_id: int) -> List[Dict[str, Any]]:
    """Retrieves all benchmarks for a specific partner."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT pb.metric_name, pb.partner_metric_value, pb.cohort_avg_value, pb.variance,
           bd.dimension_name, bd.dimension_value, p.partner_name, c.company_name
    FROM partner_benchmarks pb
    JOIN benchmark_dimensions bd ON pb.dimension_id = bd.dimension_id
    JOIN partners p ON pb.partner_id = p.partner_id
    JOIN companies c ON pb.company_id = c.company_id
    WHERE pb.partner_id = ?
    """
    cursor.execute(query, (partner_id,))
    benchmarks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return benchmarks

def get_deals_by_partner_id(partner_id: int) -> List[Dict[str, Any]]:
    """Retrieves all deals for a specific partner."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT d.deal_id, d.amount_usd, d.stage, d.close_dt, d.is_actionable,
           c.company_name, p.partner_name, pr.product_name, u.email as owner_email
    FROM deals d
    JOIN companies c ON d.company_id = c.company_id
    JOIN partners p ON d.partner_id = p.partner_id
    JOIN products pr ON d.product_id = pr.product_id
    JOIN user_profiles u ON d.owner_profile_id = u.profile_id
    WHERE d.partner_id = ?
    ORDER BY d.close_dt DESC
    """
    cursor.execute(query, (partner_id,))
    deals = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return deals

def get_partner_scores(partner_id: int) -> List[Dict[str, Any]]:
    """Retrieves all scores for a specific partner."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT ps.score_dt, ps.score_type, ps.score_value,
           c.company_name, p.partner_name
    FROM partner_scores ps
    JOIN companies c ON ps.company_id = c.company_id
    JOIN partners p ON ps.partner_id = p.partner_id
    WHERE ps.partner_id = ?
    ORDER BY ps.score_dt DESC
    """
    cursor.execute(query, (partner_id,))
    scores = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return scores

def get_partner_by_id(partner_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves details of a specific partner by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM partners WHERE partner_id = ?", (partner_id,))
    partner_row = cursor.fetchone()
    conn.close()
    return dict(partner_row) if partner_row else None

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

    # Get average deal size by company
    company_deals_raw = cursor.execute("""
        SELECT c.company_name, COUNT(d.deal_id) as deal_count, 
               COALESCE(AVG(d.amount_usd), 0) as avg_deal_size
        FROM deals d
        JOIN companies c ON d.company_id = c.company_id
        GROUP BY c.company_id
        ORDER BY avg_deal_size DESC
    """).fetchall()
    company_metrics = [dict(row) for row in company_deals_raw]

    conn.close()
    return {
        "total_deals": total_deals,
        "total_amount": total_amount,
        "stage_counts": stage_counts,
        "company_metrics": company_metrics
    }

def get_insight_actions(insight_id: int) -> List[Dict[str, Any]]:
    """Retrieves all actions for a specific insight."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT action_id, action_txt, priority, status
    FROM insight_actions
    WHERE insight_id = ?
    ORDER BY priority
    """
    cursor.execute(query, (insight_id,))
    actions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return actions

def get_telemetry_metrics(partner_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves telemetry metrics for a specific partner."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT tm.metric_id, tm.metric_name, tm.metric_value, tm.captured_at,
           c.company_name, p.partner_name
    FROM telemetry_metrics tm
    JOIN companies c ON tm.company_id = c.company_id
    JOIN partners p ON tm.partner_id = p.partner_id
    WHERE tm.partner_id = ?
    ORDER BY tm.captured_at DESC
    LIMIT ?
    """
    cursor.execute(query, (partner_id, limit))
    metrics = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return metrics

# Example usage (for testing)
if __name__ == '__main__':
    print("--- All Companies ---")
    for company in get_all_companies():
        print(company)

    print("\n--- All Partners ---")
    for partner in get_all_partners():
        print(partner)

    print("\n--- All Deals (Limit 5) ---")
    for deal in get_all_deals(limit=5):
        print(deal)
    
    print("\n--- User Profiles ---")
    for user in get_user_profiles():
        print(user)
    
    # Test with a partner_id if available
    test_partner_id = 1
    
    print(f"\n--- Partner Insights (Partner ID: {test_partner_id}) ---")
    for insight in get_partner_insights(test_partner_id):
        print(insight)
    
    print(f"\n--- Deal Summary Analytics ---")
    print(get_deal_summary_analytics()) 