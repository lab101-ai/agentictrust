"""
Shared abstractions and utilities for tool management reused by routers and services
"""
from typing import Any, Dict, List, Optional
from app.db.models import Tool, Scope
import logging

logger = logging.getLogger(__name__)


class ToolEngine:
    """Core engine for managing tool lifecycle."""
    def __init__(self):
        # No internal state needed for now
        pass

    def create_tool_record(self, name: str, description: str, category: str,
                           permissions_required: List[str], parameters: List[Dict[str, Any]]) -> Tool:
        """Create a new tool in the database or return existing"""
        # Check if tool with the same name already exists
        existing = Tool.find_by_name(name)
        if existing:
            return existing
            
        # Process scope names/ids into scope_ids
        scope_ids: List[str] = []
        missing_scopes: List[str] = []
        
        for scope_name in permissions_required:
            # If it looks like a UUID, assume it's a scope_id
            if len(scope_name) == 36 and "-" in scope_name:
                scope_ids.append(scope_name)
                continue
                
            # Otherwise, look up the scope by name
            scope = Scope.find_by_name(scope_name)
            if scope:
                scope_ids.append(scope.scope_id)
                logger.debug(f"Found scope {scope_name} with ID {scope.scope_id}")
            else:
                missing_scopes.append(scope_name)
                
        # Report any missing scopes
        if missing_scopes:
            raise ValueError(f"The following scopes are not defined: {', '.join(missing_scopes)}. Please create these scopes first.")
            
        # Create the tool using the Tool.create class method
        tool = Tool.create(
            name=name, 
            description=description,
            category=category,
            permissions_required=scope_ids,
            parameters=parameters
        )
        
        return tool

    def list_tools(self, category: Optional[str] = None, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """List tools with optional filters"""
        # Get all tools first
        all_tools = Tool.list_all()
        
        # Apply filters in memory
        filtered_tools = all_tools
        if category:
            filtered_tools = [t for t in filtered_tools if t.category == category]
        if is_active is not None:
            filtered_tools = [t for t in filtered_tools if t.is_active == is_active]
            
        return [t.to_dict() for t in filtered_tools]

    def get_tool(self, tool_id: str) -> Dict[str, Any]:
        """Get a tool by ID with schema alias."""
        if not tool_id:
            raise ValueError("tool_id is required")
        tool = Tool.get_by_id(tool_id)
        tool_dict = tool.to_dict()
        tool_dict["inputSchema"] = tool_dict.pop("parameters", [])
        return tool_dict

    def update_tool(self, tool_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a tool by ID, alias schema."""
        if not data:
            raise ValueError("No update data provided")
            
        tool = Tool.get_by_id(tool_id)
        
        # Handle schema aliasing
        if "inputSchema" in data:
            data["parameters"] = data.pop("inputSchema")
            
        # Check for name uniqueness if name is being changed
        if "name" in data and data["name"] != tool.name:
            # Check if another tool exists with the same name
            if Tool.find_by_name(data["name"]):
                raise ValueError("Tool with this name already exists")
                
        # Do the update
        updated = tool.update(**data)
        
        # Format the response
        tool_dict = updated.to_dict()
        tool_dict["inputSchema"] = tool_dict.pop("parameters", [])
        return tool_dict

    def delete_tool(self, tool_id: str) -> None:
        """Delete a tool by ID."""
        tool = Tool.get_by_id(tool_id)
        if getattr(tool, "agents", None) and len(tool.agents) > 0:
            raise ValueError(f"Tool is associated with {len(tool.agents)} agents")
        Tool.delete_by_id(tool_id)

    def activate_tool(self, tool_id: str) -> Dict[str, Any]:
        """Activate a tool by ID."""
        tool = Tool.get_by_id(tool_id)
        updated = tool.update(is_active=True)
        tool_dict = updated.to_dict()
        tool_dict["inputSchema"] = tool_dict.pop("parameters", [])
        return tool_dict

    def deactivate_tool(self, tool_id: str) -> Dict[str, Any]:
        """Deactivate a tool by ID."""
        tool = Tool.get_by_id(tool_id)
        updated = tool.update(is_active=False)
        tool_dict = updated.to_dict()
        tool_dict["inputSchema"] = tool_dict.pop("parameters", [])
        return tool_dict
