"""
Client for tool management.
"""
from typing import Dict, List, Optional, Any, Union

from .api_resources.tools import ToolsResource
from .types.tool import ToolDict, ToolListResponse
from .utils.validators import validate_string, validate_string_list, validate_dict


class ToolClient:
    """
    Client for tool management.
    """
    
    def __init__(self, parent=None):
        """
        Initialize with parent client.
        
        Args:
            parent: Parent AgenticTrustClient instance
        """
        self.parent = parent
        self._api = ToolsResource(parent)
    
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
        return self._api.list(
            category=category,
            is_active=is_active,
            page=page,
            per_page=per_page,
        )
    
    def get(self, tool_id: str) -> ToolDict:
        """
        Get tool details by tool ID.
        
        Args:
            tool_id: The ID of the tool
            
        Returns:
            Dict containing tool details
        """
        return self._api.get(tool_id=tool_id)
    
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
        return self._api.create(
            name=name,
            description=description,
            category=category,
            permissions_required=permissions_required,
            parameters=parameters,
            input_schema=input_schema,
        )
    
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
        return self._api.update(
            tool_id=tool_id,
            name=name,
            description=description,
            category=category,
            permissions_required=permissions_required,
            parameters=parameters,
            input_schema=input_schema,
            is_active=is_active,
        )
    
    def delete(self, tool_id: str) -> Dict[str, Any]:
        """
        Delete a tool.
        
        Args:
            tool_id: The ID of the tool to delete
            
        Returns:
            Dict containing deletion status
        """
        return self._api.delete(tool_id=tool_id)
    
    def activate(self, tool_id: str) -> ToolDict:
        """
        Activate a tool.
        
        Args:
            tool_id: The ID of the tool to activate
            
        Returns:
            Dict containing updated tool details
        """
        return self._api.activate(tool_id=tool_id)
    
    def deactivate(self, tool_id: str) -> ToolDict:
        """
        Deactivate a tool.
        
        Args:
            tool_id: The ID of the tool to deactivate
            
        Returns:
            Dict containing updated tool details
        """
        return self._api.deactivate(tool_id=tool_id)
