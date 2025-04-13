"""
Main client for the AgenticTrust SDK.
"""

import uuid
import json
import time
from typing import Dict, List, Optional, Union, Any

from .utils import http

# Import client classes
from .agents import AgentClient
from .tokens import TokenClient
from .tools import ToolClient

# Import configuration
from .config import Configuration, default_config

# Import exceptions
from .exceptions import AgenticTrustError


class AgenticTrustClient:
    """Main client for interacting with the AgenticTrust API."""

    def __init__(
        self,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        debug: bool = False,
        default_timeout: int = 60,
        max_retries: int = 3,
        proxies: Optional[Dict[str, str]] = None,
    ):
        """Initialize the client with configuration options.

        Args:
            api_base: Base URL for the AgenticTrust server (default: http://localhost:5001)
            api_key: API key to use for authentication (if applicable)
            debug: Whether to enable debug mode
            default_timeout: Default timeout for API requests in seconds
            max_retries: Maximum number of retries for failed requests
            proxies: Proxy configuration for requests
        """
        # Use provided configuration or fall back to environment variables and defaults
        config_params = {k: v for k, v in {
            "api_base": api_base,
            "api_key": api_key,
            "debug": debug,
            "default_timeout": default_timeout,
            "max_retries": max_retries,
            "proxies": proxies,
        }.items() if v is not None}

        # Create a custom configuration if any parameters were provided
        if config_params:
            self.config = Configuration(**config_params)
            # Update the default configuration as well
            for key, value in config_params.items():
                setattr(default_config, key, value)
        else:
            # Use the default configuration
            self.config = default_config

        # Initialize API clients
        self.agent = AgentClient(self)
        self.token = TokenClient(self)
        self.tool = ToolClient(self)

    @property
    def api_base(self) -> str:
        """Get the base URL for the API."""
        return self.config.api_base

    @api_base.setter
    def api_base(self, value: str) -> None:
        """Set the base URL for the API."""
        self.config.api_base = value.rstrip("/")
        default_config.api_base = value.rstrip("/")

    @property
    def api_key(self) -> Optional[str]:
        """Get the API key."""
        return self.config.api_key

    @api_key.setter
    def api_key(self, value: Optional[str]) -> None:
        """Set the API key."""
        self.config.api_key = value
        default_config.api_key = value

    @property
    def debug(self) -> bool:
        """Get the debug mode status."""
        return self.config.debug

    @debug.setter
    def debug(self, value: bool) -> None:
        """Set the debug mode status."""
        self.config.debug = value
        default_config.debug = value

    def __repr__(self) -> str:
        return f"<AgenticTrustClient(api_base='{self.api_base}')>"

    def _make_request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the AgenticTrust API using the HTTP utilities module.
        
        Args:
            method: HTTP method to use
            path: API endpoint path
            **kwargs: Additional arguments to pass to the request
            
        Returns:
            Dict containing the API response
            
        Raises:
            APIError: If the request fails
            AuthenticationError: For authentication failures
            InvalidRequestError: For invalid request parameters
            RateLimitError: For rate limiting errors
            APIConnectionError: For network errors
            ScopeError: For scope-related errors
            ToolAccessError: For tool access errors
        """
        # Extract parameters for the http.make_request function
        params = kwargs.pop('params', None)
        data = kwargs.pop('data', None)
        headers = kwargs.pop('headers', {})
        files = kwargs.pop('files', None)
        json_data = kwargs.pop('json', None)
        timeout = kwargs.pop('timeout', self.config.default_timeout)
        stream = kwargs.pop('stream', False)
        
        # Add API key to headers if provided
        if self.api_key and 'Authorization' not in headers:
            headers['Authorization'] = f"Bearer {self.api_key}"
        
        # Temporarily store original API base and debug settings
        original_api_base = http.default_config.api_base
        original_debug = http.default_config.debug
        original_proxies = http.default_config.proxies
        
        try:
            # Update config with client-specific settings
            http.default_config.api_base = self.api_base
            http.default_config.debug = self.debug
            http.default_config.proxies = self.config.proxies if hasattr(self.config, 'proxies') else None
            
            # Make the request using the utility function
            return http.make_request(
                method=method,
                path=path,
                params=params,
                data=data,
                headers=headers,
                files=files,
                json_data=json_data,
                timeout=timeout,
                stream=stream
            )
        finally:
            # Restore original config values
            http.default_config.api_base = original_api_base
            http.default_config.debug = original_debug
            http.default_config.proxies = original_proxies



class TokenClient:
    """
    Client for token management.
    """

    def __init__(self, parent):
        """Initialize with parent client."""
        self.parent = parent
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
    ) -> Dict[str, Any]:
        """Request a new token from the AgenticTrust server.

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
            "parent_task_id": parent_task_id,
            "parent_token": parent_token,
            "scope_inheritance_type": scope_inheritance_type,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
        }

        # Add parent tokens list if provided
        if parent_tokens:
            data["parent_tokens"] = parent_tokens

        response = self.parent._make_request("POST", "/api/oauth/token", json=data)

        # Store current token and task context
        self._current_token = response.get("access_token")
        self._current_task_id = response.get("task_id")
        self._parent_token = parent_token
        self._parent_task_id = parent_task_id
        self._current_token_id = response.get("token_id")

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
        """Verify a token and its task context.

        Args:
            token: The token to verify (uses current token if not provided)
            task_id: The task ID to verify (uses current task ID if not provided)
            parent_task_id: The parent task ID to verify (uses current parent task ID if not provided)
            parent_token: The parent token to verify (uses current parent token if not provided)
            parent_tokens: Optional list of parent tokens to verify in the chain
                           Format: [{"token": "token_string", "task_id": "task_id"}, ...]
            allow_clock_skew: Whether to allow clock skew between systems
            max_clock_skew_seconds: Maximum allowed clock skew in seconds

        Returns:
            Dict containing verification results
        """
        token_to_verify = token or self._current_token
        if not token_to_verify:
            raise ValueError(
                "No token available. Please provide a token or request one first."
            )

        # Debug info about the token being verified (only if debug mode is enabled)
        if (
            self.parent.config.debug
            and isinstance(token_to_verify, str)
            and len(token_to_verify) > 20
        ):
            print(
                f"DEBUG: Verifying token: {token_to_verify[:20]}... (length: {len(token_to_verify)})"
            )
            # Check if it has Bearer prefix
            if token_to_verify.startswith("Bearer "):
                print(
                    "WARNING: Token has 'Bearer ' prefix which may cause verification issues"
                )
                # Remove the Bearer prefix
                token_to_verify = token_to_verify[7:]
                print(
                    f"DEBUG: Fixed token: {token_to_verify[:20]}... (length: {len(token_to_verify)})"
                )

            # Debug info will be sent to server for verification

        data = {}
        data["token"] = token_to_verify
        data["task_id"] = task_id or self._current_task_id
        data["parent_task_id"] = parent_task_id or self._parent_task_id
        data["parent_token"] = parent_token or self._parent_token

        # Add clock skew parameters if requested
        if allow_clock_skew:
            data["allow_clock_skew"] = True
            data["max_clock_skew_seconds"] = max_clock_skew_seconds

        # Add parent tokens list if provided
        if parent_tokens:
            data["parent_tokens"] = parent_tokens

        try:
            result = self.parent._make_request("POST", "/api/oauth/verify", json=data)
            # Check if verification failed
            if (
                result
                and not result.get("is_valid", False)
                and self.parent.config.debug
            ):
                print(
                    f"Token verification failed: {result.get('error', 'Unknown error')}"
                )
                debug_info = result.get("debug_info", {})
                if debug_info:
                    print(f"Debug info: {debug_info}")
            return result
        except Exception as e:
            if self.parent.config.debug:
                print(f"Token verification request failed: {str(e)}")
                # Try to extract useful information from the error
                error_str = str(e)
                if "Debug info" in error_str:
                    debug_start = error_str.find("Debug info")
                    debug_info = error_str[debug_start:]
                    print(f"Error debug info: {debug_info}")
            raise

    def verify_tool_access(
        self,
        tool_name: str,
        token: Optional[str] = None,
        task_id: Optional[str] = None,
        parent_tokens: Optional[List[Dict[str, str]]] = None,
        allow_clock_skew: bool = True,
        max_clock_skew_seconds: int = 86400,
    ) -> Dict[str, Any]:
        """Verify if a token has access to use a specific tool.

        Args:
            tool_name: The name of the tool to verify access for
            token: The token to verify (uses current token if not provided)
            task_id: The task ID (uses current task ID if not provided)
            parent_tokens: Optional list of parent tokens to verify in the chain
                          Format: [{"token": "token_string", "task_id": "task_id"}, ...]
            allow_clock_skew: Whether to allow clock skew between systems
            max_clock_skew_seconds: Maximum allowed clock skew in seconds

        Returns:
            Dict containing tool access verification results
        """
        # Prepare headers with token for authentication
        headers = {}
        headers["Authorization"] = f"Bearer {token or self._current_token}"

        # Prepare data
        data = {}
        data["tool_name"] = tool_name
        data["task_id"] = task_id or self._current_task_id

        # Add parent tokens list if provided
        if parent_tokens:
            data["parent_tokens"] = parent_tokens

        # Add clock skew parameters if requested
        if allow_clock_skew:
            data["allow_clock_skew"] = True
            data["max_clock_skew_seconds"] = max_clock_skew_seconds

        return self.parent._make_request(
            "POST", "/api/oauth/tool", json=data, headers=headers
        )

    def introspect(
        self,
        token: Optional[str] = None,
        include_task_history: bool = False,
        include_children: bool = False,
    ) -> Dict[str, Any]:
        """Introspect a token to get detailed information about it.

        Args:
            token: The token to introspect (uses current token if not provided)
            include_task_history: Whether to include task history
            include_children: Whether to include child tokens

        Returns:
            Dict containing token details
        """
        data = {}
        data["token"] = token or self._current_token
        data["include_task_history"] = include_task_history
        data["include_children"] = include_children

        return self.parent._make_request("POST", "/api/oauth/introspect", json=data)

    def revoke(
        self, token: Optional[str] = None, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Revoke a token.

        Args:
            token: The token to revoke (uses current token if not provided)
            reason: Optional reason for revocation

        Returns:
            Dict containing revocation status
        """
        data = {}
        data["token"] = token or self._current_token
        data["reason"] = reason

        response = self.parent._make_request("POST", "/api/oauth/revoke", json=data)

        # Clear current token if it's the one being revoked
        if token is None or token == self._current_token:
            self._current_token = None
            self._current_task_id = None
            self._current_token_id = None

        return response

    def refresh(
        self,
        refresh_token: str,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Refresh an access token using a refresh token.

        Args:
            refresh_token: The refresh token to use
            client_id: The client ID (required for OAuth 2.1)
            client_secret: The client secret (required for OAuth 2.1)

        Returns:
            Dict containing new token details
        """
        # For OAuth 2.1, PKCE is required for token refresh
        # Generate a code verifier
        code_verifier = secrets.token_urlsafe(64)

        if not client_id or not client_secret:
            raise ValueError(
                "client_id and client_secret are required for token refresh in OAuth 2.1"
            )

        data = {}
        data["grant_type"] = "refresh_token"
        data["refresh_token"] = refresh_token
        data["client_id"] = client_id
        data["client_secret"] = client_secret
        data["code_verifier"] = code_verifier

        response = self.parent._make_request("POST", "/api/oauth/token", json=data)

        # Update stored token
        self._current_token = response.get("access_token")
        self._current_task_id = response.get("task_id")
        self._current_token_id = response.get("token_id")

        return response

    def call_protected_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        token: Optional[str] = None,
        task_id: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        parent_token: Optional[str] = None,
        allow_clock_skew: bool = True,
        max_clock_skew_seconds: int = 86400,
    ) -> Dict[str, Any]:
        """Call a protected endpoint using token authentication.

        Args:
            endpoint: The API endpoint path to call
            method: HTTP method to use
            data: Optional data to send with the request
            token: The token to use
            task_id: The task ID to include in headers
            parent_task_id: The parent task ID to include in headers
            parent_token: The parent token to include in headers
            allow_clock_skew: Whether to allow clock skew
            max_clock_skew_seconds: Maximum allowed clock skew in seconds

        Returns:
            Dict containing response from the protected endpoint
        """
        token_to_use = token or self._current_token
        if not token_to_use:
            raise ValueError("No token available. Request a token first.")

        # Create headers with proper Bearer token format
        headers = {}
        headers["Authorization"] = f"Bearer {token_to_use}"
        headers["X-Task-ID"] = task_id or self._current_task_id or ""

        if parent_task_id or self._parent_task_id:
            headers["X-Parent-Task-ID"] = parent_task_id or self._parent_task_id

        if parent_token:
            headers["X-Parent-Token"] = parent_token

        # Add clock skew headers
        if allow_clock_skew:
            headers["X-Allow-Clock-Skew"] = "true"
            headers["X-Max-Clock-Skew-Seconds"] = str(max_clock_skew_seconds)

        # Make the request to the protected endpoint
        return self.parent._make_request(method, endpoint, json=data, headers=headers)


class ToolClient:
    """Client for tool management."""

    def __init__(self, parent):
        """Initialize with parent client."""
        self.parent = parent

    def list(
        self, category: Optional[str] = None, is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """List all registered tools, with optional filtering.

        Args:
            category: Optional category to filter by
            is_active: Optional active status to filter by

        Returns:
            Dict containing list of tools
        """
        params = {}
        if category:
            params["category"] = category

        if is_active is not None:
            params["is_active"] = str(is_active).lower()

        return self.parent._make_request("GET", "/api/tools", params=params)

    def get(self, tool_id: str) -> Dict[str, Any]:
        """Get tool details by tool ID.

        Args:
            tool_id: The ID of the tool

        Returns:
            Dict containing tool details
        """
        return self.parent._make_request("GET", f"/api/tools/{tool_id}")

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        permissions_required: Optional[List[str]] = None,
        parameters: Optional[List[Dict[str, Any]]] = None,
        input_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new tool.

        Args:
            name: The name of the tool
            description: Optional description of the tool
            category: Optional category for the tool
            permissions_required: List of required permissions to use the tool
            parameters: List of parameter definitions for the tool
            input_schema: Optional JSON schema for tool input validation

        Returns:
            Dict containing created tool details
        """
        data = {}
        data["name"] = name
        data["description"] = description
        data["category"] = category
        data["permissions_required"] = permissions_required or []
        data["parameters"] = parameters or []
        data["input_schema"] = input_schema

        return self.parent._make_request("POST", "/api/tools", json=data)

    def update(self, tool_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update an existing tool.

        Args:
            tool_id: The ID of the tool to update
            **kwargs: Fields to update (name, description, category, inputSchema, etc.)

        Returns:
            Dict containing updated tool details
        """
        # Handle parameters if provided to convert to inputSchema
        if "parameters" in kwargs and "inputSchema" not in kwargs:
            kwargs["inputSchema"] = kwargs.pop("parameters")

        return self.parent._make_request("PUT", f"/api/tools/{tool_id}", json=kwargs)

    def delete(self, tool_id: str) -> Dict[str, Any]:
        """
        Delete a tool.

        Args:
            tool_id: The ID of the tool to delete

        Returns:
            Dict containing deletion status
        """
        return self.parent._make_request("DELETE", f"/api/tools/{tool_id}")

    def activate(self, tool_id: str) -> Dict[str, Any]:
        """
        Activate a tool.

        Args:
            tool_id: The ID of the tool to activate

        Returns:
            Dict containing updated tool details
        """
        return self.parent._make_request("POST", f"/api/tools/{tool_id}/activate")

    def deactivate(self, tool_id: str) -> Dict[str, Any]:
        """
        Deactivate a tool.

        Args:
            tool_id: The ID of the tool to deactivate

        Returns:
            Dict containing updated tool details
        """
        return self.parent._make_request("POST", f"/api/tools/{tool_id}/deactivate")
