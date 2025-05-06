import os
import sys
import uuid
import requests # Keep requests for now, might be used by helper in crew.py
import functools
from typing import Optional, List, Dict, Any, Callable, Union, TypeVar, Generic

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set server URL to use the specified server
SUPPORT_SERVER_URL = 'http://localhost:5002'

# Mimics CrewAI Agent structure more closely
class Agent:
    def __init__(self, 
                 name: str, 
                 role: str, 
                 goal: str, 
                 *,
                 tools: Optional[List[Callable]] = None,
                 backstory: Optional[str] = None,
                 support_server_url: Optional[str] = None,
                 verbose: bool = True):
        """Initialize the Agent.

        Args:
            name: Name of the agent.
            role: Role of the agent.
            goal: Objective of the agent.
            tools: List of tool functions the agent can use.
            backstory: Background context for the agent.
            support_server_url: Base URL for the support tool server.
            verbose: Enable verbose logging.
        """
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.support_server_url = support_server_url or os.getenv('SUPPORT_SERVER_URL', 'http://localhost:5002')
        self.verbose = verbose
        
        # --- Refined Tool Name Extraction & Debugging ---
        self.allowed_tools = []
        if tools:
            for i, tool in enumerate(tools):
                tool_name = None
                metadata = getattr(tool, '_tool_metadata', None)
                
                if isinstance(metadata, dict) and 'name' in metadata:
                    tool_name = metadata['name']
                elif hasattr(tool, '__name__'): # Fallback to function name
                    tool_name = tool.__name__
                else:
                    pass

                if tool_name:
                    self.allowed_tools.append(tool_name)
            
        # Original list comprehension (commented out)
        # self.allowed_tools = [getattr(tool, '_tool_metadata', {}).get('name', tool.__name__) for tool in tools] if tools else []
        
        # self.client will be set by the @secure_agent decorator if used
        self.client = None 

    def add_tool(self, tool_name: str):
        """Add a tool by name if not already present."""
        if tool_name not in self.allowed_tools:
            if self.verbose:
                print(f"Agent '{self.name}': Adding tool '{tool_name}'")
            self.allowed_tools.append(tool_name)
        
    # execute_task is REQUIRED by the @secure_agent decorator. 
    # The decorator wraps this method, handles token fetching/revocation,
    # and passes the obtained oauth_token to this original method.
    def execute_task(self, payload, tool_name, *, 
                     oauth_token: Optional[str] = None, # Provided by the wrapper
                     # Other params are consumed by the wrapper, but can be listed for clarity
                     scope: Optional[Union[List[str], str]] = None, 
                     token_desc: Optional[str] = None,
                     parent_token: Optional[str] = None,
                     parent_task_id: Optional[str] = None,
                     code_challenge: Optional[str] = None,
                     code_challenge_method: Optional[str] = None):
        """Execute a task using the specified tool and a provided OAuth token.

        NOTE: This method is intended to be wrapped by @secure_agent.
        The wrapper handles token acquisition/revocation. This method
        simply performs the HTTP request with the given token.
        
        Args:
            payload: Payload for the task/tool.
            tool_name: Name of the tool endpoint to call.
            oauth_token: The OAuth token provided by the @secure_agent wrapper.
            **kwargs: Other arguments are primarily for the wrapper's use.
            
        Returns:
            A dictionary with the result of the task execution (tool's JSON response).
            
        Raises:
            ValueError: If oauth_token is not provided (indicating wrapper failed or wasn't used).
            requests.exceptions.RequestException: If the HTTP request fails.
        """
        if not oauth_token:
            # This should ideally not happen if the agent is correctly decorated and secured.
            raise ValueError(f"Agent '{self.name}': execute_task called without an oauth_token. Ensure the agent is decorated with @secure_agent and initialized correctly.")
            
        url = f"{self.support_server_url}/{tool_name}"
        headers = {"Authorization": f"Bearer {oauth_token}"}
        
        # Adapt payload format if necessary (example: handle non-dict payloads)
        params_or_json = payload if isinstance(payload, dict) else {'issue': payload}
        
        # Determine HTTP method based on tool name convention or payload content
        # (Customize this logic if needed)
        method = 'POST' if tool_name.endswith('/admin') or 'write' in params_or_json else 'GET'
        
        try:
            if self.verbose:
                print(f"  Agent '{self.name}' executing {method} request to {url} (using wrapped token)")
            
            if method == 'GET':
                resp = requests.get(url, params=params_or_json, headers=headers)
            else:
                resp = requests.post(url, json=params_or_json, headers=headers)
                
            resp.raise_for_status() # Check for HTTP errors
            
            if self.verbose:
                print(f"  Agent '{self.name}' tool '{tool_name}' request successful (Status: {resp.status_code}).")
            return resp.json()
        
        except requests.exceptions.RequestException as e:
            print(f"  Agent '{self.name}' tool '{tool_name}' request failed: {e}")
            # Re-raise the exception to be caught by the Crew's execution logic
            raise

    def __str__(self):
        """String representation of the Agent"""
        return f"Agent(name='{self.name}', role='{self.role}', goal='{self.goal}', tools={len(self.allowed_tools)})"
