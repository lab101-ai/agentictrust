"""End-to-end tests for tool management."""
import pytest
from agentictrust.db.models import Tool

def test_create_tool(test_db, tool_engine, sample_scope):
    """Test creating a new tool."""
    # Create a new tool
    tool = tool_engine.create_tool_record(
        name="new_test_tool",
        description="A tool created in test",
        category="test",
        permissions_required=[sample_scope.scope_id],
        parameters=[
            {"name": "param1", "type": "string", "required": True},
            {"name": "param2", "type": "integer", "required": False}
        ]
    )
    
    # Verify tool attributes
    assert tool.name == "new_test_tool"
    assert tool.description == "A tool created in test"
    assert tool.category == "test"
    assert sample_scope.scope_id in tool.permissions_required
    assert len(tool.parameters) == 2
    assert tool.is_active is True
    
    # Verify tool exists in database
    db_tool = Tool.get_by_id(tool.tool_id)
    assert db_tool is not None
    assert db_tool.name == "new_test_tool"
    
    # Clean up
    Tool.delete_by_id(tool.tool_id)

def test_get_tool(test_db, sample_tool, tool_engine):
    """Test getting a tool by ID."""
    # Get the tool
    tool_data = tool_engine.get_tool(sample_tool.tool_id)
    
    # Verify tool data - note the schema alias from parameters to inputSchema
    assert tool_data["tool_id"] == sample_tool.tool_id
    assert tool_data["name"] == sample_tool.name
    assert "inputSchema" in tool_data
    assert len(tool_data["inputSchema"]) == len(sample_tool.parameters)

def test_list_tools(test_db, sample_tool, tool_engine):
    """Test listing all tools."""
    # Get all tools
    tools = tool_engine.list_tools()
    
    # Verify sample tool is in the list
    tool_ids = [tool["tool_id"] for tool in tools]
    assert sample_tool.tool_id in tool_ids
    
    # Test filtering by category
    category_tools = tool_engine.list_tools(category=sample_tool.category)
    assert len(category_tools) > 0
    assert all(tool["category"] == sample_tool.category for tool in category_tools)
    
    # Test filtering by active status
    active_tools = tool_engine.list_tools(is_active=True)
    assert sample_tool.tool_id in [tool["tool_id"] for tool in active_tools]

def test_update_tool(test_db, sample_tool, tool_engine):
    """Test updating a tool."""
    # Update the tool
    updated_data = tool_engine.update_tool(
        sample_tool.tool_id,
        {
            "name": "updated_tool_name",
            "description": "Updated description",
            "category": "updated_category",
            "inputSchema": [
                {"name": "new_param", "type": "string", "required": True}
            ]
        }
    )
    
    # Verify update was successful
    assert updated_data["name"] == "updated_tool_name"
    assert updated_data["description"] == "Updated description"
    assert updated_data["category"] == "updated_category"
    assert len(updated_data["inputSchema"]) == 1
    assert updated_data["inputSchema"][0]["name"] == "new_param"
    
    # Verify database was updated
    tool = Tool.get_by_id(sample_tool.tool_id)
    assert tool.name == "updated_tool_name"
    assert tool.description == "Updated description"
    assert tool.category == "updated_category"
    assert len(tool.parameters) == 1
    assert tool.parameters[0]["name"] == "new_param"

def test_activate_deactivate_tool(test_db, tool_engine, sample_scope):
    """Test activating and deactivating a tool."""
    # Create a tool
    tool = tool_engine.create_tool_record(
        name="activation_test_tool",
        description="Testing activation/deactivation",
        category="test",
        permissions_required=[sample_scope.scope_id],
        parameters=[]
    )
    
    # Deactivate the tool
    deactivated = tool_engine.deactivate_tool(tool.tool_id)
    assert deactivated["is_active"] is False
    
    # Verify tool is deactivated in database
    db_tool = Tool.get_by_id(tool.tool_id)
    assert db_tool.is_active is False
    
    # Activate the tool
    activated = tool_engine.activate_tool(tool.tool_id)
    assert activated["is_active"] is True
    
    # Verify tool is activated in database
    db_tool = Tool.get_by_id(tool.tool_id)
    assert db_tool.is_active is True
    
    # Clean up
    Tool.delete_by_id(tool.tool_id)

def test_delete_tool(test_db, tool_engine, sample_scope):
    """Test deleting a tool."""
    # Create a tool to delete
    tool = tool_engine.create_tool_record(
        name="delete_test_tool",
        description="Tool to delete",
        category="test",
        permissions_required=[sample_scope.scope_id],
        parameters=[]
    )
    
    # Verify tool exists
    db_tool = Tool.get_by_id(tool.tool_id)
    assert db_tool is not None
    
    # Delete the tool
    tool_engine.delete_tool(tool.tool_id)
    
    # Verify tool no longer exists
    with pytest.raises(ValueError, match="Tool not found"):
        Tool.get_by_id(tool.tool_id)
