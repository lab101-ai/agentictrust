# crew.py
import os
import sys
import requests 
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports if running script directly
# This might be needed if crew.py is executed stand-alone
if __name__ == "__main__" and '.' not in __package__:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agent import Agent
    # Import PKCE helpers relative to project root assuming sdk is sibling to demo
    try:
        from sdk.security.agent_security import generate_code_verifier, generate_code_challenge, secure_agent
        from sdk.client import AgenticTrustClient
        from support_tools import actionable_deals_tool, lci_telemetry_tool, support_tool
    except ImportError:
        print("Error: Could not import PKCE helpers from sdk.security.agent_security")
        sys.exit(1)
else:
    # Regular import if used as part of a package
    try:
        from .agent import Agent
        from ..sdk.security.agent_security import generate_code_verifier, generate_code_challenge, secure_agent
        from ..sdk.client import AgenticTrustClient
        from .support_tools import actionable_deals_tool, lci_telemetry_tool, support_tool
    except (ImportError, ValueError):
        # Fallback if run from parent directory perhaps, or different structure
        try:
            from agent import Agent
            from sdk.security.agent_security import generate_code_verifier, generate_code_challenge, secure_agent
            from sdk.client import AgenticTrustClient
            from support_tools import actionable_deals_tool, lci_telemetry_tool, support_tool
        except ImportError as e:
            print(f"Error: Could not import Agent, security components, or tools: {e}. Ensure sdk and demo are structured correctly.")
            sys.exit(1)

class Crew:
    """Orchestrates a group of agents to execute a sequence of tasks."""
    def __init__(self, agents: List[Agent]):
        """
        Initializes the Crew with a list of secured Agent instances.
        Assumes each agent has a 'client' attribute for token requests,
        typically added by the @secure_agent decorator.

        Args:
            agents: A list of secured Agent instances.
        """
        self.agents: Dict[str, Agent] = {}
        for agent in agents:
            if not hasattr(agent, 'client') or agent.client is None:
                raise ValueError(f"Agent '{agent.name}' must be secured and have a valid 'client' attribute. Apply the @secure_agent decorator.")
            if agent.name in self.agents:
                raise ValueError(f"Duplicate agent name found: '{agent.name}'. Agent names must be unique within a Crew.")
            self.agents[agent.name] = agent
        print(f"Crew initialized with {len(self.agents)} agents: {list(self.agents.keys())}")

    def _execute_tool_call(self, 
                           agent: Agent, 
                           task_info: Dict[str, Any]
                           ) -> Dict[str, Any]:
        """Handles the secure execution of a single tool call by invoking the wrapped agent.execute_task."""
        tool_name = task_info['tool_name']
        payload = task_info['payload']
        scope = task_info.get('scope', tool_name) # Default scope to tool_name
        token_desc = task_info.get('token_desc', f"Agent '{agent.name}' executing tool '{tool_name}' for task: {task_info.get('description', 'N/A')}")
        parent_token = task_info.get('parent_token')
        parent_task_id = task_info.get('parent_task_id')
        
        # Generate PKCE parameters REQUIRED by the @secure_agent wrapper's internal token fetch
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
        code_challenge_method = "S256" # Standard method
        if agent.verbose:
            print(f"  Generating PKCE for wrapped call to '{tool_name}' (method: {code_challenge_method})")

        try:
            # Directly call the agent's execute_task method.
            # The @secure_agent decorator wraps this method, handles token fetching 
            # using the provided params (scope, PKCE, etc.), calls the original 
            # execute_task with the token, and handles revocation.
            if agent.verbose:
                print(f"  Calling wrapped agent.execute_task for tool '{tool_name}'...")
            
            result = agent.execute_task(
                payload=payload,
                tool_name=tool_name,
                # --- Parameters consumed by the @secure_agent wrapper --- 
                scope=scope, 
                token_desc=token_desc,
                parent_token=parent_token,
                parent_task_id=parent_task_id,
                code_challenge=code_challenge,        
                code_challenge_method=code_challenge_method 
                # oauth_token is NOT provided here; the wrapper fetches it.
            )
            
            if agent.verbose:
                print(f"  Wrapped agent.execute_task for '{tool_name}' completed successfully.")
            return result # Return the JSON response from the underlying tool call
        
        except Exception as e:
            # Catch errors raised either by the wrapper (e.g., token fetch fail) 
            # or by the underlying agent.execute_task (e.g., HTTP request fail)
            error_msg = f"Error during wrapped execution of tool '{tool_name}' (Agent: {agent.name}): {type(e).__name__}: {e}"
            print(f"  ERROR: {error_msg}")
            # Optionally include traceback here if needed for debugging
            # import traceback
            # print(traceback.format_exc())
            return {"error": error_msg, "task_info": task_info}

    def kickoff(self, tasks: List[Dict[str, Any]]) -> List[Any]:
        """
        Executes a sequence of tasks using the assigned agents.

        Args:
            tasks: A list of dictionaries, each representing a task.
                   Required keys:
                     - 'description': str (Human-readable description)
                     - 'agent_name': str (Name of the agent to execute the task)
                     - 'tool_name': str (Name of the tool to use)
                     - 'payload': dict (Payload for the tool)
                   Optional keys:
                     - 'scope': str (OAuth scope, defaults to tool_name)
                     - 'token_desc': str (Description for token audit)
                     - 'parent_token': str
                     - 'parent_task_id': str
                     - 'expected_output': str (Description of desired outcome)

        Returns:
            A list containing the results (or errors) of each task execution.
        """
        results = []
        print(f"\n--- Starting Crew Kickoff with {len(tasks)} tasks --- ")
        for i, task in enumerate(tasks):
            print(f"\n--- Task {i+1}/{len(tasks)}: {task.get('description', 'No description')} --- ")
            agent_name = task.get('agent_name')
            tool_name = task.get('tool_name')
            payload = task.get('payload')

            # Basic validation
            if not all([agent_name, tool_name, payload is not None]):
                error_msg = f"Skipping invalid task at index {i}: Missing 'agent_name', 'tool_name', or 'payload'. Task: {task}"
                print(error_msg)
                results.append({"error": error_msg, "task_info": task})
                continue

            # Find the assigned agent
            assigned_agent = self.agents.get(agent_name)
            if not assigned_agent:
                error_msg = f"Skipping task {i+1}: Agent '{agent_name}' not found in crew."
                print(error_msg)
                results.append({"error": error_msg, "task_info": task})
                continue

            # Check if agent is allowed to use the tool
            if tool_name not in assigned_agent.allowed_tools:
                error_msg = f"Skipping task {i+1}: Agent '{assigned_agent.name}' is not authorized to use tool '{tool_name}'. Allowed tools: {assigned_agent.allowed_tools}"
                print(error_msg)
                results.append({"error": error_msg, "task_info": task})
                continue

            if assigned_agent.verbose:
                print(f"Assigning task to Agent: '{assigned_agent.name}' (Role: {assigned_agent.role}) ")
                print(f"Tool to use: '{tool_name}'")

            # Execute the tool call securely
            result = self._execute_tool_call(agent=assigned_agent, task_info=task)
            results.append(result)
            
            if assigned_agent.verbose:
                # Print a summary of the result, avoid printing huge data structures
                result_summary = result
                if isinstance(result, dict) and len(str(result)) > 200: # Simple length check
                    result_summary = {k: (type(v).__name__ if not isinstance(v, (str, int, float, bool, list, dict)) else v) for k,v in result.items()}
                    if len(str(result_summary)) > 200:
                         result_summary = f"{{...keys: {list(result.keys())}...}} (Result too large to display fully)" 
                elif len(str(result)) > 200:
                    result_summary = f"{str(result)[:197]}... (Result too large)"
                print(f"Task {i+1} Result: {result_summary}")
                
        print(f"\n--- Crew Kickoff Completed --- ")
        return results

# Example Usage (requires setting up secured agents first)
if __name__ == '__main__':
    print("--- Crew Example Script --- ")
    print("Requires:")
    print(" 1. Running AgenticTrust Server (localhost:8000)")
    print(" 2. Running Support Tool Server (localhost:5002) - only if Agent makes HTTP calls")
    
    # --- Configuration --- 
    AGENTIC_TRUST_SERVER_URL = os.getenv('AGENTIC_TRUST_SERVER_URL', 'http://localhost:8000')
    SUPPORT_SERVER_URL = os.getenv('SUPPORT_SERVER_URL', 'http://localhost:5002') # Used by Agent's default HTTP call

    # --- Instantiate Client --- 
    try:
        trust_client = AgenticTrustClient(api_base=AGENTIC_TRUST_SERVER_URL, debug=True)
        print(f"AgenticTrustClient initialized for {trust_client.api_base}")
    except Exception as e:
        print(f"Error initializing AgenticTrustClient: {e}")
        sys.exit(1)

    # --- Define Agent Subclasses (Inheriting from demo.agent.Agent) ---
    class PartnerDataAgent(Agent):
        # You can add specific methods or override __init__ if needed
        pass 

    class SupportAgent(Agent):
        # You can add specific methods or override __init__ if needed
        pass

    # --- Instantiate and Secure Agents --- 
    try:
        print("Instantiating agents...")
        # Agent 1: Accesses Partner Data
        partner_agent = PartnerDataAgent(
            name="PartnerAnalyst",
            role="Partner Data Analyst",
            goal="Retrieve and analyze partner performance data",
            tools=[actionable_deals_tool, lci_telemetry_tool], # Pass tool functions
            support_server_url=SUPPORT_SERVER_URL, # URL for HTTP calls within Agent.execute_task
            verbose=True
        )
        # Apply decorator to the INSTANCE
        secure_agent(client=trust_client)(partner_agent)
        print(f"Agent '{partner_agent.name}' instantiated and secured.")

        # Agent 2: Handles Support Tickets
        support_agent_instance = SupportAgent(
            name="SupportSpecialist",
            role="Customer Support Specialist",
            goal="Manage customer support tickets efficiently",
            tools=[support_tool], # Pass tool function
            support_server_url=SUPPORT_SERVER_URL,
            verbose=True
        )
        # Apply decorator to the INSTANCE
        secure_agent(client=trust_client)(support_agent_instance)
        print(f"Agent '{support_agent_instance.name}' instantiated and secured.")

        # --- Create Crew --- 
        print("\nCreating crew...")
        demo_crew = Crew(agents=[partner_agent, support_agent_instance])
        print("Crew created.")

        # --- Define Tasks --- 
        # Example tasks referencing tool names defined in @secure_tool
        tasks_to_run = [
            {
                'description': "Get actionable deals for EPLUS",
                'agent_name': 'PartnerAnalyst',
                'tool_name': 'actionable_deals', # Name from @secure_tool
                'payload': {'partner': 'EPLUS'},
                # 'scope': 'deals.read' # Optional: Wrapper gets scope from decorator
            },
            {
                'description': "Get LCI telemetry for EPLUS",
                'agent_name': 'PartnerAnalyst',
                'tool_name': 'lci_telemetry', # Name from @secure_tool
                'payload': {'partner': 'EPLUS'},
            },
            {
                'description': "Log a support issue for EPLUS regarding telemetry",
                'agent_name': 'SupportSpecialist',
                'tool_name': 'support_demo_v2', # Name from @secure_tool
                'payload': {'issue': 'Partner EPLUS has low telemetry adoption score', 'action': 'log_ticket'},
            },
        ]
        print(f"Defined {len(tasks_to_run)} tasks.")

        # --- Kickoff Crew --- 
        print("\nKicking off crew...")
        results = demo_crew.kickoff(tasks=tasks_to_run)

        # --- Print Results --- 
        print("\n--- Final Results --- ")
        for i, result in enumerate(results):
            print(f"Task {i+1} Output: {result}")

    except Exception as e:
        print(f"\n--- An error occurred during execution --- ")
        import traceback
        print(f"Error: {type(e).__name__}: {e}")
        print(traceback.format_exc())
        sys.exit(1)
