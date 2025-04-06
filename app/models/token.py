import uuid
import secrets
from datetime import datetime, timedelta
from app import db
from werkzeug.security import generate_password_hash

class IssuedToken(db.Model):
    """Model for issued OAuth tokens."""
    __tablename__ = 'issued_tokens'
    
    token_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('agents.client_id'), nullable=False)
    
    # Token values (hashed for security)
    access_token_hash = db.Column(db.String(256), nullable=False)
    refresh_token_hash = db.Column(db.String(256), nullable=True)
    
    # Token metadata
    scope = db.Column(db.JSON, nullable=False)
    granted_tools = db.Column(db.JSON, nullable=False)
    granted_resources = db.Column(db.JSON, nullable=False)
    task_id = db.Column(db.String(36), nullable=False)
    parent_task_id = db.Column(db.String(36), nullable=True)
    parent_token_id = db.Column(db.String(36), db.ForeignKey('issued_tokens.token_id'), nullable=True)
    task_description = db.Column(db.Text, nullable=True)
    scope_inheritance_type = db.Column(db.String(20), default='restricted')
    
    # Token lifecycle
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_revoked = db.Column(db.Boolean, default=False)
    revoked_at = db.Column(db.DateTime, nullable=True)
    revocation_reason = db.Column(db.String(100), nullable=True)
    
    # Self-referential relationship for parent-child tokens
    child_tokens = db.relationship(
        'IssuedToken', 
        backref=db.backref('parent_token', remote_side=[token_id]),
        lazy=True,
        cascade='all, delete-orphan'
    )
    
    # Relationship with audit logs
    audit_logs = db.relationship('TaskAuditLog', backref='token', lazy=True, cascade='all, delete-orphan')
    
    @classmethod
    def create(cls, client_id, scope, granted_tools, granted_resources, task_id, 
              task_description=None, parent_task_id=None, parent_token_id=None,
              scope_inheritance_type='restricted', expires_in=None):
        """Create a new token with generated access and refresh tokens."""
        
        # Generate tokens
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(48)
        
        # Hash tokens for storage
        access_token_hash = generate_password_hash(access_token)
        refresh_token_hash = generate_password_hash(refresh_token)
        
        # Set expiry time (default from config if not specified)
        if not expires_in:
            from flask import current_app
            expires_in = current_app.config.get('ACCESS_TOKEN_EXPIRY', timedelta(hours=1))
            
        expires_at = datetime.utcnow() + expires_in
        
        # Create token record
        token = cls(
            client_id=client_id,
            access_token_hash=access_token_hash,
            refresh_token_hash=refresh_token_hash,
            scope=scope,
            granted_tools=granted_tools,
            granted_resources=granted_resources,
            task_id=task_id,
            parent_task_id=parent_task_id,
            parent_token_id=parent_token_id,
            task_description=task_description,
            scope_inheritance_type=scope_inheritance_type,
            expires_at=expires_at
        )
        
        db.session.add(token)
        db.session.commit()
        
        # Return both the token object and plaintext tokens (only known once)
        return token, access_token, refresh_token
    
    def revoke(self, reason=None):
        """Revoke this token and optionally all child tokens."""
        self.is_revoked = True
        self.revoked_at = datetime.utcnow()
        self.revocation_reason = reason
        
        # Recursively revoke all child tokens
        for child_token in self.child_tokens:
            child_token.revoke(reason=f"Parent token revoked: {reason}")
            
        db.session.commit()
        
    def is_valid(self):
        """Check if token is valid (not expired, not revoked)."""
        return not self.is_revoked and self.expires_at > datetime.utcnow()
    
    def to_dict(self, include_children=False):
        """Convert token to dictionary representation."""
        data = {
            'token_id': self.token_id,
            'client_id': self.client_id,
            'scope': self.scope,
            'granted_tools': self.granted_tools,
            'granted_resources': self.granted_resources,
            'task_id': self.task_id,
            'parent_task_id': self.parent_task_id,
            'parent_token_id': self.parent_token_id,
            'task_description': self.task_description,
            'scope_inheritance_type': self.scope_inheritance_type,
            'issued_at': self.issued_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'is_revoked': self.is_revoked,
            'is_valid': self.is_valid()
        }
        
        if self.revoked_at:
            data['revoked_at'] = self.revoked_at.isoformat()
            data['revocation_reason'] = self.revocation_reason
            
        if include_children:
            data['child_tokens'] = [child.to_dict() for child in self.child_tokens]
            
        return data 