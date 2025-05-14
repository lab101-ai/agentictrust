"""
AgenticTrust Python SDK Client
"""
import requests
from typing import Dict, Any, List, Optional

class AgenticTrustClient:
    """Client for interacting with the AgenticTrust API."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """Initialize the client with base URL and optional API key."""
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({"X-API-Key": api_key})
    
    def set_token(self, token: str):
        """Set the authorization token for subsequent requests."""
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def create_user(self, username: str, email: str, full_name: Optional[str] = None, 
                   password: Optional[str] = None, is_external: bool = False,
                   department: Optional[str] = None, job_title: Optional[str] = None,
                   level: Optional[str] = None, scopes: Optional[List[str]] = None):
        """Create a new user."""
        url = f"{self.base_url}/api/users"
        
        data = {
            "username": username,
            "email": email,
            "full_name": full_name,
            "password": password,
            "is_external": is_external,
            "department": department,
            "job_title": job_title,
            "level": level,
            "scopes": scopes or []
        }
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_user(self, user_id: str):
        """Get user by ID."""
        url = f"{self.base_url}/api/users/{user_id}"
        
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def update_user(self, user_id: str, data: Dict[str, Any]):
        """Update user."""
        url = f"{self.base_url}/api/users/{user_id}"
        
        response = self.session.put(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def create_agent(self, agent_name: str, description: str, agent_type: str,
                    agent_model: str, agent_provider: str):
        """Create a new agent."""
        url = f"{self.base_url}/api/agents"
        
        data = {
            "agent_name": agent_name,
            "description": description,
            "agent_type": agent_type,
            "agent_model": agent_model,
            "agent_provider": agent_provider
        }
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_agent(self, agent_id: str):
        """Get agent by ID."""
        url = f"{self.base_url}/api/agents/{agent_id}"
        
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def get_token(self, client_id: str, client_secret: str, scope: List[str]):
        """Get OAuth token using client credentials grant."""
        url = f"{self.base_url}/api/oauth/token"
        
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope
        }
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def introspect_token(self, token: str):
        """Introspect OAuth token."""
        url = f"{self.base_url}/api/oauth/introspect"
        
        data = {"token": token}
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def revoke_token(self, token: str, revoke_children: bool = False):
        """Revoke OAuth token."""
        url = f"{self.base_url}/api/oauth/revoke"
        
        data = {
            "token": token,
            "revoke_children": revoke_children
        }
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def exchange_auth0_token(self, auth0_token: str):
        """Exchange Auth0 token for AgenticTrust token."""
        url = f"{self.base_url}/api/users/auth0/token"
        
        data = {"auth0_token": auth0_token}
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_user_profile(self, token: str):
        """Get user profile using Auth0 token."""
        url = f"{self.base_url}/api/users/profile"
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.session.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def create_user_agent_authorization(self, user_id: str, agent_id: str, scopes: List[str],
                                       constraints: Optional[Dict[str, Any]] = None,
                                       ttl_days: int = 30):
        """Create authorization for agent to act on behalf of user."""
        url = f"{self.base_url}/api/users/{user_id}/authorizations"
        
        data = {
            "user_id": user_id,
            "agent_id": agent_id,
            "scopes": scopes,
            "constraints": constraints,
            "ttl_days": ttl_days
        }
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_user_agent_authorizations(self, user_id: str):
        """Get all authorizations for a user."""
        url = f"{self.base_url}/api/users/{user_id}/authorizations"
        
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def revoke_user_agent_authorization(self, user_id: str, authorization_id: str):
        """Revoke authorization for agent to act on behalf of user."""
        url = f"{self.base_url}/api/users/{user_id}/authorizations/{authorization_id}"
        
        response = self.session.delete(url)
        response.raise_for_status()
        
        return response.json()
    
    def delegate_token(self, client_id: str, delegator_token: str, scopes: List[str], 
                      task_description: Optional[str] = None, task_id: Optional[str] = None, 
                      parent_task_id: Optional[str] = None, purpose: Optional[str] = None, 
                      constraints: Optional[Dict[str, Any]] = None, 
                      agent_instance_id: Optional[str] = None):
        """Request a delegated token from a human user to an agent."""
        url = f"{self.base_url}/api/oauth/delegate"
        
        data = {
            "client_id": client_id,
            "delegation_type": "human_to_agent",
            "delegator_token": delegator_token,
            "scope": scopes,
            "task_description": task_description,
            "task_id": task_id,
            "parent_task_id": parent_task_id,
            "purpose": purpose,
            "constraints": constraints,
            "agent_instance_id": agent_instance_id
        }
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    

    
    def get_delegation_chain(self, token_id: str):
        """Get delegation chain for a token."""
        url = f"{self.base_url}/api/audit/delegation/{token_id}/chain"
        
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def get_user_delegation_activity(self, user_id: str):
        """Get delegation activity for a user."""
        url = f"{self.base_url}/api/audit/delegation/user/{user_id}"
        
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def verify_with_rbac(self, token: str, resource: str, action: str):
        """Verify token and check RBAC permissions."""
        url = f"{self.base_url}/api/oauth/verify_with_rbac"
        
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "resource": resource,
            "action": action
        }
        
        response = self.session.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        return response.json()
