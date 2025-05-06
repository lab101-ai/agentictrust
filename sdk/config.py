"""
Configuration management for the AgenticTrust SDK.
"""
import os
from typing import Dict, Any, Optional


class Configuration:
    """
    Configuration management for the AgenticTrust SDK.
    """
    
    def __init__(
        self,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        debug: bool = False,
        default_timeout: int = 60,
        max_retries: int = 3,
        proxies: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the configuration.
        
        Args:
            api_base: Base URL for the AgenticTrust server
            api_key: API key to use for authentication (if applicable)
            debug: Whether to enable debug mode
            default_timeout: Default timeout for API requests in seconds
            max_retries: Maximum number of retries for failed requests
            proxies: Proxy configuration for requests
        """
        # Set api_base with fallback to environment variable or default
        self.api_base = api_base or os.environ.get("AGENTICTRUST_API_BASE", "http://localhost:5001")
        
        # Remove trailing slash if present for consistency
        self.api_base = self.api_base.rstrip('/')
        
        # Set api_key with fallback to environment variable
        self.api_key = api_key or os.environ.get("AGENTICTRUST_API_KEY")
        
        # Other settings
        self.debug = debug or os.environ.get("AGENTICTRUST_DEBUG", "").lower() in ("true", "1", "t")
        self.default_timeout = int(os.environ.get("AGENTICTRUST_TIMEOUT", default_timeout))
        self.max_retries = int(os.environ.get("AGENTICTRUST_MAX_RETRIES", max_retries))
        self.proxies = proxies
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to a dictionary.
        
        Returns:
            Dict containing configuration values
        """
        return {
            "api_base": self.api_base,
            "api_key": "**redacted**" if self.api_key else None,
            "debug": self.debug,
            "default_timeout": self.default_timeout,
            "max_retries": self.max_retries,
            "proxies": self.proxies,
        }
        
    def __repr__(self) -> str:
        return f"<Configuration {self.to_dict()}>"


# Default configuration instance
default_config = Configuration()
