import os
import sys
import uuid
import time
import datetime

# Ensure project root in path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Add demo directory for local module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sdk.tokens
from sdk.client import AgenticTrustClient
from sdk.security.agent_security import secure_agent, generate_code_verifier, generate_code_challenge
from sdk.security.tool_security import register_tool_with_client
from agent import Agent
from crew import Crew
# Import tools
from support_tools import (
    actionable_deals_tool,
    lci_telemetry_tool,
)

# Service URLs
SERVER_URL = 'http://localhost:8000' # Changed port from 5001 to 8000
SUPPORT_SERVER_URL = 'http://localhost:5002'

# Initialize client
client = AgenticTrustClient(api_base=SERVER_URL, debug=False)

# --- Explicitly register tools BEFORE defining agents that use them ---
print(f"[{datetime.datetime.now().isoformat()}] 🛠️ Registering tools...")
for _tool in (actionable_deals_tool, lci_telemetry_tool):
    register_tool_with_client(client, _tool)
    print(
        f"[{datetime.datetime.now().isoformat()}] ✅ Tool '{getattr(_tool, '_tool_metadata', {}).get('name')}' registered."
    )

# Method 1: Using @secure_agent decorator on a class
@secure_agent(client=client)
class PartnerDataAgent(Agent):
    """Secure agent for partner data queries"""
    def __init__(self):
        super().__init__(
            name='PartnerDataAgent',
            role='Retrieve partner actionable insights',
            goal='Provide timely and relevant data points about partners to drive sales actions.',
            tools=[actionable_deals_tool, lci_telemetry_tool],
            support_server_url=SUPPORT_SERVER_URL,
        )

# Method 2: Using @secure_agent decorator on a function that returns an Agent
@secure_agent(client=client)
def create_research_agent():
    """Create and return a research agent"""
    return Agent(
        name='ResearchAgent',
        role='Research and analyze information',
        goal='Gather and synthesize information from various sources for comprehensive reports.',
        tools=[actionable_deals_tool, lci_telemetry_tool],
        support_server_url=SUPPORT_SERVER_URL
    )

def demo():
    """Run demo: register tool, create agent, execute task using Crew"""
    print(f"[{datetime.datetime.now().isoformat()}] 🚀 DEMO START")

    # Step 1: Tool is now registered explicitly above

    # Step 2a: Instantiate secure agent using decorated class
    support_agent = PartnerDataAgent()
    print(f"[{datetime.datetime.now().isoformat()}] ✅ Agent '{support_agent.name}' ready (Method 1: Decorated class)")
    
    # Step 2b: Create agent using decorated factory function
    research_agent = create_research_agent()
    print(f"[{datetime.datetime.now().isoformat()}] ✅ Agent '{research_agent.name}' ready (Method 2: Decorated factory)")
    
    # --- Crew Setup and Execution ---
    print(f"\n[{datetime.datetime.now().isoformat()}] 🏃 Setting up Crew...")
    # Instantiate Crew with a list of agents
    my_crew = Crew(agents=[support_agent, research_agent])

    # Define a sequence of tasks for the crew
    # Tasks now need 'agent_name' to assign them
    tasks = [
        {
            'description': 'Fetch high-value EPlus deals',
            'agent_name': 'PartnerDataAgent', # Assign task to this agent
            'tool_name': 'actionable_deals',
            'payload': {'partner': 'EPlus'},
            'scope': 'deals.read', # Example scope
            'token_desc': 'Fetch high-value deals for partner EPlus'
        },
        {
            'description': 'Get EPlus LCI telemetry',
            'agent_name': 'PartnerDataAgent', # Assign task to this agent
            'tool_name': 'lci_telemetry',
            'payload': {'partner': 'EPlus'},
            # Uses default scope (tool_name) and description
        },
        # Example task for the other agent (if desired)
        # {
        #     'description': 'Research alternative partners',
        #     'agent_name': 'ResearchAgent',
        #     'tool_name': 'some_research_tool', # Assuming a tool exists
        #     'payload': {'topic': 'alternative data partners'}
        # },
    ]

    print(f"[{datetime.datetime.now().isoformat()}] ▶️ Kicking off tasks...")
    # Use kickoff method with the list of tasks
    results = my_crew.kickoff(tasks=tasks)

    print(f"\n[{datetime.datetime.now().isoformat()}] 📊 Crew Results:")
    import json
    print(json.dumps(results, indent=2))

    print(f"\n[{datetime.datetime.now().isoformat()}] 🎉 DEMO COMPLETE")

if __name__ == '__main__':
    try:
        demo()
    except KeyboardInterrupt:
        print(f"[{datetime.datetime.now().isoformat()}] ❌ DEMO INTERRUPTED by user")