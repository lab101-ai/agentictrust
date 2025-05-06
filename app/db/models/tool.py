import uuid
import json
import logging
import traceback
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.db import Base, db_session

logger = logging.getLogger(__name__)

class Tool(Base):
    """Model for registered tools that agents can use."""
    __tablename__ = 'tools'
    
    tool_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    permissions_required = Column(JSON, nullable=False, default=list)
    parameters = Column(JSON, nullable=False, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def create(cls, name, description=None, category=None, permissions_required=None, parameters=None):
        """Create a new tool."""
        if not name:
            logger.error("Cannot create tool: name is required")
            raise ValueError("Tool name is required")
            
        # Validate permissions_required is JSON serializable
        perm_list = permissions_required or []
        param_list = parameters or []
        
        try:
            # Ensure these are serializable
            json.dumps(perm_list)
            json.dumps(param_list)
        except (TypeError, ValueError) as e:
            logger.error(f"Invalid JSON format in tool creation: {str(e)}")
            raise ValueError(f"Invalid format for permissions or parameters: {str(e)}") from e
            
        # Create the tool instance
        tool = cls(
            name=name,
            description=description,
            category=category,
            permissions_required=perm_list,
            parameters=param_list
        )
        
        # Add to database
        try:
            db_session.add(tool)
            db_session.commit()
            logger.info(f"Tool '{name}' created successfully with ID: {tool.tool_id}")
        except IntegrityError as e:
            db_session.rollback()
            logger.error(f"Database integrity error creating tool '{name}': {str(e)}")
            if 'unique constraint' in str(e).lower():
                raise ValueError(f"A tool with name '{name}' already exists") from e
            raise ValueError(f"Could not create tool due to database constraint: {str(e)}") from e
        except SQLAlchemyError as e:
            db_session.rollback()
            err_msg = f"Database error creating tool '{name}': {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        except Exception as e:
            db_session.rollback()
            err_msg = f"Unexpected error creating tool '{name}': {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
            
        return tool
    
    def update(self, **kwargs):
        """Update tool attributes."""
        if not kwargs:
            logger.warning(f"No update data provided for tool {self.tool_id} ({self.name})")
            return self
            
        properties_updated = []
        
        # Validate JSON fields if present
        if 'permissions_required' in kwargs:
            try:
                json.dumps(kwargs['permissions_required'])
            except (TypeError, ValueError) as e:
                logger.error(f"Invalid JSON format for permissions_required: {str(e)}")
                raise ValueError(f"Invalid format for permissions_required: {str(e)}") from e
                
        if 'parameters' in kwargs:
            try:
                json.dumps(kwargs['parameters'])
            except (TypeError, ValueError) as e:
                logger.error(f"Invalid JSON format for parameters: {str(e)}")
                raise ValueError(f"Invalid format for parameters: {str(e)}") from e
        
        # Update attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                old_value = getattr(self, key)
                if key in ('parameters', 'permissions_required'):
                    # For JSON fields, log length change rather than content
                    old_len = len(old_value) if old_value else 0
                    new_len = len(value) if value else 0
                    setattr(self, key, value)
                    properties_updated.append(f"{key}: {old_len} items -> {new_len} items")
                elif key == 'name':
                    setattr(self, key, value)
                    properties_updated.append(f"{key}: '{old_value}' -> '{value}'")
                else:
                    setattr(self, key, value)
                    properties_updated.append(key)
        
        if not properties_updated:
            logger.warning(f"No valid properties to update for tool {self.tool_id}")
            return self
            
        try:
            db_session.commit()
            logger.info(f"Updated tool {self.tool_id} ({self.name}) properties: {', '.join(properties_updated)}")
        except IntegrityError as e:
            db_session.rollback()
            logger.error(f"Database integrity error updating tool {self.tool_id}: {str(e)}")
            if 'unique constraint' in str(e).lower() and 'name' in kwargs:
                raise ValueError(f"A tool with name '{kwargs['name']}' already exists") from e
            raise ValueError(f"Could not update tool due to database constraint: {str(e)}") from e
        except SQLAlchemyError as e:
            db_session.rollback()
            err_msg = f"Database error updating tool {self.tool_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        except Exception as e:
            db_session.rollback()
            err_msg = f"Unexpected error updating tool {self.tool_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
            
        return self
    
    def to_dict(self):
        """Convert tool to dictionary representation."""
        return {
            'tool_id': self.tool_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'permissions_required': self.permissions_required,
            'parameters': self.parameters,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
    @classmethod
    def get_by_id(cls, tool_id):
        """Get tool by ID."""
        if not tool_id:
            logger.error("Cannot get tool: tool_id is None or empty")
            raise ValueError("tool_id is required")
            
        try:
            tool = cls.query.get(tool_id)
            if not tool:
                logger.warning(f"Tool not found with ID: {tool_id}")
                raise ValueError(f"Tool not found with ID: {tool_id}")
            logger.debug(f"Retrieved tool: {tool_id} - {tool.name}")
            return tool
        except SQLAlchemyError as e:
            err_msg = f"Database error retrieving tool with ID {tool_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        
    @classmethod
    def list_all(cls):
        """List all tools."""
        try:
            tools = cls.query.all()
            logger.debug(f"Retrieved {len(tools)} tools")
            return tools
        except SQLAlchemyError as e:
            err_msg = f"Database error retrieving all tools: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        
    @classmethod
    def delete_by_id(cls, tool_id):
        """Delete a tool by ID."""
        if not tool_id:
            logger.error("Cannot delete tool: tool_id is None or empty")
            raise ValueError("tool_id is required")
            
        try:
            tool = cls.query.get(tool_id)
            if not tool:
                logger.warning(f"Cannot delete tool: not found with ID {tool_id}")
                raise ValueError(f"Tool not found with ID: {tool_id}")
                
            # Check if the tool is associated with any agents before deletion
            if getattr(tool, "agents", None) and len(tool.agents) > 0:
                msg = f"Cannot delete tool {tool_id} ({tool.name}) as it is associated with {len(tool.agents)} agents"
                logger.warning(msg)
                raise ValueError(msg)
                
            tool_name = tool.name  # Store for logging after deletion
            db_session.delete(tool)
            db_session.commit()
            logger.info(f"Tool deleted successfully: {tool_id} - {tool_name}")
        except IntegrityError as e:
            db_session.rollback()
            err_msg = f"Cannot delete tool {tool_id} due to integrity constraints: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise ValueError(f"Cannot delete tool due to existing relationships: {str(e)}") from e
        except SQLAlchemyError as e:
            db_session.rollback()
            err_msg = f"Database error deleting tool {tool_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        except Exception as e:
            db_session.rollback()
            err_msg = f"Unexpected error deleting tool {tool_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
            
    @classmethod
    def find_by_name(cls, name):
        """Find a tool by name."""
        if not name:
            logger.warning("Cannot find tool: name is None or empty")
            return None
            
        try:
            tool = cls.query.filter_by(name=name).first()
            if tool:
                logger.debug(f"Found tool by name: {name} (ID: {tool.tool_id})")
            else:
                logger.debug(f"No tool found with name: {name}")
            return tool
        except SQLAlchemyError as e:
            err_msg = f"Database error finding tool by name '{name}': {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e