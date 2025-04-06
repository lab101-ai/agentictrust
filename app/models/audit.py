import uuid
from datetime import datetime
from app import db
from flask import current_app

class TaskAuditLog(db.Model):
    """Model for auditing task execution and token usage."""
    __tablename__ = 'task_audit_logs'
    
    log_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('agents.client_id'), nullable=False)
    token_id = db.Column(db.String(36), db.ForeignKey('issued_tokens.token_id'), nullable=False)
    access_token_hash = db.Column(db.String(256), nullable=False)
    
    # Task context
    task_id = db.Column(db.String(36), nullable=False)
    parent_task_id = db.Column(db.String(36), nullable=True)
    
    # Event details
    event_type = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False)
    source_ip = db.Column(db.String(45), nullable=True)
    
    # Use JSON type which works in SQLite
    details = db.Column(db.JSON, nullable=True)
    
    @classmethod
    def log_event(cls, client_id, token_id, access_token_hash, task_id, event_type, status, 
                 parent_task_id=None, source_ip=None, details=None):
        """Create a new audit log entry."""
        log_entry = cls(
            client_id=client_id,
            token_id=token_id,
            access_token_hash=access_token_hash,
            task_id=task_id,
            parent_task_id=parent_task_id,
            event_type=event_type,
            status=status,
            source_ip=source_ip,
            details=details or {}
        )
        
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
    
    @classmethod
    def get_task_history(cls, task_id):
        """Get the full history of events for a specific task."""
        return cls.query.filter_by(task_id=task_id).order_by(cls.timestamp).all()
    
    @classmethod
    def get_task_chain(cls, task_id):
        """Get the full chain of parent and child tasks related to a specific task."""
        # First find the root parent
        task = cls.query.filter_by(task_id=task_id).first()
        if not task:
            return []
            
        if task.parent_task_id:
            # Recursively find the root parent
            return cls.get_task_chain(task.parent_task_id)
        
        # Now find all tasks with this root parent
        task_chain = cls.query.filter(
            (cls.task_id == task_id) | 
            (cls.parent_task_id == task_id)
        ).distinct(cls.task_id).all()
        
        # For each child, recursively find their children too
        result = [task_id]
        for task in task_chain:
            if task.task_id != task_id:
                result.append(task.task_id)
                child_chain = cls.get_task_chain(task.task_id)
                for child_id in child_chain:
                    if child_id not in result:
                        result.append(child_id)
                        
        return result
    
    def to_dict(self):
        """Convert audit log to dictionary representation."""
        return {
            'log_id': self.log_id,
            'client_id': self.client_id,
            'token_id': self.token_id,
            'task_id': self.task_id,
            'parent_task_id': self.parent_task_id,
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status,
            'source_ip': self.source_ip,
            'details': self.details
        } 