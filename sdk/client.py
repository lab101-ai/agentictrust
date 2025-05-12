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
from .scopes import ScopesClient
from .policies import PoliciesClient
from .delegations import DelegationsClient

# Import configuration
from .config import Configuration, default_config

# Import exceptions
from .exceptions import AgenticTrustError, APIError, AuthenticationError, InvalidRequestError, RateLimitError, APIConnectionError, ScopeError, ToolAccessError


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
        self.scopes = ScopesClient(self)
        self.policies = PoliciesClient(self)
        self.delegations = DelegationsClient(self)

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

