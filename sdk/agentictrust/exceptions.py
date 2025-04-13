"""
Exceptions for the AgenticTrust SDK.
"""
from typing import Dict, Any, Optional, List


class AgenticTrustError(Exception):
    """Base exception class for AgenticTrust errors."""
    
    def __init__(
        self, 
        message: str,
        http_status: Optional[int] = None,
        error_code: Optional[str] = None,
        error_data: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ):
        self.message = message
        self.http_status = http_status
        self.error_code = error_code
        self.error_data = error_data or {}
        self.request_id = request_id
        
        error_message = message
        if http_status is not None:
            error_message = f"HTTP {http_status}: {error_message}"
        if error_code is not None:
            error_message = f"{error_message} (Error code: {error_code})"
        if request_id is not None:
            error_message = f"{error_message} [Request ID: {request_id}]"
            
        super().__init__(error_message)


class APIError(AgenticTrustError):
    """Error returned by the AgenticTrust API."""
    pass


class AuthenticationError(AgenticTrustError):
    """Authentication-related errors."""
    pass


class InvalidRequestError(AgenticTrustError):
    """Error due to an invalid request."""
    pass


class RateLimitError(AgenticTrustError):
    """Error due to exceeding the rate limit."""
    pass


class APIConnectionError(AgenticTrustError):
    """Network communication errors."""
    pass


class ScopeError(AgenticTrustError):
    """Error related to token scopes."""
    
    def __init__(
        self,
        message: str,
        http_status: Optional[int] = None,
        error_code: Optional[str] = None, 
        error_data: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        exceeded_scopes: Optional[List[str]] = None,
        available_parent_scopes: Optional[List[str]] = None,
    ):
        self.exceeded_scopes = exceeded_scopes or []
        self.available_parent_scopes = available_parent_scopes or []
        
        super().__init__(message, http_status, error_code, error_data, request_id)


class ToolAccessError(AgenticTrustError):
    """Error related to tool access."""
    
    def __init__(
        self,
        message: str,
        http_status: Optional[int] = None,
        error_code: Optional[str] = None, 
        error_data: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        exceeded_tools: Optional[List[str]] = None,
        available_parent_tools: Optional[List[str]] = None,
    ):
        self.exceeded_tools = exceeded_tools or []
        self.available_parent_tools = available_parent_tools or []
        
        super().__init__(message, http_status, error_code, error_data, request_id)
