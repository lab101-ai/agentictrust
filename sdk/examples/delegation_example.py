"""
Example of human-to-agent delegation in AgenticTrust.
"""
import os
import sys
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from sdk.agentictrust.client import AgenticTrustClient

client = AgenticTrustClient(base_url="http://localhost:8000")

def authenticate_user():
    """Authenticate user and get token."""
    print("Authenticating user...")
    
    response = requests.post(
        "http://localhost:8000/api/oauth/token",
        json={
            "grant_type": "client_credentials",
            "client_id": "user-123",
            "client_secret": "user-secret",
            "scope": "read:data write:data"
        }
    )
    
    user_token = response.json()["access_token"]
    print(f"User authenticated, token received")
    
    return user_token

def authorize_agent(user_id, agent_id):
    """Create authorization for agent to act on behalf of user."""
    print(f"Creating user-agent authorization for user {user_id} and agent {agent_id}...")
    
    response = requests.post(
        f"http://localhost:8000/api/users/{user_id}/authorizations",
        json={
            "user_id": user_id,
            "agent_id": agent_id,
            "scopes": ["read:data", "write:data"],
            "constraints": {"time_restrictions": {"start_hour": 9, "end_hour": 17}},
            "ttl_days": 30
        }
    )
    
    authorization = response.json()
    print(f"Authorization created: {authorization['authorization_id']}")
    
    return authorization

def delegate_token(agent_id, user_token):
    """Request delegated token from user to agent."""
    print(f"Requesting delegated token for agent {agent_id}...")
    
    token_response = client.delegate_token(
        client_id=agent_id,
        delegator_token=user_token,
        scopes=["read:data"],
        task_description="Analyze user data",
        task_id="task-789",
        purpose="Data analysis"
    )
    
    print(f"Delegated token received: {token_response['access_token'][:10]}...")
    
    return token_response

def use_delegated_token(token_response):
    """Use delegated token to access resources."""
    print("Using delegated token to access resources...")
    
    access_token = token_response["access_token"]
    
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        "http://localhost:8000/api/protected-resource",
        headers=headers
    )
    
    print(f"Resource access result: {response.status_code}")
    
    return response

def view_delegation_audit(token_id, user_id):
    """View delegation audit information."""
    print("Viewing delegation audit information...")
    
    chain = client.get_delegation_chain(token_id)
    print(f"Delegation chain: {chain}")
    
    activity = client.get_user_delegation_activity(user_id)
    print(f"User delegation activity: {len(activity['delegations_as_principal'])} delegations")
    
    return chain, activity

def main():
    """Run the delegation example."""
    user_token = authenticate_user()
    
    user_id = "user-123"
    agent_id = "agent-456"
    authorization = authorize_agent(user_id, agent_id)
    
    token_response = delegate_token(agent_id, user_token)
    
    if not token_response:
        print("Failed to get delegated token")
        return
    
    resource_response = use_delegated_token(token_response)
    
    token_id = token_response["task_id"]
    chain, activity = view_delegation_audit(token_id, user_id)
    
    print("Delegation example completed successfully")

if __name__ == "__main__":
    main()
