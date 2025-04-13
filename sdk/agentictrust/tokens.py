"""
Client for token management.
"""
from typing import Dict, List, Optional, Any, Union

from .api_resources.tokens import TokensResource
from .types.token import TokenRequestDict, TokenResponseDict, TokenIntrospectionDict, ParentTokenDict
from .utils.validators import validate_string, validate_string_list, validate_dict, validate_bool


class TokenClient:
    """
    Client for token management.
    """
    
    def __init__(self, parent=None):
        """
        Initialize with parent client.
        
        Args:
            parent: Parent AgenticTrustClient instance
        """
        self.parent = parent
        self._api = TokensResource(parent)
    
    def request(
        self,
        client_id: str,
        client_secret: str,
        scope: Union[List[str], str] = [],
        task_id: Optional[str] = None,
        task_description: Optional[str] = None,
        required_tools: Optional[List[str]] = None,
        parent_task_id: Optional[str] = None,
        parent_token: Optional[str] = None,
        scope_inheritance_type: str = "restricted",
        code_challenge: Optional[str] = None,
        code_challenge_method: str = "S256",
        parent_tokens: Optional[List[Dict[str, str]]] = None,
    ) -> TokenResponseDict:
        """
        Request a new token from the AgenticTrust server.
        
        Args:
            client_id: The client ID of the agent
            client_secret: The client secret of the agent
            scope: List of requested scopes or space-separated string
            task_id: Optional task ID (generated if not provided)
            task_description: Optional description of the task
            required_tools: List of required tools for this task
            parent_task_id: Optional parent task ID (for child agents)
            parent_token: Optional parent token (for child agents)
            scope_inheritance_type: Type of scope inheritance (default: "restricted")
            code_challenge: PKCE code challenge (required for OAuth 2.1)
            code_challenge_method: PKCE code challenge method (default: "S256")
            parent_tokens: Optional list of parent tokens in the chain (for multi-level task inheritance)
                         Format: [{"token": "token_string", "task_id": "task_id"}, ...]
            
        Returns:
            Dict containing token details
        """
        return self._api.request(
            client_id=client_id,
            client_secret=client_secret,
            scope=scope,
            task_id=task_id,
            task_description=task_description,
            required_tools=required_tools,
            parent_task_id=parent_task_id,
            parent_token=parent_token,
            scope_inheritance_type=scope_inheritance_type,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            parent_tokens=parent_tokens,
        )
    
    def verify(
        self,
        token: Optional[str] = None,
        task_id: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        parent_token: Optional[str] = None,
        parent_tokens: Optional[List[Dict[str, str]]] = None,
        allow_clock_skew: bool = True,
        max_clock_skew_seconds: int = 86400,
    ) -> Dict[str, Any]:
        """
        Verify a token and its task context.
        
        Args:
            token: The token to verify (uses current token if not provided)
            task_id: The task ID to verify (uses current task ID if not provided)
            parent_task_id: The parent task ID to verify (uses current parent task ID if not provided)
            parent_token: The parent token to verify (uses current parent token if not provided)
            parent_tokens: Optional list of parent tokens to verify in the chain
                         Format: [{"token": "token_string", "task_id": "task_id"}, ...]
            allow_clock_skew: Whether to allow clock skew between systems (default: True)
            max_clock_skew_seconds: Maximum allowed clock skew in seconds (default: 86400, 1 day)
            
        Returns:
            Dict containing verification results
        """
        return self._api.verify(
            token=token,
            task_id=task_id,
            parent_task_id=parent_task_id,
            parent_token=parent_token,
            parent_tokens=parent_tokens,
            allow_clock_skew=allow_clock_skew,
            max_clock_skew_seconds=max_clock_skew_seconds,
        )
    
    def verify_tool_access(
        self,
        tool_name: str,
        token: Optional[str] = None,
        task_id: Optional[str] = None,
        parent_tokens: Optional[List[Dict[str, str]]] = None,
        allow_clock_skew: bool = True,
        max_clock_skew_seconds: int = 86400,
    ) -> Dict[str, Any]:
        """
        Verify if a token has access to use a specific tool.
        
        Args:
            tool_name: The name of the tool to verify access for
            token: The token to verify (uses current token if not provided)
            task_id: The task ID (uses current task ID if not provided)
            parent_tokens: Optional list of parent tokens to verify in the chain
                          Format: [{"token": "token_string", "task_id": "task_id"}, ...]
            allow_clock_skew: Whether to allow clock skew between systems (default: True)
            max_clock_skew_seconds: Maximum allowed clock skew in seconds (default: 86400, 1 day)
            
        Returns:
            Dict containing tool access verification results
        """
        return self._api.verify_tool_access(
            tool_name=tool_name,
            token=token,
            task_id=task_id,
            parent_tokens=parent_tokens,
            allow_clock_skew=allow_clock_skew,
            max_clock_skew_seconds=max_clock_skew_seconds,
        )
    
    def introspect(
        self,
        token: Optional[str] = None,
        include_task_history: bool = False,
        include_children: bool = False,
    ) -> TokenIntrospectionDict:
        """
        Introspect a token to get detailed information about it.
        
        Args:
            token: The token to introspect (uses current token if not provided)
            include_task_history: Whether to include task history
            include_children: Whether to include child tokens
            
        Returns:
            Dict containing token details
        """
        return self._api.introspect(
            token=token,
            include_task_history=include_task_history,
            include_children=include_children,
        )
    
    def revoke(
        self,
        token: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Revoke a token.
        
        Args:
            token: The token to revoke (uses current token if not provided)
            reason: Optional reason for revocation
            
        Returns:
            Dict containing revocation status
        """
        return self._api.revoke(
            token=token,
            reason=reason,
        )
    
    def refresh(
        self,
        refresh_token: str,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ) -> TokenResponseDict:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: The refresh token to use
            client_id: The client ID (required for OAuth 2.1)
            client_secret: The client secret (required for OAuth 2.1)
            
        Returns:
            Dict containing new token details
        """
        return self._api.refresh(
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
        )
    
    def get_current_token(self) -> Optional[str]:
        """
        Get the current token.
        
        Returns:
            Current token or None if no token is set
        """
        return self._api.get_current_token()
    
    def get_current_task_id(self) -> Optional[str]:
        """
        Get the current task ID.
        
        Returns:
            Current task ID or None if no task ID is set
        """
        return self._api.get_current_task_id()
    
    def set_current_token(self, token: str, task_id: str) -> None:
        """
        Set the current token and task ID.
        
        Args:
            token: Token to set as current
            task_id: Task ID to set as current
        """
        self._api.set_current_token(token=token, task_id=task_id)
    
    def set_parent_context(self, parent_token: str, parent_task_id: str) -> None:
        """
        Set the parent token and task ID.
        
        Args:
            parent_token: Parent token to set
            parent_task_id: Parent task ID to set
        """
        self._api.set_parent_context(parent_token=parent_token, parent_task_id=parent_task_id)
