"""
Task-related audit logging models.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, JSON, ForeignKey
from agentictrust.db.models.audit.audit_base import BaseAuditLog
from agentictrust.db import db_session
from agentictrust.utils.logger import logger

class TaskAuditLog(BaseAuditLog):
    """Model for auditing task execution and token usage."""
    __tablename__ = 'task_audit_logs'
    
    # log_id inherited from BaseAuditLog
    client_id = Column(String(36), ForeignKey('agents.client_id'), nullable=False)
    token_id = Column(String(36), nullable=False, index=True)
    access_token_hash = Column(String(256), nullable=False)
    
    # Task context
    task_id = Column(String(36), nullable=False)
    parent_task_id = Column(String(36), nullable=True)
    
    # Event details
    event_type = Column(String(50), nullable=False)
    # timestamp inherited from BaseAuditLog
    status = Column(String(20), nullable=False)
    source_ip = Column(String(45), nullable=True)
    
    # Use JSON type which works in SQLite
    details = Column(JSON, nullable=True)
    
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
            
            db_session.add(log_entry)
            db_session.commit()
            return log_entry
        except Exception as e:
            logger.error(f"Error creating audit log: {str(e)}")
            db_session.rollback()
            
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
            
            db_session.add(log_entry)
            db_session.commit()
            return log_entry
        except Exception as e:
            logger.error(f"Error creating error audit log: {str(e)}")
            db_session.rollback()
            return None
    
    def to_dict(self):
        """Convert the audit log to a dictionary."""
        return {
            'log_id': self.log_id,
            'client_id': self.client_id,
            'token_id': self.token_id,
            'task_id': self.task_id,
            'parent_task_id': self.parent_task_id,
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'status': self.status,
            'source_ip': self.source_ip,
            'details': self.details or {}
        }
        
    @classmethod
    def get_task_history(cls, task_id):
        """Get the full history of events for a specific task."""
        return cls.query.filter_by(task_id=task_id).order_by(cls.timestamp).all()
    
    @classmethod
    def get_task_chain(cls, task_id):
        """
        Get the full chain of parent and child tasks related to a specific task.
        First finds the root task, then builds a complete hierarchical chain.
        """
        try:
            logger.info(f"Finding task chain for task ID: {task_id}")
            
            # Step 1: Find the root task by following parent tasks
            root_task_id = cls._find_root_task(task_id)
            logger.info(f"Found root task ID: {root_task_id}")
            
            # Step 2: Build the complete chain starting from the root
            chain = cls._build_complete_chain(root_task_id)
            
            # Log the result for debugging
            logger.info(f"Complete task chain: {chain}")
            return chain
        except Exception as e:
            logger.error(f"Unexpected error in get_task_chain for task_id {task_id}: {str(e)}")
            return [task_id] if task_id else []
    
    @classmethod
    def _find_root_task(cls, task_id, visited=None):
        """
        Find the root task by traversing upward through parent_task_id.
        """
        if not visited:
            visited = set()
            
        if task_id in visited:
            # Circular reference detected, break the chain
            logger.warning(f"Circular reference detected when finding root for task_id: {task_id}")
            return task_id
            
        visited.add(task_id)
        
        # Get the current task
        task = cls.query.filter_by(task_id=task_id).first()
        if not task:
            logger.warning(f"Task not found for task_id: {task_id}")
            return task_id
            
        # If no parent, this is the root
        if not task.parent_task_id:
            return task_id
            
        # Otherwise, check parent
        return cls._find_root_task(task.parent_task_id, visited)
    
    @classmethod
    def _build_complete_chain(cls, root_task_id):
        """
        Build a complete hierarchical chain of tasks starting from the root.
        Uses breadth-first traversal to find all related tasks.
        """
        # Initialize with the root task
        all_tasks = set([root_task_id])
        task_chain = [root_task_id]  # Ordered list starting with root
        
        # Queue for breadth-first traversal
        queue = [root_task_id]
        visited = set([root_task_id])
        
        while queue:
            current_task_id = queue.pop(0)
            
            # Find all direct children of the current task
            children = cls.query.filter_by(parent_task_id=current_task_id).all()
            
            for child in children:
                if child.task_id not in visited:
                    visited.add(child.task_id)
                    queue.append(child.task_id)
                    all_tasks.add(child.task_id)
                    task_chain.append(child.task_id)  # Add to ordered list
        
        # Double check if we missed any related tasks
        # This catches tasks that might be related by reference but missing proper parent_task_id
        try:
            # Find all tasks that mention any task in our chain in their details
            for task_id in list(all_tasks):  # Use a copy to avoid modifying during iteration
                # Look for references in details
                referenced_tasks = cls.query.filter(
                    cls.details.contains(task_id)  # This works for JSON fields
                ).all()
                
                for ref_task in referenced_tasks:
                    if ref_task.task_id not in all_tasks:
                        all_tasks.add(ref_task.task_id)
                        task_chain.append(ref_task.task_id)
        except Exception as e:
            # This is a supplementary check, continue even if it fails
            logger.warning(f"Error during supplementary task chain check: {str(e)}")
        
        return task_chain
