"""
API resource for tool management.
"""
from typing import Dict, List, Optional, Any, Union

from .abstract import APIResource
from ..types.tool import ToolDict, ToolListResponse
from ..utils.validators import validate_string, validate_string_list, validate_dict


class ToolsResource(APIResource):
    """API resource for tool management."""
    
    def list(
        self,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> ToolListResponse:
        """
        List all registered tools, with optional filtering.
        
        Args:
            category: Optional category to filter by
            is_active: Optional active status to filter by
            page: Page number for pagination
            per_page: Number of items per page
            
        Returns:
            Dict containing list of tools
        """
        # Prepare query parameters
        params = {
            "page": page,
            "per_page": per_page,
        }
        
        if category:
            params["category"] = validate_string(category, "category")
            
        if is_active is not None:
            params["is_active"] = "true" if is_active else "false"
        
        # Make API request
        return self._request("GET", "/api/tools", params=params)
    
    def get(self, tool_id: str) -> ToolDict:
        """
        Get tool details by tool ID.
        
        Args:
            tool_id: The ID of the tool
            
        Returns:
            Dict containing tool details
        """
        # Validate input
        tool_id = validate_string(tool_id, "tool_id")
        
        # Make API request
        return self._request("GET", f"/api/tools/{tool_id}")
    
    def create(
        self,
        name: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        permissions_required: Optional[List[str]] = None,
        parameters: Optional[List[Dict[str, Any]]] = None,
        input_schema: Optional[Dict[str, Any]] = None,
    ) -> ToolDict:
        """
        Create a new tool.
        
        Args:
            name: Name of the tool
            description: Optional description of the tool
            category: Optional category for the tool
            permissions_required: List of permissions required to use this tool
            parameters: List of parameter definitions for this tool (legacy)
            input_schema: JSON Schema defining the input structure for this tool (preferred)
            
        Returns:
            Dict containing tool details
        """
        # Validate inputs
        name = validate_string(name, "name")
        description = validate_string(description, "description", required=False)
        category = validate_string(category, "category", required=False)
        permissions_required = validate_string_list(permissions_required, "permissions_required", required=False)
        
        # Validate parameters if provided
        if parameters is not None:
            if not isinstance(parameters, list):
                raise ValueError("parameters must be a list")
            
            for i, param in enumerate(parameters):
                if not isinstance(param, dict):
                    raise ValueError(f"parameters[{i}] must be a dictionary")
                
                # Ensure required fields are present
                if "name" not in param:
                    raise ValueError(f"parameters[{i}] must have a 'name' field")
                
                if "type" not in param:
                    raise ValueError(f"parameters[{i}] must have a 'type' field")
        
        # Validate input_schema if provided
        if input_schema is not None:
            if not isinstance(input_schema, dict):
                raise ValueError("input_schema must be a dictionary")
        
        # Prepare request data
        data = {
            "name": name,
        }
        
        if description:
            data["description"] = description
            
        if category:
            data["category"] = category
            
        if permissions_required:
            data["permissions_required"] = permissions_required
            
        if parameters:
            data["parameters"] = parameters
            
        if input_schema:
            data["inputSchema"] = input_schema
        
        # Make API request
        return self._request("POST", "/api/tools", json_data=data)
    
    def update(
        self,
        tool_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        permissions_required: Optional[List[str]] = None,
        parameters: Optional[List[Dict[str, Any]]] = None,
        input_schema: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None,
    ) -> ToolDict:
        """
        Update an existing tool.
        
        Args:
            tool_id: The ID of the tool to update
            name: Optional new name for the tool
            description: Optional new description for the tool
            category: Optional new category for the tool
            permissions_required: Optional new list of permissions required
            parameters: Optional new list of parameter definitions (legacy)
            input_schema: Optional new JSON Schema for input structure
            is_active: Optional new active status
            
        Returns:
            Dict containing updated tool details
        """
        # Validate inputs
        tool_id = validate_string(tool_id, "tool_id")
        
        # Prepare request data (only include non-None values)
        data = {}
        
        if name is not None:
            data["name"] = validate_string(name, "name")
            
        if description is not None:
            data["description"] = validate_string(description, "description", required=False)
            
        if category is not None:
            data["category"] = validate_string(category, "category", required=False)
            
        if permissions_required is not None:
            data["permissions_required"] = validate_string_list(permissions_required, "permissions_required", required=False)
            
        if parameters is not None:
            if not isinstance(parameters, list):
                raise ValueError("parameters must be a list")
            
            for i, param in enumerate(parameters):
                if not isinstance(param, dict):
                    raise ValueError(f"parameters[{i}] must be a dictionary")
                
                # Ensure required fields are present
                if "name" not in param:
                    raise ValueError(f"parameters[{i}] must have a 'name' field")
                
                if "type" not in param:
                    raise ValueError(f"parameters[{i}] must have a 'type' field")
                    
            data["parameters"] = parameters
            
        if input_schema is not None:
            if not isinstance(input_schema, dict):
                raise ValueError("input_schema must be a dictionary")
                
            data["inputSchema"] = input_schema
            
        if is_active is not None:
            data["is_active"] = is_active
        
        # Make API request
        return self._request("PUT", f"/api/tools/{tool_id}", json_data=data)
    
    def delete(self, tool_id: str) -> Dict[str, Any]:
        """
        Delete a tool.
        
        Args:
            tool_id: The ID of the tool to delete
            
        Returns:
            Dict containing deletion status
        """
        # Validate input
        tool_id = validate_string(tool_id, "tool_id")
        
        # Make API request
        return self._request("DELETE", f"/api/tools/{tool_id}")
    
    def activate(self, tool_id: str) -> ToolDict:
        """
        Activate a tool.
        
        Args:
            tool_id: The ID of the tool to activate
            
        Returns:
            Dict containing updated tool details
        """
        # Validate input
        tool_id = validate_string(tool_id, "tool_id")
        
        # Make API request
        return self._request("POST", f"/api/tools/{tool_id}/activate")
    
    def deactivate(self, tool_id: str) -> ToolDict:
        """
        Deactivate a tool.
        
        Args:
            tool_id: The ID of the tool to deactivate
            
        Returns:
            Dict containing updated tool details
        """
        # Validate input
        tool_id = validate_string(tool_id, "tool_id")
        
        # Make API request
        return self._request("POST", f"/api/tools/{tool_id}/deactivate")
