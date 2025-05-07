"""Minimal FastAPI UI for Cisco Operational DB"""
from pathlib import Path
import os
import sys

# Ensure project root is in sys.path for 'demo' package imports when executed directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Import functions from cisco_data_tool
from demo.tools.cisco_data_tool import (
    init_db_from_sql_file,
    get_all_partners,
    get_all_products,
    get_all_deals,
    get_deal_summary_analytics,
    get_all_users,
    get_owner_performance
)

# Directories
ROOT_DIR = Path(__file__).resolve().parent.parent  # demo/
DATA_DIR = ROOT_DIR / "data"
SQL_DIR = ROOT_DIR / "sql"
DATA_DIR.mkdir(exist_ok=True)

BASE_DIR = Path(__file__).resolve().parent  # demo/ui
DB_FILE = DATA_DIR / "cisco_ops.db"

def _ensure_db():
    print("[cisco_app] (Re)creating local SQLite DB …")
    print(f"DB_FILE path: {DB_FILE}")
    print(f"DATA_DIR path: {DATA_DIR}")
    print(f"SQL_DIR path: {SQL_DIR}")
    
    # Construct path to init_cisco.sql relative to this file (cisco_app.py)
    # cisco_app.py is in demo/ui/
    # init_cisco.sql is in demo/sql/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(current_dir, "..", "sql", "init_cisco.sql")
    print(f"SQL init file path: {sql_file}")
    
    if not os.path.exists(sql_file):
        print(f"ERROR: SQL init file not found at {sql_file}. DB will not be initialized.")
        return
    
    # Debug the database file path
    print(f"About to call init_db_from_sql_file with SQL file: {sql_file}")
    try:
        init_db_from_sql_file(sql_file) # This function is from cisco_data_tool.py
        print(f"Database initialization completed successfully")
    except Exception as e:
        print(f"ERROR during database initialization: {e}")

_ensure_db() # Ensures DB is created/recreated on startup

app = FastAPI(title="Cisco Operational DB UI")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Use functions from cisco_data_tool
    partners = get_all_partners()
    products = get_all_products()
    deals = get_all_deals(limit=100) # Default limit in tool is 100
    
    deal_analytics = get_deal_summary_analytics()
    owner_perf_data = get_owner_performance()
    users = get_all_users()

    # Prepare analytics dictionary for the template
    analytics = {
        "total_deals": deal_analytics["total_deals"],
        "total_amount": deal_analytics["total_amount"],
        "stage_counts": list(deal_analytics["stage_counts"].items()), # Convert dict to list of tuples for template
        "owner_performance": owner_perf_data["owner_performance"],
        "all_stages_list": owner_perf_data["all_stages_list"]
    }

    return templates.TemplateResponse(
        "cisco.html",
        {
            "request": request,
            "title": "Cisco Operational",
            "partners": partners,
            "products": products,
            "deals": deals,
            "analytics": analytics,
            "users": users,
        },
    )

def main():  # Entry point for poetry script
    import uvicorn
    uvicorn.run("demo.ui.cisco_app:app", host="127.0.0.1", port=8501, reload=True)

if __name__ == "__main__":
    main()
