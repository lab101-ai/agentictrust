import uuid
from datetime import datetime
from app import db

class Tool(db.Model):
    """Model for registered tools that agents can use."""
    __tablename__ = 'tools'
    
    tool_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    permissions_required = db.Column(db.JSON, nullable=False, default=list)
    parameters = db.Column(db.JSON, nullable=False, default=list)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def create(cls, name, description=None, category=None, permissions_required=None, parameters=None):
        """Create a new tool."""
        tool = cls(
            name=name,
            description=description,
            category=category,
            permissions_required=permissions_required or [],
            parameters=parameters or []
        )
        
        db.session.add(tool)
        db.session.commit()
        return tool
    
    def update(self, **kwargs):
        """Update tool attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        db.session.commit()
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