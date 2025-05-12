import uuid
import secrets
import traceback
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Table, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from werkzeug.security import generate_password_hash
from agentictrust.db import Base, db_session
from agentictrust.utils.logger import logger

# Association table for agent-tool many-to-many relationship
agent_tools = Table('agent_tools', Base.metadata,
    Column('agent_id', String(36), ForeignKey('agents.client_id'), primary_key=True),
    Column('tool_id', String(36), ForeignKey('tools.tool_id'), primary_key=True)
)

class Agent(Base):
    """Model for Agent registration in the OAuth system."""
    __tablename__ = 'agents'
    
    client_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_secret_hash = Column(String(256), nullable=False)
    agent_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    max_scope_level = Column(String(20), default='restricted')
    registration_token = Column(String(64), unique=True, nullable=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime, nullable=True)
    
    # OIDC-A identity metadata
    agent_type = Column(String(50), nullable=True)
    agent_model = Column(String(100), nullable=True)
    agent_version = Column(String(50), nullable=True)
    agent_provider = Column(String(100), nullable=True)
    
    # Relationships
    tokens = relationship('IssuedToken', backref='agent', lazy=True, cascade='all, delete-orphan')
    tools = relationship('Tool', secondary=agent_tools, lazy='subquery', backref='agents')
    
    @classmethod
    def create(cls, agent_name, description=None, max_scope_level='restricted', agent_type=None, agent_model=None, agent_version=None, agent_provider=None):
        """Create a new agent with generated client credentials."""
        if not agent_name:
            logger.error("Cannot create agent: agent_name is required")
            raise ValueError("agent_name is required")
            
        # Generate secure credentials
        try:
            client_secret = secrets.token_urlsafe(32)
            client_secret_hash = generate_password_hash(client_secret)
            registration_token = secrets.token_urlsafe(48)
        except Exception as e:
            logger.error(f"Failed to generate secure credentials: {str(e)}")
            raise RuntimeError(f"Failed to generate secure credentials: {str(e)}") from e
        
        # Create agent instance
        agent = cls(
            agent_name=agent_name,
            description=description,
            max_scope_level=max_scope_level,
            client_secret_hash=client_secret_hash,
            registration_token=registration_token,
            agent_type=agent_type,
            agent_model=agent_model,
            agent_version=agent_version,
            agent_provider=agent_provider
        )
        
        # Add to database
        try:
            db_session.add(agent)
            db_session.commit()
            logger.info(f"Agent '{agent_name}' created successfully with ID: {agent.client_id}")
        except IntegrityError as e:
            db_session.rollback()
            logger.error(f"Database integrity error creating agent '{agent_name}': {str(e)}")
            if 'unique constraint' in str(e).lower():
                raise ValueError(f"An agent with name '{agent_name}' already exists") from e
            raise ValueError(f"Could not create agent due to database constraint: {str(e)}") from e
        except SQLAlchemyError as e:
            db_session.rollback()
            err_msg = f"Database error creating agent '{agent_name}': {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        except Exception as e:
            db_session.rollback()
            err_msg = f"Unexpected error creating agent '{agent_name}': {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        
        # Return both the agent and the plain text client secret (only known once)
        return agent, client_secret
    
    def activate(self):
        """Activate the agent after registration confirmation."""
        if self.is_active:
            logger.warning(f"Attempted to activate already active agent: {self.client_id}")
            return
            
        self.is_active = True
        self.registration_token = None
        
        try:
            db_session.commit()
            logger.info(f"Agent activated successfully: {self.client_id} - {self.agent_name}")
        except SQLAlchemyError as e:
            db_session.rollback()
            err_msg = f"Database error activating agent {self.client_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        except Exception as e:
            db_session.rollback()
            err_msg = f"Unexpected error activating agent {self.client_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
    
    def add_tool(self, tool):
        """Add a tool to this agent's allowed tools."""
        if not tool:
            logger.error(f"Cannot add tool to agent {self.client_id}: tool is None")
            raise ValueError("Tool cannot be None")
            
        if tool not in self.tools:
            try:
                self.tools.append(tool)
                db_session.commit()
                logger.info(f"Tool {tool.tool_id} ({tool.name}) added to agent {self.client_id}")
            except SQLAlchemyError as e:
                db_session.rollback()
                err_msg = f"Database error adding tool {tool.tool_id} to agent {self.client_id}: {str(e)}"
                logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
                raise RuntimeError(err_msg) from e
            except Exception as e:
                db_session.rollback()
                err_msg = f"Unexpected error adding tool to agent {self.client_id}: {str(e)}"
                logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
                raise RuntimeError(err_msg) from e
        else:
            logger.info(f"Tool {tool.tool_id} already associated with agent {self.client_id} - no action taken")
    
    def remove_tool(self, tool):
        """Remove a tool from this agent's allowed tools."""
        if not tool:
            logger.error(f"Cannot remove tool from agent {self.client_id}: tool is None")
            raise ValueError("Tool cannot be None")
            
        if tool in self.tools:
            try:
                self.tools.remove(tool)
                db_session.commit()
                logger.info(f"Tool {tool.tool_id} ({tool.name}) removed from agent {self.client_id}")
            except SQLAlchemyError as e:
                db_session.rollback()
                err_msg = f"Database error removing tool {tool.tool_id} from agent {self.client_id}: {str(e)}"
                logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
                raise RuntimeError(err_msg) from e
            except Exception as e:
                db_session.rollback()
                err_msg = f"Unexpected error removing tool from agent {self.client_id}: {str(e)}"
                logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
                raise RuntimeError(err_msg) from e
        else:
            logger.info(f"Tool {tool.tool_id} not associated with agent {self.client_id} - no action taken")
        
    def to_dict(self):
        """Convert agent to dictionary representation."""
        return {
            'agent_type': self.agent_type,
            'agent_model': self.agent_model,
            'agent_version': self.agent_version,
            'agent_provider': self.agent_provider,
            'client_id': self.client_id,
            'agent_name': self.agent_name,
            'description': self.description,
            'max_scope_level': self.max_scope_level,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tools': [tool.to_dict() for tool in self.tools]
        }
        
    @classmethod
    def get_by_id(cls, client_id):
        """Get agent by client_id."""
        if not client_id:
            logger.error("Cannot get agent: client_id is None or empty")
            raise ValueError("client_id is required")
            
        try:
            agent = cls.query.get(client_id)
            if not agent:
                logger.warning(f"Agent not found with ID: {client_id}")
                raise ValueError(f"Agent not found with ID: {client_id}")
            logger.debug(f"Retrieved agent: {client_id} - {agent.agent_name}")
            return agent
        except SQLAlchemyError as e:
            err_msg = f"Database error retrieving agent with ID {client_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        
    @classmethod
    def list_all(cls):
        """List all agents."""
        try:
            agents = cls.query.all()
            logger.debug(f"Retrieved {len(agents)} agents")
            return agents
        except SQLAlchemyError as e:
            err_msg = f"Database error retrieving all agents: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        
    @classmethod
    def delete_by_id(cls, client_id):
        """Delete an agent by client_id."""
        if not client_id:
            logger.error("Cannot delete agent: client_id is None or empty")
            raise ValueError("client_id is required")
            
        try:
            agent = cls.query.get(client_id)
            if not agent:
                logger.warning(f"Cannot delete agent: not found with ID {client_id}")
                raise ValueError(f"Agent not found with ID: {client_id}")
                
            agent_name = agent.agent_name  # Store for logging after deletion
            db_session.delete(agent)
            db_session.commit()
            logger.info(f"Agent deleted successfully: {client_id} - {agent_name}")
        except IntegrityError as e:
            db_session.rollback()
            err_msg = f"Cannot delete agent {client_id} due to integrity constraints: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise ValueError(f"Cannot delete agent due to existing relationships: {str(e)}") from e
        except SQLAlchemyError as e:
            db_session.rollback()
            err_msg = f"Database error deleting agent {client_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        except Exception as e:
            db_session.rollback()
            err_msg = f"Unexpected error deleting agent {client_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
            
    @classmethod
    def find_by_registration_token(cls, registration_token):
        """Find agent by registration token."""
        if not registration_token:
            logger.error("Cannot find agent: registration_token is None or empty")
            raise ValueError("registration_token is required")
            
        try:
            agent = cls.query.filter_by(registration_token=registration_token).first()
            if not agent:
                logger.warning(f"No agent found with registration token: {registration_token[:10]}...")
                raise ValueError(f"No agent found with the provided registration token")
            logger.debug(f"Retrieved agent by registration token: {agent.client_id} - {agent.agent_name}")
            return agent
        except SQLAlchemyError as e:
            err_msg = f"Database error finding agent by registration token: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        
    def update_properties(self, data):
        """Update agent properties."""
        if not data:
            logger.error(f"Cannot update agent {self.client_id}: no data provided")
            raise ValueError("Update data is required")
            
        properties_updated = []
        
        if 'agent_name' in data:
            old_name = self.agent_name
            self.agent_name = data['agent_name']
            properties_updated.append(f"agent_name: '{old_name}' -> '{data['agent_name']}'")
            
        if 'description' in data:
            self.description = data['description']
            properties_updated.append("description")
            
        if 'max_scope_level' in data:
            old_level = self.max_scope_level
            self.max_scope_level = data['max_scope_level']
            properties_updated.append(f"max_scope_level: '{old_level}' -> '{data['max_scope_level']}'")
            
        if not properties_updated:
            logger.warning(f"No properties updated for agent {self.client_id} - data contained no valid fields")
            return self
            
        try:
            db_session.commit()
            logger.info(f"Updated agent {self.client_id} properties: {', '.join(properties_updated)}")
        except IntegrityError as e:
            db_session.rollback()
            err_msg = f"Database integrity error updating agent {self.client_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            if 'unique constraint' in str(e).lower() and 'agent_name' in data:
                raise ValueError(f"An agent with name '{data['agent_name']}' already exists") from e
            raise ValueError(f"Could not update agent due to database constraint: {str(e)}") from e
        except SQLAlchemyError as e:
            db_session.rollback()
            err_msg = f"Database error updating agent {self.client_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        except Exception as e:
            db_session.rollback()
            err_msg = f"Unexpected error updating agent {self.client_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
            
        return self