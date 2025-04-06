import uuid
import requests
from typing import Dict, List, Optional, Union, Any

class AgenticTrustClient:
    """
    Main client for interacting with the AgenticTrust OAuth server.
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """Initialize the client with the base URL of the AgenticTrust server."""
        self.base_url = base_url.rstrip('/')
        self.agent = AgentClient(self)
        self.token = TokenClient(self)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the AgenticTrust server."""
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, **kwargs)
        
        # Raise exception for HTTP errors
        response.raise_for_status()
        
        # Return JSON response
        return response.json()

class AgentClient:
    """
    Client for agent registration and management.
    """
    
    def __init__(self, parent: AgenticTrustClient):
        """Initialize with parent client."""
        self.parent = parent
    
    def register(self, agent_name: str, description: Optional[str] = None,
                allowed_tools: Optional[List[str]] = None,
                allowed_resources: Optional[List[str]] = None,
                max_scope_level: str = "restricted") -> Dict[str, Any]:
        """
        Register a new agent with the AgenticTrust server.
        
        Args:
            agent_name: Name of the agent
            description: Optional description of the agent
            allowed_tools: List of allowed tools for this agent
            allowed_resources: List of allowed resources for this agent
            max_scope_level: Maximum scope level (default: "restricted")
            
        Returns:
            Dict containing agent details and credentials
        """
        data = {
            "agent_name": agent_name,
            "description": description,
            "allowed_tools": allowed_tools or [],
            "allowed_resources": allowed_resources or [],
            "max_scope_level": max_scope_level
        }
        
        return self.parent._make_request("POST", "/api/agents/register", json=data)
    
    def activate(self, registration_token: str) -> Dict[str, Any]:
        """
        Activate a registered agent using the registration token.
        
        Args:
            registration_token: The registration token received during registration
            
        Returns:
            Dict containing activation status and agent details
        """
        data = {
            "registration_token": registration_token
        }
        
        return self.parent._make_request("POST", "/api/agents/activate", json=data)
    
    def list(self) -> Dict[str, Any]:
        """
        List all registered agents.
        
        Returns:
            Dict containing list of agents
        """
        return self.parent._make_request("GET", "/api/agents/list")
    
    def get(self, client_id: str) -> Dict[str, Any]:
        """
        Get agent details by client ID.
        
        Args:
            client_id: The client ID of the agent
            
        Returns:
            Dict containing agent details
        """
        return self.parent._make_request("GET", f"/api/agents/{client_id}")
    
    def delete(self, client_id: str) -> Dict[str, Any]:
        """
        Delete an agent by client ID.
        
        Args:
            client_id: The client ID of the agent
            
        Returns:
            Dict containing deletion status
        """
        return self.parent._make_request("DELETE", f"/api/agents/{client_id}")

class TokenClient:
    """
    Client for token management.
    """
    
    def __init__(self, parent: AgenticTrustClient):
        """Initialize with parent client."""
        self.parent = parent
        self._current_token = None
        self._current_task_id = None
        self._parent_token = None
        self._parent_task_id = None
    
    def request(self, client_id: str, client_secret: str, 
               scope: Union[List[str], str] = [],
               task_id: Optional[str] = None,
               task_description: Optional[str] = None,
               required_tools: Optional[List[str]] = None,
               required_resources: Optional[List[str]] = None,
               parent_task_id: Optional[str] = None,
               parent_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Request a new token from the AgenticTrust server.
        
        Args:
            client_id: The client ID of the agent
            client_secret: The client secret of the agent
            scope: List of requested scopes or space-separated string
            task_id: Optional task ID (generated if not provided)
            task_description: Optional description of the task
            required_tools: List of required tools for this task
            required_resources: List of required resources for this task
            parent_task_id: Optional parent task ID (for child agents)
            parent_token: Optional parent token (for child agents)
            
        Returns:
            Dict containing token details
        """
        if isinstance(scope, list):
            scope = " ".join(scope)
            
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope,
            "task_id": task_id or str(uuid.uuid4()),
            "task_description": task_description,
            "required_tools": required_tools or [],
            "required_resources": required_resources or [],
            "parent_task_id": parent_task_id,
            "parent_token": parent_token
        }
        
        response = self.parent._make_request("POST", "/api/oauth/token", json=data)
        
        # Store current token and task context
        self._current_token = response.get("access_token")
        self._current_task_id = response.get("task_id")
        self._parent_token = parent_token
        self._parent_task_id = response.get("parent_task_id")
        
        return response
    
    def verify(self, token: Optional[str] = None, 
              task_id: Optional[str] = None,
              parent_task_id: Optional[str] = None,
              parent_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify a token and its task context.
        
        Args:
            token: The token to verify (uses current token if not provided)
            task_id: The task ID to verify (uses current task ID if not provided)
            parent_task_id: The parent task ID to verify (uses current parent task ID if not provided)
            parent_token: The parent token to verify (uses current parent token if not provided)
            
        Returns:
            Dict containing verification results
        """
        data = {
            "token": token or self._current_token,
            "task_id": task_id or self._current_task_id,
            "parent_task_id": parent_task_id or self._parent_task_id,
            "parent_token": parent_token or self._parent_token
        }
        
        return self.parent._make_request("POST", "/api/oauth/verify", json=data)
    
    def introspect(self, token: Optional[str] = None,
                  include_task_history: bool = False,
                  include_children: bool = False) -> Dict[str, Any]:
        """
        Introspect a token to get detailed information about it.
        
        Args:
            token: The token to introspect (uses current token if not provided)
            include_task_history: Whether to include task history
            include_children: Whether to include child tokens
            
        Returns:
            Dict containing token details
        """
        data = {
            "token": token or self._current_token,
            "include_task_history": include_task_history,
            "include_children": include_children
        }
        
        return self.parent._make_request("POST", "/api/oauth/introspect", json=data)
    
    def revoke(self, token: Optional[str] = None,
              reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Revoke a token.
        
        Args:
            token: The token to revoke (uses current token if not provided)
            reason: Optional reason for revocation
            
        Returns:
            Dict containing revocation status
        """
        data = {
            "token": token or self._current_token,
            "reason": reason
        }
        
        response = self.parent._make_request("POST", "/api/oauth/revoke", json=data)
        
        # Clear current token if it's the one being revoked
        if token is None or token == self._current_token:
            self._current_token = None
            self._current_task_id = None
            
        return response
    
    def call_protected_endpoint(self, token: Optional[str] = None,
                               task_id: Optional[str] = None,
                               parent_task_id: Optional[str] = None,
                               parent_token_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Call a protected endpoint using token authentication.
        
        Args:
            token: The token to use (uses current token if not provided)
            task_id: The task ID to include in headers (uses current task ID if not provided)
            parent_task_id: The parent task ID to include in headers
            parent_token_id: The parent token ID to include in headers
            
        Returns:
            Dict containing response from the protected endpoint
        """
        token = token or self._current_token
        if not token:
            raise ValueError("No token available. Request a token first.")
            
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Task-ID": task_id or self._current_task_id
        }
        
        if parent_task_id or self._parent_task_id:
            headers["X-Parent-Task-ID"] = parent_task_id or self._parent_task_id
            
        if parent_token_id:
            headers["X-Parent-Token-ID"] = parent_token_id
            
        return self.parent._make_request("GET", "/api/oauth/protected", headers=headers) 