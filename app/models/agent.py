import uuid
import secrets
from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

# Association table for agent-tool many-to-many relationship
agent_tools = db.Table('agent_tools',
    db.Column('agent_id', db.String(36), db.ForeignKey('agents.client_id'), primary_key=True),
    db.Column('tool_id', db.String(36), db.ForeignKey('tools.tool_id'), primary_key=True)
)

class Agent(db.Model):
    """Model for Agent registration in the OAuth system."""
    __tablename__ = 'agents'
    
    client_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_secret_hash = db.Column(db.String(256), nullable=False)
    agent_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    allowed_resources = db.Column(db.JSON, nullable=False, default=list)
    max_scope_level = db.Column(db.String(20), default='restricted')
    registration_token = db.Column(db.String(64), unique=True, nullable=True)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tokens = db.relationship('IssuedToken', backref='agent', lazy=True, cascade='all, delete-orphan')
    # Relationship with tools
    tools = db.relationship('Tool', secondary=agent_tools, lazy='subquery',
                           backref=db.backref('agents', lazy=True))
    
    @classmethod
    def create(cls, agent_name, description=None, allowed_resources=None, max_scope_level='restricted'):
        """Create a new agent with generated client credentials."""
        client_secret = secrets.token_urlsafe(32)
        client_secret_hash = generate_password_hash(client_secret)
        registration_token = secrets.token_urlsafe(48)
        
        agent = cls(
            agent_name=agent_name,
            description=description,
            allowed_resources=allowed_resources or [],
            max_scope_level=max_scope_level,
            client_secret_hash=client_secret_hash,
            registration_token=registration_token
        )
        
        db.session.add(agent)
        db.session.commit()
        
        # Return both the agent and the plain text client secret (only known once)
        return agent, client_secret
    
    def verify_client_secret(self, client_secret):
        """Verify the provided client secret against the stored hash."""
        return check_password_hash(self.client_secret_hash, client_secret)
    
    def activate(self):
        """Activate the agent after registration confirmation."""
        self.is_active = True
        self.registration_token = None
        db.session.commit()
    
    def add_tool(self, tool):
        """Add a tool to this agent's allowed tools."""
        if tool not in self.tools:
            self.tools.append(tool)
            db.session.commit()
    
    def remove_tool(self, tool):
        """Remove a tool from this agent's allowed tools."""
        if tool in self.tools:
            self.tools.remove(tool)
            db.session.commit()
        
    def to_dict(self):
        """Convert agent to dictionary representation."""
        return {
            'client_id': self.client_id,
            'agent_name': self.agent_name,
            'description': self.description,
            'allowed_resources': self.allowed_resources,
            'max_scope_level': self.max_scope_level,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tools': [tool.to_dict() for tool in self.tools]
        } 