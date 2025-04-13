import uuid
from datetime import datetime
from app import db

class Scope(db.Model):
    """Model for OAuth scopes that can be assigned to tokens."""
    __tablename__ = 'scopes'
    
    scope_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)  # Read, Write, Admin, Tool
    is_sensitive = db.Column(db.Boolean, default=False)
    requires_approval = db.Column(db.Boolean, default=False)
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def create(cls, name, description=None, category="read", is_sensitive=False, 
               requires_approval=False, is_default=False):
        """Create a new OAuth scope."""
        scope = cls(
            name=name,
            description=description,
            category=category,
            is_sensitive=is_sensitive,
            requires_approval=requires_approval,
            is_default=is_default
        )
        
        db.session.add(scope)
        db.session.commit()
        return scope
    
    def update(self, **kwargs):
        """Update scope attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return self
    
    def to_dict(self):
        """Convert scope to dictionary representation."""
        return {
            'scope_id': self.scope_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'is_sensitive': self.is_sensitive,
            'requires_approval': self.requires_approval,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Association table for agent-scope many-to-many relationship
agent_default_scopes = db.Table('agent_default_scopes',
    db.Column('agent_id', db.String(36), db.ForeignKey('agents.client_id'), primary_key=True),
    db.Column('scope_id', db.String(36), db.ForeignKey('scopes.scope_id'), primary_key=True)
)

# Association table for tool-scope many-to-many relationship
tool_required_scopes = db.Table('tool_required_scopes',
    db.Column('tool_id', db.String(36), db.ForeignKey('tools.tool_id'), primary_key=True),
    db.Column('scope_id', db.String(36), db.ForeignKey('scopes.scope_id'), primary_key=True)
)
