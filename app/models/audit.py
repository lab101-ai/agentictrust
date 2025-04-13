import uuid
from datetime import datetime
from app import db
from flask import current_app

class TaskAuditLog(db.Model):
    """Model for auditing task execution and token usage."""
    __tablename__ = 'task_audit_logs'
    
    log_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('agents.client_id'), nullable=False)
    token_id = db.Column(db.String(36), nullable=False, index=True)
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
        try:
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
        except Exception as e:
            current_app.logger.error(f"Error creating audit log: {str(e)}")
            db.session.rollback()
            
            # If it's a NOT NULL constraint error for token_id, try the error_log method
            if "NOT NULL constraint failed" in str(e) and "token_id" in str(e):
                return cls.error_log(
                    client_id=client_id,
                    task_id=task_id, 
                    event_type=event_type,
                    status=status,
                    parent_task_id=parent_task_id,
                    source_ip=source_ip,
                    details=details
                )
            return None
    
    @classmethod
    def error_log(cls, client_id, task_id, event_type, status, 
                parent_task_id=None, source_ip=None, details=None):
        """
        Create an audit log for errors that occur before a token exists.
        Uses a synthetic token_id to satisfy database constraints.
        
        Note: This uses a special token_id format "error-<uuid>" that won't exist in the 
        issued_tokens table. The relationship with IssuedToken is handled using primaryjoin
        in the IssuedToken model.
        """
        try:
            import uuid
            
            # Generate a special error token ID with a recognizable prefix
            error_token_id = f"error-{uuid.uuid4()}"
            
            log_entry = cls(
                client_id=client_id,
                token_id=error_token_id,  # Use synthetic token ID with "error-" prefix
                access_token_hash="error_log_entry",  # Use placeholder hash
                task_id=task_id,
                parent_task_id=parent_task_id,
                event_type=event_type,
                status=status,
                source_ip=source_ip,
                details=details or {}
            )
            
            # Add extra context that this is an error log without a real token
            if details is None:
                log_entry.details = {}
            log_entry.details["_error_log"] = True
            log_entry.details["_error_token_id"] = error_token_id
            
            db.session.add(log_entry)
            db.session.commit()
            current_app.logger.debug(f"Created error audit log entry with synthetic token: {error_token_id}")
            return log_entry
        except Exception as e:
            current_app.logger.error(f"Error creating error audit log: {str(e)}")
            db.session.rollback()
            return None
    
    @classmethod
    def is_error_token(cls, token_id):
        """Check if a token ID is a synthetic error token."""
        return token_id and isinstance(token_id, str) and token_id.startswith("error-")
    
    @classmethod
    def get_task_history(cls, task_id):
        """Get the full history of events for a specific task."""
        return cls.query.filter_by(task_id=task_id).order_by(cls.timestamp).all()
    
    @classmethod
    def get_task_chain(cls, task_id, visited_tasks=None):
        """
        Get the full chain of parent and child tasks related to a specific task.
        Using visited_tasks set to prevent infinite recursion in case of circular references.
        """
        try:
            # Initialize visited tasks set to prevent infinite recursion
            if visited_tasks is None:
                visited_tasks = set()
                
            # If we've already visited this task, return empty to avoid infinite recursion
            if task_id in visited_tasks:
                current_app.logger.warning(f"Circular reference detected in task chain for task_id: {task_id}")
                return []
                
            # Add current task to visited set
            visited_tasks.add(task_id)
                
            # First find the task
            task = cls.query.filter_by(task_id=task_id).first()
            if not task:
                current_app.logger.warning(f"Task not found for task_id: {task_id}")
                return []
                
            # Find the root parent
            if task.parent_task_id:
                # Make sure we're not in a loop
                if task.parent_task_id in visited_tasks:
                    current_app.logger.warning(f"Circular reference detected in parent chain for task_id: {task_id}")
                    return [task_id]  # Return only current task to break the cycle
                return cls.get_task_chain(task.parent_task_id, visited_tasks)
            
            # Reset visited set for the second phase (finding children)
            visited_tasks = {task_id}
            
            # Now find all tasks with this root parent
            try:
                task_chain = cls.query.filter(
                    (cls.task_id == task_id) | 
                    (cls.parent_task_id == task_id)
                ).distinct(cls.task_id).all()
            except Exception as e:
                current_app.logger.error(f"Error querying task chain: {str(e)}")
                return [task_id]  # Return at least the current task
            
            # For each child, recursively find their children too
            result = [task_id]
            for task in task_chain:
                if task.task_id != task_id and task.task_id not in visited_tasks:
                    result.append(task.task_id)
                    visited_tasks.add(task.task_id)
                    child_chain = cls.get_task_chain(task.task_id, visited_tasks.copy())
                    for child_id in child_chain:
                        if child_id not in result:
                            result.append(child_id)
                            
            return result
        except Exception as e:
            current_app.logger.error(f"Unexpected error in get_task_chain for task_id {task_id}: {str(e)}")
            return [task_id] if task_id else []
    
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