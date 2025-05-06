"""Interactive demo for 1.2 Multi-Hop / Delegated scenarios (P-6…P-8).

Run after support server is up:

    uvicorn demo.support_server:app --reload
    python  demo/multi_hop_scenarios.py
"""
from __future__ import annotations

import datetime
import os
import sys
from typing import List, Dict

# Ensure project root + demo directory on path -----------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
DEMO_DIR = os.path.join(PROJECT_ROOT, "demo")
if DEMO_DIR not in sys.path:
    sys.path.append(DEMO_DIR)

from sdk.client import AgenticTrustClient  # noqa: E402
from sdk.security.agent_security import secure_agent  # noqa: E402
from sdk.security.tool_security import register_tool_with_client  # noqa: E402
from agent import Agent  # noqa: E402 – local demo Agent helper
from crew import Crew  # noqa: E402

# Import tools that will be used -------------------------------------------------
from support_tools import (  # noqa: E402
    actionable_deals_tool,
    lci_telemetry_tool,
)

SERVER_URL = os.getenv("OAUTH_SERVER_URL", "http://localhost:8000")
SUPPORT_SERVER_URL = "http://localhost:5002"

client = AgenticTrustClient(api_base=SERVER_URL, debug=False)

for _tool in (
    actionable_deals_tool,
    lci_telemetry_tool,
):
    register_tool_with_client(client, _tool)

# Agent definitions -------------------------------------------------------------

@secure_agent(client=client)
class InternalAgent(Agent):
    def __init__(self, name: str, tools: List = None):
        super().__init__(
            name=name,
            role="Internal agent",
            goal="Execute internal tasks and potentially delegate.",
            tools=tools or [actionable_deals_tool, lci_telemetry_tool],
            support_server_url=SUPPORT_SERVER_URL,
        )


@secure_agent(client=client)
class ExternalAgent(Agent):
    def __init__(self, name: str, tools: List = None):
        super().__init__(
            name=name,
            role="External SaaS agent",
            goal="Perform partner-facing operations securely.",
            tools=tools or [actionable_deals_tool, lci_telemetry_tool],
            support_server_url=SUPPORT_SERVER_URL,
        )


# Utility -----------------------------------------------------------------------

def log(msg: str):
    print(f"[{datetime.datetime.now().isoformat()}] {msg}")


def pretty(obj: Dict):
    import json as _json
    print(_json.dumps(obj, indent=2))


def wait():
    """Pause for user, but auto-continue if stdin not interactive."""
    try:
        input("\nPress <Enter> to continue…")
    except EOFError:
        # CI / piped execution: just continue
        print("(auto-continue)\n")


# Scenario helpers --------------------------------------------------------------

def scenario_p6():
    """P-6: Internal User → Internal Agent (nested calls share context)."""
    log("🚀 Scenario P-6 start – nested internal chain")
    agent = InternalAgent(name="NestedAgentP6")
    my_crew = Crew(agents=[agent])
    
    tasks = [
        {
            'description': 'Fetch deals',
            'agent_name': 'NestedAgentP6',
            'tool_name': 'actionable_deals',
            'payload': {'partner': 'EPLUS'},
            'scope': ['deals.read'],
            'token_desc': 'Fetch deals'
        },
        {
            'description': 'Fetch telemetry',
            'agent_name': 'NestedAgentP6',
            'tool_name': 'lci_telemetry',
            'payload': {'partner': 'EPLUS'},
            'scope': ['lci_telemetry.read'],
            'token_desc': 'Fetch telemetry'
        }
    ]
    
    results = my_crew.kickoff(tasks=tasks)
    
    log("Crew results:")
    for result in results:
        pretty(result)
        
    log("✔ Scenario P-6 completed\n")


def scenario_p7():
    """P-7: Internal Agent → External Agent → External Tool (chained via secure_agent)."""
    log("🚀 Scenario P-7 start – internal → external chain")
    agent_a = InternalAgent(name="AgentA_P7")
    agent_b = ExternalAgent(name="ExternalAgentB_P7")
    my_crew = Crew(agents=[agent_a, agent_b])
    
    tasks = [
        {
            'description': 'Initial fetch deals by A',
            'agent_name': 'AgentA_P7',
            'tool_name': 'actionable_deals',
            'payload': {'partner': 'EPLUS'},
            'scope': ['deals.read'],
            'token_desc': 'Initial fetch deals by A'
        },
        {
            'description': 'Delegated fetch telemetry by B',
            'agent_name': 'ExternalAgentB_P7',
            'tool_name': 'lci_telemetry',
            'payload': {'partner': 'EPLUS'},
            'scope': ['lci_telemetry.read'],
            'token_desc': 'Delegated fetch telemetry by B'
        }
    ]
    
    results = my_crew.kickoff(tasks=tasks)
    
    log("Crew results:")
    for result in results:
        pretty(result)
        
    log("✔ Scenario P-7 completed\n")


def scenario_p8():
    """P-8: External User → External Agent → Internal Tool.
    
    Note: Refactored to use Crew. The original direct execute_task allowed passing
    an external partner_token. The Crew/secure_agent model assumes the agent itself
    authenticates via the wrapper to get its token, so the partner_token concept
    is simulated here by the external agent running the tasks under its own identity.
    """
    log("🚀 Scenario P-8 – External user via external agent (Crew refactor)")
    # partner_token = "partner_user_token" # Mocked token from original, not used by Crew
    # log(f"Simulating Partner access token: {partner_token}\nScopes = ['deals.read', 'lci_telemetry.read']")
    # wait()

    ext_agent = ExternalAgent(name="ExtAgentP8")
    my_crew = Crew(agents=[ext_agent])

    tasks = [
        {
            'description': 'Partner user deals (via ExtAgentP8)',
            'agent_name': 'ExtAgentP8',
            'tool_name': 'actionable_deals',
            'payload': {'partner': 'EPLUS'},
            'scope': ['deals.read'],
            'token_desc': 'Partner user deals (via ExtAgentP8)'
        },
        {
            'description': 'Partner user telemetry (via ExtAgentP8)',
            'agent_name': 'ExtAgentP8',
            'tool_name': 'lci_telemetry',
            'payload': {'partner': 'EPLUS'},
            'scope': ['lci_telemetry.read'],
            'token_desc': 'Partner user telemetry (via ExtAgentP8)'
        }
    ]

    results = my_crew.kickoff(tasks=tasks)
    
    log("Crew results:")
    for result in results:
        pretty(result)

    log("✔ Scenario P-8 completed\n")


SCENARIOS = {
    "6": ("P-6 Internal → Internal chain", scenario_p6),
    "7": ("P-7 Internal → External chain", scenario_p7),
    "8": ("P-8 External user chain", scenario_p8),
    "all": ("Run all P-6 … P-8", None),
}


def main():
    print("\n1.2 Multi-Hop / Delegated Scenarios – Interactive Demo\n")
    for key, (title, _) in SCENARIOS.items():
        print(f"  {key:>3}  {title}")
    choice = input("\nSelect scenario (6/7/8/all): ").strip().lower() or "all"

    if choice == "all":
        for key in ("6", "7", "8"):
            _, fn = SCENARIOS[key]
            fn()
    elif choice in SCENARIOS:
        _, fn = SCENARIOS[choice]
        fn()
    else:
        print("Invalid choice – exiting.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted – exiting.")
