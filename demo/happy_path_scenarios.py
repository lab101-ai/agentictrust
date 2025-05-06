"""Demo script that walks through all Positive (Happy-Path) scenarios defined in .plan/demo.md.

Each scenario prints the step-by-step flow and asserts that the AgenticTrust SDK
calls complete without raising.  The flows purposely mirror P-1 … P-8 from the
markdown file.

Run this file after starting the support server:

    uvicorn demo.support_server:app --reload

The script will sequentially execute each scenario, printing ✔ or ❌.
"""
from __future__ import annotations

import datetime
import os
import sys
from typing import List

# Project + demo imports --------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
DEMO_DIR = os.path.join(PROJECT_ROOT, "demo")
sys.path.append(DEMO_DIR)

from sdk.client import AgenticTrustClient  # noqa: E402  – after sys.path hacks
from sdk.security.agent_security import secure_agent, generate_code_verifier, generate_code_challenge  # noqa: E402
from sdk.security.tool_security import register_tool_with_client  # noqa: E402
from agent import Agent  # noqa: E402 – local demo agent helper
from crew import Crew  # noqa: E402

# Import demo tools so they register with the AgenticTrust backend
from support_tools import (  # noqa: E402
    actionable_deals_tool,
    lci_telemetry_tool,
)

# --------------------------------------------------------------------------------
# SETUP
# --------------------------------------------------------------------------------
SERVER_URL = os.getenv("OAUTH_SERVER_URL", "http://localhost:8000")
SUPPORT_SERVER_URL = "http://localhost:5002"  # FastAPI support_server assumed running

client = AgenticTrustClient(api_base=SERVER_URL, debug=False)

# Explicitly (re-)register tools. This is idempotent.
for _tool in (
    actionable_deals_tool,
    lci_telemetry_tool,
):
    register_tool_with_client(client, _tool)

print("\n🛠️  Tools registered with AgenticTrust service.\n")

# --------------------------------------------------------------------------------
# AGENT DEFINITIONS
# --------------------------------------------------------------------------------

@secure_agent(client=client)
class InternalAgent(Agent):
    """Represents an internal first-party agent."""

    def __init__(self, name: str = "InternalAgent", tools: List = None):
        super().__init__(
            name=name,
            role="Internal agent performing tasks",
            goal="Perform internal tasks efficiently and securely",
            tools=tools or [actionable_deals_tool, lci_telemetry_tool],
            support_server_url=SUPPORT_SERVER_URL,
        )


@secure_agent(client=client)
class ExternalAgent(Agent):
    """Represents an external SaaS / partner agent."""

    def __init__(self, name: str = "ExternalAgent", tools: List = None):
        super().__init__(
            name=name,
            role="External agent performing partner operations",
            goal="Interact with external partner systems securely",
            tools=tools or [actionable_deals_tool, lci_telemetry_tool],
            support_server_url=SUPPORT_SERVER_URL,
        )


# --------------------------------------------------------------------------------
# TOKEN HELPERS (mocked for demo)
# --------------------------------------------------------------------------------

def log(msg: str):
    print(f"[{datetime.datetime.now().isoformat()}] {msg}")


# --------------------------------------------------------------------------------
# SCENARIO IMPLEMENTATIONS
# --------------------------------------------------------------------------------

def scenario_p1_internal_user_to_internal_agent():
    """P-1 Internal User → Internal Agent (single hop)."""
    log("🚀 Scenario P-1 start")
    agent = InternalAgent(name="P1Agent")
    my_crew = Crew(agents=[agent])
    tasks = [
        {
            'description': 'P1 Internal user fetch deals',
            'agent_name': 'P1Agent',
            'tool_name': 'actionable_deals',
            'payload': {'partner': 'EPLUS'},
            'scope': ['deals.read'],
            'token_desc': 'P1 Internal user fetch deals'
        }
    ]
    
    results = my_crew.kickoff(tasks=tasks)
    log(f"✔ P-1 response: {results[0] if results else 'No result'}\n")


def scenario_p2_internal_user_to_external_agent():
    """P-2 Internal User → External Agent."""
    log("🚀 Scenario P-2 start")
    agent = ExternalAgent(name="ExtAgentP2")
    my_crew = Crew(agents=[agent])
    tasks = [
        {
            'description': 'P2 Internal user via external agent',
            'agent_name': 'ExtAgentP2',
            'tool_name': 'lci_telemetry',
            'payload': {'partner': 'EPLUS'},
            'scope': ['lci_telemetry.read'],
            'token_desc': 'P2 Internal user via external agent'
        }
    ]
    
    results = my_crew.kickoff(tasks=tasks)
    log(f"✔ P-2 response: {results[0] if results else 'No result'}\n")


def scenario_p3_external_user_to_internal_agent():
    """P-3 External User → Internal Agent."""
    log("🚀 Scenario P-3 start")
    agent = InternalAgent(name="P3IntAgent")
    my_crew = Crew(agents=[agent])
    tasks = [
        {
            'description': 'P3 External user read telemetry',
            'agent_name': 'P3IntAgent',
            'tool_name': 'lci_telemetry',
            'payload': {'partner': 'EPLUS'},
            'scope': ['lci_telemetry.read'],
            'token_desc': 'P3 External user read telemetry'
        }
    ]
    
    results = my_crew.kickoff(tasks=tasks)
    log(f"✔ P-3 response: {results[0] if results else 'No result'}\n")


def scenario_p8_external_user_to_external_agent_internal_tool():
    """P-8 External User → External Agent → Internal Tool."""
    log("🚀 Scenario P-8 start")
    ext_agent = ExternalAgent(name="ExtAgentP8")
    my_crew = Crew(agents=[ext_agent])
    tasks = [
        {
            'description': 'P8 ext user deals',
            'agent_name': 'ExtAgentP8',
            'tool_name': 'actionable_deals',
            'payload': {'partner': 'EPLUS'},
            'scope': ['deals.read'],
            'token_desc': 'P8 ext user deals'
        }
    ]
    
    results = my_crew.kickoff(tasks=tasks)
    log(f"✔ P-8 response: {results[0] if results else 'No result'}\n")


# --------------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------------

SCENARIOS = [
    scenario_p1_internal_user_to_internal_agent,
    scenario_p2_internal_user_to_external_agent,
    scenario_p3_external_user_to_internal_agent,
    scenario_p8_external_user_to_external_agent_internal_tool,
]

if __name__ == "__main__":
    for fn in SCENARIOS:
        try:
            fn()
        except Exception as e:
            log(f"❌ Scenario {fn.__name__} failed: {e}\n")
