"""
Abstract base class for API resources.
"""
from typing import Dict, Any, Optional, List, Union, Callable

from ..utils.http import make_request


class APIResource:
    """Base class for API resources."""
    
    def __init__(self, parent=None):
        """
        Initialize the API resource.
        
        Args:
            parent: Parent client instance
        """
        self.parent = parent
        
    def _get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """
        Get request headers with authentication if token is provided.
        
        Args:
            token: Optional access token for authentication
            
        Returns:
            Dict containing HTTP headers
        """
        headers = {}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        return headers
    
    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Make a request to the API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            params: Query parameters
            data: Form data
            json_data: JSON data for the request body
            headers: HTTP headers
            files: Files to upload
            timeout: Request timeout in seconds
            stream: Whether to stream the response
            
        Returns:
            API response as a dictionary
        """
        return make_request(
            method=method,
            path=path,
            params=params,
            data=data,
            json_data=json_data,
            headers=headers,
            files=files,
            timeout=timeout,
            stream=stream,
        )
