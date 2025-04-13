import os
import sys
import uuid
import base64
import hashlib
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import client from agentictrust package
from agentictrust import AgenticTrustClient

# Set server URL to use the specified server
SERVER_URL = 'http://localhost:5001'

# Simple Agent class for demonstration
class Agent:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.client_id = None
        self.client_secret = None
        self.oauth_token = None
        self.task_id = None
        self.allowed_tools = []
        self.tool_ids = []
        
    def set_credentials(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        
    def set_oauth_token(self, token, task_id):
        self.oauth_token = token
        self.task_id = task_id
        
    def add_tool(self, tool_name):
        self.allowed_tools.append(tool_name)
        
    def add_tool_id(self, tool_id):
        self.tool_ids.append(tool_id)
        
    def execute_task(self, task_description, tool_name):
        """Execute a task using the specified tool.
        
        Args:
            task_description: Description of the task
            tool_name: Name of the tool to use
            
        Returns:
            A dictionary with the result of the task execution
        """
        print(f"Agent {self.name} executing task: {task_description}")
        print(f"Tool used: {tool_name}")
        print(f"Task executed successfully: {task_description}")
        
        return {
            "status": "success",
            "agent": self.name,
            "tool_used": tool_name,
            "result": "Task completed successfully"
        }
        
    def __str__(self):
        return f"Agent(name='{self.name}', role='{self.role}')"


def simple_example():
    """Run a simple example demonstrating the basic workflow with AgenticTrust."""
    # Create client
    client = AgenticTrustClient(api_base=SERVER_URL, debug=True)
    
    print("=== SIMPLE AGENTICTRUST EXAMPLE ===")
    print(f"AgenticTrust Client using server: {SERVER_URL}")
    
    # Step 1: Register a tool
    print("\nStep 1: Registering a tool")
    tool_name = "web_search"
    
    try:
        # Check if tool already exists
        tool_list = client.tool.list()
        existing_tool = None
        
        for t in tool_list.get("tools", []):
            if t["name"] == tool_name:
                existing_tool = t
                break
        
        if existing_tool:
            # Use existing tool
            tool_id = existing_tool.get("tool_id")
            print(f"Using existing tool: {tool_name} (ID: {tool_id})")
        else:
            # Create new tool
            response = client.tool.create(
                name=tool_name,
                description="Search the web for information",
                category="research",
                permissions_required=["read:web"],
                input_schema={"type": "object", "properties": {}}
            )
            tool_id = response["tool"]["tool_id"]
            print(f"Tool registered: {tool_name} (ID: {tool_id})")
    except Exception as e:
        print(f"Error registering tool: {str(e)}")
        return
    
    # Step 2: Register an agent
    print("\nStep 2: Registering an agent")
    agent = Agent("ResearchAgent", "Researcher: Find information")
    agent.add_tool(tool_name)
    
    try:
        # Register the agent with the server
        response = client.agent.register(
            agent_name=agent.name,
            description=agent.role,
            allowed_tools=[tool_name],
            max_scope_level="restricted",
            tool_ids=[tool_id]
        )
        
        # The response structure contains nested objects
        # Extract client_id, client_secret, and registration_token from credentials
        client_id = response["credentials"]["client_id"]
        client_secret = response["credentials"]["client_secret"]
        registration_token = response["credentials"]["registration_token"]
        
        # Store credentials
        agent.set_credentials(client_id, client_secret)
        
        # Activate the agent using the registration token
        client.agent.activate(registration_token)
        
        print(f"Agent registered and activated: {agent.name}")
        print(f"Client ID: {client_id}")
        print(f"Allowed tools: {agent.allowed_tools}")
    except Exception as e:
        print(f"Error registering agent: {str(e)}")
        return
    
    # Step 3: Get authorization for agent
    print("\nStep 3: Getting authorization for agent")
    task_id = str(uuid.uuid4())
    
    # Generate PKCE code verifier and challenge
    def generate_code_verifier(length=128):
        import secrets
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(96)).decode('utf-8')
        code_verifier = code_verifier.rstrip('=')
        return code_verifier[:length]
    
    def generate_code_challenge(verifier):
        code_challenge = hashlib.sha256(verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
        code_challenge = code_challenge.rstrip('=')
        return code_challenge
    
    # Create PKCE values
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    
    print(f"Generated PKCE code_verifier: {code_verifier[:10]}... (truncated)")
    print(f"Generated PKCE code_challenge: {code_challenge[:10]}... (truncated)")
    
    try:
        # Request token for the agent with PKCE
        token_response = client.token.request(
            client_id=agent.client_id,
            client_secret=agent.client_secret,
            scope=["read:web"],
            task_id=task_id,
            task_description="Search for information",
            required_tools=[tool_name],
            code_challenge=code_challenge,
            code_challenge_method="S256"
        )
        
        # Set token for agent
        agent.set_oauth_token(token_response.get("access_token"), task_id)
        
        print(f"Token acquired for agent {agent.name}")
        print(f"Task ID: {task_id}")
    except Exception as e:
        print(f"Error getting token: {str(e)}")
        return
    
    # Step 4: Execute a tool based on agent's auth
    print("\nStep 4: Executing a tool based on agent's auth")
    
    # For demo purposes, we'll just simulate executing the tool
    # In a real scenario, you would use the token to make authorized API calls
    result = agent.execute_task("Search for product information", tool_name)
    
    print(f"\nTask result: {result}")
    
    # Cleanup - revoke token when done
    print("\nRevoking token after task completion")
    try:
        revocation = client.token.revoke(
            token=agent.oauth_token,
            reason="Tasks completed"
        )
        print(f"Token revocation: {revocation}")
    except Exception as e:
        print(f"Error revoking token: {str(e)}")
    
    print("\nWorkflow completed!")


# Example usage
if __name__ == "__main__":
    simple_example()