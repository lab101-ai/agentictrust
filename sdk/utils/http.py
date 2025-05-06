"""
HTTP utilities for making API requests.
"""
import json
import uuid
from typing import Dict, Any, Optional, Union, List, Tuple
import httpx

from ..exceptions import (
    APIError,
    AuthenticationError,
    InvalidRequestError,
    RateLimitError,
    APIConnectionError,
    ScopeError,
    ToolAccessError,
)
from ..config import default_config


def handle_error_response(response: httpx.Response) -> Dict[str, Any]:
    """
    Handle an error response from the API.
    
    Args:
        response: The response from the API
        
    Returns:
        A dictionary containing error details
        
    Raises:
        APIError: If the request fails
    """
    error_data = {}
    request_id = None
    
    # Try to parse error response as JSON
    try:
        error_data = response.json()
        request_id = error_data.get("request_id")
    except (ValueError, KeyError):
        # If JSON parsing fails, use text response
        error_message = response.text[:200]  # Limit text size
    
    status_code = response.status_code
    error_type = error_data.get("error", "unknown_error")
    error_message = error_data.get("error_description", response.text[:200])
    
    # Handle specific error types
    if status_code == 401:
        raise AuthenticationError(
            message=error_message,
            http_status=status_code,
            error_code=error_type,
            error_data=error_data,
            request_id=request_id,
        )
    elif status_code == 400:
        raise InvalidRequestError(
            message=error_message,
            http_status=status_code,
            error_code=error_type,
            error_data=error_data,
            request_id=request_id,
        )
    elif status_code == 429:
        raise RateLimitError(
            message=error_message,
            http_status=status_code,
            error_code=error_type,
            error_data=error_data,
            request_id=request_id,
        )
    elif status_code == 403 and error_type == "invalid_scope":
        # Handle scope inheritance errors with details
        details = error_data.get("details", {})
        
        raise ScopeError(
            message=error_message,
            http_status=status_code,
            error_code=error_type,
            error_data=error_data,
            request_id=request_id,
            exceeded_scopes=details.get("exceeded_scopes", []),
            available_parent_scopes=details.get("available_parent_scopes", []),
        )
    elif status_code == 403 and error_type == "invalid_tool_access":
        # Handle tool access errors
        details = error_data.get("details", {})
        
        raise ToolAccessError(
            message=error_message,
            http_status=status_code,
            error_code=error_type,
            error_data=error_data,
            request_id=request_id,
            exceeded_tools=details.get("exceeded_tools", []),
            available_parent_tools=details.get("available_parent_tools", []),
        )
    else:
        # Generic API error for all other cases
        raise APIError(
            message=error_message,
            http_status=status_code,
            error_code=error_type,
            error_data=error_data,
            request_id=request_id,
        )


def make_request(
    method: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: Optional[int] = None,
    stream: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """
    Make a request to the AgenticTrust API.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: API endpoint path
        params: Query parameters
        data: Form data
        headers: HTTP headers
        files: Files to upload
        json_data: JSON data for the request body
        timeout: Request timeout in seconds
        stream: Whether to stream the response
        
    Returns:
        API response as a dictionary
        
    Raises:
        APIConnectionError: If a network error occurs
    """
    # Prepare request URL and headers
    url = f"{default_config.api_base}{path}"
    
    # Use provided headers or initialize empty dict
    request_headers = headers or {}
    
    # Add common headers
    if "Content-Type" not in request_headers and json_data is not None:
        request_headers["Content-Type"] = "application/json"
    
    # Add trace ID for debugging
    request_headers["X-Request-ID"] = str(uuid.uuid4())
    
    # Add API key if available
    if default_config.api_key and "Authorization" not in request_headers:
        request_headers["Authorization"] = f"Bearer {default_config.api_key}"
    
    # Set timeout
    request_timeout = timeout or default_config.default_timeout
    
    # Build request kwargs
    request_kwargs = {
        "headers": request_headers,
        "params": params,
        "data": data,
        "files": files,
        "timeout": request_timeout,
        "stream": stream,
    }
    
    # Add JSON data if provided
    if json_data is not None:
        request_kwargs["json"] = json_data
    
    # Add proxies if configured
    if default_config.proxies:
        request_kwargs["proxies"] = default_config.proxies
    
    # Debug information
    if default_config.debug:
        debug_info = {
            "method": method,
            "url": url,
            "headers": {k: v if k != "Authorization" else "Bearer ..." for k, v in request_headers.items()},
            "params": params,
            "data": data,
            "json": json_data,
        }
        print(f"Request: {json.dumps(debug_info, indent=2, default=str)}")
    
    # Make the request
    try:
        # Create a client with the configured proxies if any
        client_kwargs = {}
        if default_config.proxies:
            client_kwargs['proxies'] = default_config.proxies
                
        # Save the stream flag but remove it from request_kwargs
        # as httpx.Client.request() doesn't accept it directly
        stream_enabled = request_kwargs.pop('stream', False)
        
        with httpx.Client(**client_kwargs) as client:
            # If streaming is needed, we'll need to implement that separately
            # For now, just make the request without the stream parameter
            response = client.request(method, url, **request_kwargs)
            
            # Debug response
            if default_config.debug:
                print(f"Response status: {response.status_code}")
                try:
                    print(f"Response body: {json.dumps(response.json(), indent=2)}")
                except ValueError:
                    print(f"Response body: {response.text[:200]}")
            
            # Handle error responses
            if response.status_code >= 400:
                handle_error_response(response)
            
            # Return JSON response if possible
            try:
                return response.json()
            except ValueError:
                # Return text response if not JSON
                return {"text": response.text}
                
    except httpx.RequestError as e:
        # Wrap network errors in APIConnectionError
        raise APIConnectionError(
            message=f"Network error: {str(e)}",
            error_data={"original_error": str(e)},
        ) from e
