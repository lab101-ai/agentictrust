"""Policy model for AgenticTrust."""
from sqlalchemy import Column, String, Integer, Text, Table, ForeignKey
from sqlalchemy.orm import relationship
import json
import uuid
from agentictrust.db import Base, db_session
from agentictrust.utils.logger import logger

policy_scope_association = Table(
    'policy_scope_association',
    Base.metadata,
    Column('policy_id', String(36), ForeignKey('policies.policy_id')),
    Column('scope_id', String(36), ForeignKey('scopes.scope_id'))
)

class Policy(Base):
    """Policy model for authorization decisions."""
    
    __tablename__ = 'policies'
    
    policy_id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    effect = Column(String(10), default="allow")  # allow or deny
    priority = Column(Integer, default=0)
    conditions = Column(Text, nullable=True)  # JSON string of conditions
    
    scopes = relationship("Scope", secondary=policy_scope_association, backref="policies")
    
    @classmethod
    def create(cls, name, description=None, effect="allow", priority=0, conditions=None, scope_ids=None):
        """Create a new policy."""
        policy_id = str(uuid.uuid4())
        
        if conditions and isinstance(conditions, dict):
            conditions = json.dumps(conditions)
        elif conditions and not isinstance(conditions, str):
            conditions = str(conditions)
        
        policy = cls(
            policy_id=policy_id,
            name=name,
            description=description,
            effect=effect,
            priority=priority,
            conditions=conditions
        )
        
        db_session.add(policy)
        
        if scope_ids:
            from agentictrust.db.models import Scope
            for scope_id in scope_ids:
                scope = Scope.query.get(scope_id)
                if scope:
                    policy.scopes.append(scope)
        
        db_session.commit()
        return policy
    
    @classmethod
    def get_by_id(cls, policy_id):
        """Get policy by ID."""
        return cls.query.get(policy_id)
    
    @classmethod
    def delete_by_id(cls, policy_id):
        """Delete policy by ID."""
        policy = cls.query.get(policy_id)
        if policy:
            db_session.delete(policy)
            db_session.commit()
            return True
        return False
    
    def get_conditions(self):
        """Get conditions as a dictionary."""
        if self.conditions:
            try:
                return json.loads(self.conditions)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in conditions for policy {self.policy_id}")
        return {}
    
    def set_conditions(self, conditions):
        """Set conditions from a dictionary."""
        if conditions and isinstance(conditions, dict):
            self.conditions = json.dumps(conditions)
        elif conditions:
            self.conditions = str(conditions)
    
    def to_dict(self):
        """Convert policy to dictionary."""
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "description": self.description,
            "effect": self.effect,
            "priority": self.priority,
            "conditions": self.get_conditions(),
            "scopes": [scope.name for scope in self.scopes]
        }
