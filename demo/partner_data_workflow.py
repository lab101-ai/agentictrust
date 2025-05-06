"""
Interactive partner-data workflow demo.

This script mirrors the high-level OAuth exchange flow described in the
product requirements document (PRD) and the user-provided workflow
specification.  A human user (selected from ``data/users.yml``) asks our
PXP AI Agent to fetch actionable partner data (deals and LCI telemetry).

The script then performs the following steps:

1.  Loads available users from ``data/users.yml`` and lets the operator
    pick one (defaults to *amit_cisco*).
2.  Registers demo tools (``actionable_deals`` and ``lci_telemetry``)
    with the local AgenticTrust server.
3.  Instantiates a *secure* PXPAgent using ``@secure_agent`` so that each
    tool invocation obtains a short-lived scoped token, executes the
    remote API call via the support server, and immediately revokes the
    token afterwards.
4.  Executes two tasks on behalf of the chosen user/partner:
      • Fetch actionable deals
      • Fetch LCI telemetry (adoption score etc.)
   The underlying SDK automatically conveys task-level context (task ID,
   parent token, scopes) in every call, satisfying the PRD lineage
   requirements.
5.  Prints the aggregated results to the console.

Prerequisites
-------------
• AgenticTrust API server running locally on http://localhost:8000
• Demo support server running on           http://localhost:5002
• The *demo/support_tools.py* module already loaded by the support
  server (see README).

Run the demo with:

    poetry run python demo/partner_data_workflow.py

Optionally pass a username as the first CLI argument:

    poetry run python demo/partner_data_workflow.py alice_google
"""

import os
import sys
import argparse
import datetime
import yaml
import json as _json

# ────────────────────────────────────────────────────────────────────────────
# Ensure project root in path for imports
# ────────────────────────────────────────────────────────────────────────────
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# Import SDK and demo helpers
from sdk.client import AgenticTrustClient
from sdk.security.agent_security import (
    secure_agent,
    start_task,
)
from sdk.security.tool_security import register_tool_with_client
from demo.support_tools import actionable_deals_tool, lci_telemetry_tool
from demo.agent import Agent  # core agent implementation

# Service URLs (adjust if your local dev setup differs)
SERVER_URL = "http://localhost:8000"  # AgenticTrust API

USERS_YAML_PATH = os.path.join(ROOT_DIR, "data", "users.yml")

# Shared API client used for tool registration and secure_agent decorator
client = AgenticTrustClient(api_base=SERVER_URL, debug=False)


# ────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ────────────────────────────────────────────────────────────────────────────

def load_users(path: str):
    """Load users YAML and return list of user dicts."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("users", [])


def choose_user(users, username_arg: str | None = None):
    """Return user dict matching *username_arg* or prompt interactively."""
    if username_arg:
        user = next((u for u in users if u["username"] == username_arg), None)
        if not user:
            raise ValueError(f"Unknown username '{username_arg}'. Available: {[u['username'] for u in users]}")
        return user

    # Interactive prompt
    print("Available users:")
    for idx, u in enumerate(users, 1):
        print(f"  {idx}. {u['username']} ({u['full_name']}, partner={u['partner']})")
    while True:
        choice = input("Select user by number [1]: ").strip() or "1"
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(users):
                return users[idx]
        except ValueError:
            pass
        print("Invalid selection – try again.")


# ────────────────────────────────────────────────────────────────────────────
# Secure PXP Agent definition
# ────────────────────────────────────────────────────────────────────────────

@secure_agent(client=client)
class PXPAgent(Agent):
    """Partner-eXperience Proxy agent performing data retrieval."""

    def __init__(self):
        super().__init__(
            name="PXPAgent",
            role="Retrieve partner adoption score, actionable deals, and telemetry on behalf of end-users.",
            goal="Securely fetch and report partner data based on user requests.",
            tools=[actionable_deals_tool, lci_telemetry_tool],
        )


# ────────────────────────────────────────────────────────────────────────────
# Main demo routine
# ────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Interactive partner-data workflow demo")
    parser.add_argument("username", nargs="?", help="Username from data/users.yml (interactive if omitted)")
    args = parser.parse_args()

    # Load and choose user ---------------------------------------------------
    users = load_users(USERS_YAML_PATH)
    user = choose_user(users, args.username)
    partner = user["partner"]

    print(f"[{datetime.datetime.now().isoformat()}] 👤 Acting on behalf of {user['full_name']} (username={user['username']}, partner={partner})")

    # -------------------------------------------------------------------
    # Ensure tools are registered with the AgenticTrust server
    # -------------------------------------------------------------------
    print(f"[{datetime.datetime.now().isoformat()}] 🛠️  Registering tools …")
    for _tool in (actionable_deals_tool, lci_telemetry_tool):
        register_tool_with_client(client, _tool)

    # Instantiate secure agent ----------------------------------------------
    print(f"[{datetime.datetime.now().isoformat()}] 🤖 Spinning up PXPAgent …")
    pxp_agent = PXPAgent()
    print(f"[{datetime.datetime.now().isoformat()}] ✅ PXPAgent ready – allowed tools: {pxp_agent.allowed_tools}\n")

    # -----------------------------------------------------------------------
    # Execute workflow using direct tool calls within start_task context
    # -----------------------------------------------------------------------
    print("\n==== Executing Partner Data Workflow (Direct In-Process Tool Calls) ====")

    # Define the parent task description
    parent_task_description = f"User {user['username']} wants deals and LCI telemetry data for partner {partner}"
    print(f"[{datetime.datetime.now().isoformat()}] 🚀 Entering parent task context (start_task) with description: '{parent_task_description}' ...")
    
    # Start the parent task context
    with start_task(
        pxp_agent,
        scope=['deals.read', 'lci_telemetry.read'],
        description=parent_task_description,
        agent_type=pxp_agent.name,
        agent_model=pxp_agent.__class__.__name__,
        agent_provider=pxp_agent.__class__.__module__,
        agent_instance_id=pxp_agent.name,
        delegator_sub=user['username']
    ):
        # Execute the tools directly in-process
        print(f"[{datetime.datetime.now().isoformat()}] 🔍 Fetching actionable deals for {partner}...")
        deals_result = actionable_deals_tool(partner=partner)
        
        print(f"[{datetime.datetime.now().isoformat()}] 📊 Fetching LCI telemetry for {partner}...")
        telemetry_result = lci_telemetry_tool(partner=partner)
        
        # Store results for display after context exit
        results = {
            'deals': deals_result,
            'telemetry': telemetry_result
        }
        
        print(f"[{datetime.datetime.now().isoformat()}] ✅ All tools executed successfully")

    # Display results after context has exited and parent token is revoked
    print("\n==== Final Workflow Results ====")
    
    # Display deals
    print(f"\n  💼 Actionable Deals for {partner}:")
    deals = results['deals'].get('deals', [])
    if deals:
        for deal in deals:
            print(f"    • {deal['name']} (ID: {deal['id']})")
            print(f"      Next step: {deal['next_step']}")
    else:
        print(f"    No actionable deals found for {partner}")
    
    # Display telemetry
    print(f"\n  📊 LCI Telemetry for {partner}:")
    telemetry = results['telemetry'].get('telemetry')
    if telemetry:
        print(f"    • Adoption Score: {telemetry['adoption_score']}")
        print(f"    • Weekly Active Users: {telemetry['weekly_active_users']}")
        print(f"    • Feature Usage:")
        print(f"      - Reports: {telemetry['feature_usage']['reports']}")
        print(f"      - Integrations: {telemetry['feature_usage']['integrations']}")
    else:
        print(f"    No telemetry data found for {partner}")

    print(f"\n[{datetime.datetime.now().isoformat()}] 🛑 Exited parent task context (start_task). Parent token has been revoked.")


# Pretty-print helper using json but imported lazily to avoid overhead if not needed
def json_dump(obj):
    import json
    return json.dumps(obj, indent=2, sort_keys=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user – exiting.")