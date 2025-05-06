"""
Pydantic models for OAuth/OIDC-A request validation.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal, Union, Dict, Any
from enum import Enum

# LaunchReason enum for token issuance context
class LaunchReason(str, Enum):
    user_interactive = "user_interactive"
    system_job = "system_job"
    agent_delegated = "agent_delegated"

# Define Delegation Step Structure (as per Proposal 2.4.2)
class DelegationStep(BaseModel):
    iss: str = Field(..., description="Issuer of this delegation step.")
    sub: str = Field(..., description="Subject identifier of the delegator.")
    aud: str = Field(..., description="Audience - identifier of the delegatee (agent).")
    delegated_at: int = Field(..., description="Timestamp of delegation (NumericDate).")
    scope: str = Field(..., description="Space-separated OAuth scopes granted.")
    purpose: Optional[str] = Field(None, description="Intended purpose of this delegation step.")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Constraints on the delegation.")
    jti: Optional[str] = Field(None, description="Unique identifier for this delegation step.")

# Define Agent Attestation Structure (placeholder - as per Proposal 2.4.4)
class AgentAttestation(BaseModel):
    format: str = Field(..., description="Format of the attestation evidence (e.g., 'jwt', 'saml').")
    evidence: Union[str, Dict[str, Any]] = Field(..., description="The attestation evidence itself or a reference.")

class TokenRequestBase(BaseModel):
    """Base model for common token request fields."""
    grant_type: str

class TokenRequestClientCredentials(TokenRequestBase):
    """Model for client_credentials grant type requests."""
    grant_type: Literal['client_credentials']
    client_id: str
    client_secret: str
    # Core Agent Identity Claims (REQUIRED by OIDC-A Proposal 2.1)
    agent_type: str = Field(..., description="Type/class of agent (e.g., 'assistant').")
    agent_model: str = Field(..., description="Specific model (e.g., 'gpt-4').")
    agent_provider: str = Field(..., description="Organization providing the agent.")
    agent_instance_id: str = Field(..., description="Unique identifier for this agent instance.") # Was already required

    # Delegation and Authority Claims (REQUIRED/RECOMMENDED by OIDC-A Proposal 2.2)
    delegator_sub: str = Field(..., description="Subject identifier of the delegator.")

    scope: Optional[str] = ""
    task_id: Optional[str] = None
    task_description: Optional[str] = None
    required_tools: Optional[List[str]] = Field(default_factory=list)
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None
    parent_token: Optional[str] = None
    scope_inheritance_type: Optional[Literal['restricted', 'inherited']] = 'restricted'

    # Optional/Recommended OIDC-A Claims (updated types)
    delegation_chain: Optional[List[DelegationStep]] = Field(None, description="Ordered array of delegation steps.")
    delegation_purpose: Optional[str] = Field(None, description="Overall purpose of the delegation.")
    delegation_constraints: Optional[Dict[str, Any]] = Field(None, description="Overall constraints placed by the initial delegator.")
    agent_capabilities: Optional[List[str]] = Field(default_factory=list, description="Array of capability identifiers.")
    agent_trust_level: Optional[str] = Field(None, description="Trust classification of the agent.")
    agent_attestation: Optional[AgentAttestation] = Field(None, description="Attestation evidence or reference.")
    agent_context_id: Optional[str] = Field(None, description="Identifier for the conversation/task context.")

    # Delegation support (Unified flow)
    delegation_grant_id: Optional[str] = Field(None, description="ID of DelegationGrant to act on behalf of a principal.")
    launch_reason: LaunchReason = Field(LaunchReason.user_interactive, description="Why token is being issued: user_interactive, system_job, or agent_delegated")
    launched_by: Optional[str] = Field(None, description="Identifier of who triggered issuance (user_id or client_id)")

    @validator('code_challenge_method')
    def validate_code_challenge_method(cls, v, values):
        if 'code_challenge' in values and values['code_challenge'] and not v:
            raise ValueError('code_challenge_method is required if code_challenge is provided')
        if v and v not in ['S256', 'plain']:
            raise ValueError('code_challenge_method must be S256 or plain')
        return v

    @validator('delegation_grant_id')
    def warn_delegation_grant_usage(cls, v):
        if v:
            import warnings
            warnings.warn(
                "TokenRequestDelegationToken grant_type is deprecated; use delegation_grant_id on standard grants.",
                DeprecationWarning,
            )
        return v

class TokenRequestRefreshToken(TokenRequestBase):
    """Model for refresh_token grant type requests."""
    grant_type: Literal['refresh_token']
    refresh_token: str
    scope: Optional[str] = None # Allow scope modification on refresh
    delegation_grant_id: Optional[str] = None
    launch_reason: LaunchReason = LaunchReason.user_interactive
    launched_by: Optional[str] = None

# -----------------------------------------------------------------------------
# New model for authorization_code grant
# -----------------------------------------------------------------------------

class TokenRequestAuthorizationCode(BaseModel):
    grant_type: Literal["authorization_code"]
    code: str
    client_id: str
    redirect_uri: str
    code_verifier: str
    scope: Optional[str] = None
    delegation_grant_id: Optional[str] = None
    launch_reason: LaunchReason = LaunchReason.user_interactive
    launched_by: Optional[str] = None

# Update Union (deprecated TokenRequestDelegationToken removed)
TokenRequest = Union[
    TokenRequestClientCredentials,
    TokenRequestRefreshToken,
    TokenRequestAuthorizationCode,
]

class IntrospectRequest(BaseModel):
    token: str
    token_type_hint: Optional[Literal['access_token', 'refresh_token']] = None

class RevokeRequest(BaseModel):
    token: str
    token_type_hint: Optional[Literal['access_token', 'refresh_token']] = None
    revoke_children: Optional[bool] = False  # Whether to revoke descendant tokens as well
