"""
API resource for token management.
"""
from typing import Dict, List, Optional, Any, Union

from .abstract import APIResource
from ..types.token import TokenRequestDict, TokenResponseDict, TokenIntrospectionDict, ParentTokenDict
from ..utils.validators import validate_string, validate_string_list, validate_dict, validate_bool


class TokensResource(APIResource):
    """API resource for token management."""
    
    def __init__(self, parent=None):
        """
        Initialize the tokens resource.
        
        Args:
            parent: Parent client instance
        """
        super().__init__(parent)
        self._current_token = None
        self._current_task_id = None
        self._parent_token = None
        self._parent_task_id = None
        self._current_token_id = None
    
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
        # Validate inputs
        client_id = validate_string(client_id, "client_id")
        client_secret = validate_string(client_secret, "client_secret")
        scope_list = validate_string_list(scope, "scope", required=False)
        task_id = validate_string(task_id, "task_id", required=False)
        task_description = validate_string(task_description, "task_description", required=False)
        required_tools = validate_string_list(required_tools, "required_tools", required=False)
        parent_task_id = validate_string(parent_task_id, "parent_task_id", required=False)
        parent_token = validate_string(parent_token, "parent_token", required=False)
        scope_inheritance_type = validate_string(scope_inheritance_type, "scope_inheritance_type")
        code_challenge = validate_string(code_challenge, "code_challenge", required=False)
        code_challenge_method = validate_string(code_challenge_method, "code_challenge_method")
        
        # Validate parent_tokens if provided
        validated_parent_tokens = None
        if parent_tokens:
            validated_parent_tokens = []
            for i, token_info in enumerate(parent_tokens):
                if not isinstance(token_info, dict):
                    raise ValueError(f"parent_tokens[{i}] must be a dictionary")
                
                validated_token_info = {
                    "token": validate_string(token_info.get("token"), f"parent_tokens[{i}].token"),
                    "task_id": validate_string(token_info.get("task_id"), f"parent_tokens[{i}].task_id"),
                }
                validated_parent_tokens.append(validated_token_info)
        
        # Prepare request data
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": " ".join(scope_list) if isinstance(scope_list, list) else scope_list,
        }
        
        if task_id:
            data["task_id"] = task_id
            
        if task_description:
            data["task_description"] = task_description
            
        if required_tools:
            data["required_tools"] = required_tools
            
        if parent_task_id:
            data["parent_task_id"] = parent_task_id
            
        if parent_token:
            data["parent_token"] = parent_token
            
        if scope_inheritance_type:
            data["scope_inheritance_type"] = scope_inheritance_type
            
        if code_challenge:
            data["code_challenge"] = code_challenge
            data["code_challenge_method"] = code_challenge_method
            
        if validated_parent_tokens:
            data["parent_tokens"] = validated_parent_tokens
        
        # Make API request
        response = self._request("POST", "/api/oauth/token", data=data)
        
        # Store current token and task ID for convenience
        self._current_token = response.get("access_token")
        self._current_task_id = response.get("task_id")
        self._current_token_id = response.get("token_id")
        
        # Store parent context if provided
        if parent_token:
            self._parent_token = parent_token
            self._parent_task_id = parent_task_id
            
        return response
    
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
        # Use current token/task_id if not provided
        token = token or self._current_token
        task_id = task_id or self._current_task_id
        parent_task_id = parent_task_id or self._parent_task_id
        parent_token = parent_token or self._parent_token
        
        # Validate inputs
        token = validate_string(token, "token")
        task_id = validate_string(task_id, "task_id")
        allow_clock_skew = validate_bool(allow_clock_skew, "allow_clock_skew")
        
        # Validate parent_tokens if provided
        validated_parent_tokens = None
        if parent_tokens:
            validated_parent_tokens = []
            for i, token_info in enumerate(parent_tokens):
                if not isinstance(token_info, dict):
                    raise ValueError(f"parent_tokens[{i}] must be a dictionary")
                
                validated_token_info = {
                    "token": validate_string(token_info.get("token"), f"parent_tokens[{i}].token"),
                    "task_id": validate_string(token_info.get("task_id"), f"parent_tokens[{i}].task_id"),
                }
                validated_parent_tokens.append(validated_token_info)
        
        # Prepare request data
        data = {
            "token": token,
            "task_id": task_id,
            "allow_clock_skew": allow_clock_skew,
            "max_clock_skew_seconds": max_clock_skew_seconds,
        }
        
        if parent_task_id:
            data["parent_task_id"] = parent_task_id
            
        if parent_token:
            data["parent_token"] = parent_token
            
        if validated_parent_tokens:
            data["parent_tokens"] = validated_parent_tokens
        
        # Make API request
        return self._request("POST", "/api/tokens/verify", json_data=data)
    
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
        # Use current token/task_id if not provided
        token = token or self._current_token
        task_id = task_id or self._current_task_id
        
        # Validate inputs
        tool_name = validate_string(tool_name, "tool_name")
        token = validate_string(token, "token")
        task_id = validate_string(task_id, "task_id")
        allow_clock_skew = validate_bool(allow_clock_skew, "allow_clock_skew")
        
        # Validate parent_tokens if provided
        validated_parent_tokens = None
        if parent_tokens:
            validated_parent_tokens = []
            for i, token_info in enumerate(parent_tokens):
                if not isinstance(token_info, dict):
                    raise ValueError(f"parent_tokens[{i}] must be a dictionary")
                
                validated_token_info = {
                    "token": validate_string(token_info.get("token"), f"parent_tokens[{i}].token"),
                    "task_id": validate_string(token_info.get("task_id"), f"parent_tokens[{i}].task_id"),
                }
                validated_parent_tokens.append(validated_token_info)
        
        # Prepare request data
        data = {
            "tool_name": tool_name,
            "token": token,
            "task_id": task_id,
            "allow_clock_skew": allow_clock_skew,
            "max_clock_skew_seconds": max_clock_skew_seconds,
        }
        
        if validated_parent_tokens:
            data["parent_tokens"] = validated_parent_tokens
        
        # Make API request
        return self._request("POST", "/api/tokens/verify-tool-access", json_data=data)
    
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
        # Use current token if not provided
        token = token or self._current_token
        
        # Validate inputs
        token = validate_string(token, "token")
        include_task_history = validate_bool(include_task_history, "include_task_history")
        include_children = validate_bool(include_children, "include_children")
        
        # Prepare request data
        data = {
            "token": token,
            "include_task_history": include_task_history,
            "include_children": include_children,
        }
        
        # Make API request
        return self._request("POST", "/api/tokens/introspect", json_data=data)
    
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
        # Use current token if not provided
        token = token or self._current_token
        
        # Validate inputs
        token = validate_string(token, "token")
        reason = validate_string(reason, "reason", required=False)
        
        # Prepare request data
        data = {
            "token": token,
        }
        
        if reason:
            data["reason"] = reason
        
        # Make API request
        response = self._request("POST", "/api/tokens/revoke", json_data=data)
        
        # Clear current token if we just revoked it
        if token == self._current_token:
            self._current_token = None
            self._current_task_id = None
            self._current_token_id = None
            
        return response
    
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
        # Validate inputs
        refresh_token = validate_string(refresh_token, "refresh_token")
        client_id = validate_string(client_id, "client_id", required=False)
        client_secret = validate_string(client_secret, "client_secret", required=False)
        
        # Prepare request data
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        
        if client_id:
            data["client_id"] = client_id
            
        if client_secret:
            data["client_secret"] = client_secret
        
        # Make API request
        response = self._request("POST", "/api/oauth/token", data=data)
        
        # Update current token and task ID
        self._current_token = response.get("access_token")
        self._current_task_id = response.get("task_id")
        self._current_token_id = response.get("token_id")
        
        return response
    
    def get_current_token(self) -> Optional[str]:
        """
        Get the current token.
        
        Returns:
            Current token or None if no token is set
        """
        return self._current_token
    
    def get_current_task_id(self) -> Optional[str]:
        """
        Get the current task ID.
        
        Returns:
            Current task ID or None if no task ID is set
        """
        return self._current_task_id
    
    def set_current_token(self, token: str, task_id: str) -> None:
        """
        Set the current token and task ID.
        
        Args:
            token: Token to set as current
            task_id: Task ID to set as current
        """
        self._current_token = validate_string(token, "token")
        self._current_task_id = validate_string(task_id, "task_id")
    
    def set_parent_context(self, parent_token: str, parent_task_id: str) -> None:
        """
        Set the parent token and task ID.
        
        Args:
            parent_token: Parent token to set
            parent_task_id: Parent task ID to set
        """
        self._parent_token = validate_string(parent_token, "parent_token")
        self._parent_task_id = validate_string(parent_task_id, "parent_task_id")
