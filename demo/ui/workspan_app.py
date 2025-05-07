"""Minimal FastAPI UI for Workspan Analytics DB"""
from pathlib import Path
import sqlite3
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
SQL_DIR = ROOT_DIR / "sql"
DATA_DIR.mkdir(exist_ok=True)

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = DATA_DIR / "workspan_core.db"
INIT_SQL = SQL_DIR / "init_workspan.sql"

def _ensure_db() -> None:
    if DB_FILE.exists():
        DB_FILE.unlink()
    print("[workspan_app] (Re)creating local SQLite DB …")
    conn = sqlite3.connect(DB_FILE)
    conn.executescript(INIT_SQL.read_text())
    conn.close()

_ensure_db()

def get_conn():
    return sqlite3.connect(DB_FILE)

app = FastAPI(title="Workspan Analytics DB UI")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    conn = get_conn()
    cur = conn.cursor()
    companies = cur.execute("SELECT company_id, company_name, hq_country, industry FROM companies ORDER BY company_id").fetchall()
    partners = cur.execute("SELECT partner_id, partner_name, hq_country FROM partners ORDER BY partner_id").fetchall()
    products = cur.execute("SELECT product_id, product_name, category FROM products ORDER BY product_id").fetchall()
    deals = cur.execute(
        """
        SELECT d.deal_id, c.company_name, p.partner_name, d.amount_usd, d.stage, u.email
        FROM deals d
        JOIN companies c USING(company_id)
        JOIN partners p USING(partner_id)
        JOIN user_profiles u ON u.profile_id = d.owner_profile_id
        ORDER BY d.deal_id
        LIMIT 100
        """
    ).fetchall()
    total_deals, total_amount = cur.execute("SELECT COUNT(*), COALESCE(SUM(amount_usd),0) FROM deals").fetchone()
    stage_counts_raw = cur.execute("SELECT stage, COUNT(*) FROM deals GROUP BY stage").fetchall()
    analytics = {"total_deals": total_deals, "total_amount": total_amount, "stage_counts": stage_counts_raw}
    users = cur.execute("SELECT profile_id, email, first_name, last_name, role FROM user_profiles ORDER BY profile_id").fetchall()

    owner_stage_details_cur = conn.cursor()
    owner_stage_details_cur.execute("""
        SELECT
            up.profile_id,
            up.first_name,
            up.last_name,
            up.email,
            d.stage,
            COUNT(d.deal_id) AS stage_deal_count,
            SUM(d.amount_usd) AS stage_total_amount
        FROM deals d
        JOIN user_profiles up ON d.owner_profile_id = up.profile_id
        GROUP BY up.profile_id, up.first_name, up.last_name, up.email, d.stage
        ORDER BY up.first_name, up.last_name, d.stage
    """)
    
    owner_performance_map = {} 
    all_stages_list = sorted(list(set(s[0] for s in stage_counts_raw))) # Unique stages, sorted

    for row in owner_stage_details_cur.fetchall():
        profile_id, first_name, last_name, email, stage, stage_deal_count, stage_total_amount = row
        
        if profile_id not in owner_performance_map:
            owner_performance_map[profile_id] = {
                'owner_name': f"{first_name} {last_name} ({email})",
                'total_amount': 0,
                'stages': {s_name: 0 for s_name in all_stages_list},
                'total_deals': 0
            }
        
        owner_performance_map[profile_id]['stages'][stage] = stage_deal_count
        # Ensure stage_total_amount is not None before adding
        owner_performance_map[profile_id]['total_amount'] += (stage_total_amount or 0)
        owner_performance_map[profile_id]['total_deals'] += stage_deal_count

    processed_owner_performance = sorted(list(owner_performance_map.values()), key=lambda x: x['owner_name'])

    analytics["owner_performance"] = processed_owner_performance
    analytics["all_stages_list"] = all_stages_list

    conn.close()
    return templates.TemplateResponse(
        "workspan.html",
        {
            "request": request,
            "title": "Workspan Analytics",
            "companies": companies,
            "partners": partners,
            "products": products,
            "deals": deals,
            "analytics": analytics,
            "users": users,
        },
    )

def main():
    import uvicorn
    uvicorn.run("demo.ui.workspan_app:app", host="127.0.0.1", port=8502, reload=True)

if __name__ == "__main__":
    main()
