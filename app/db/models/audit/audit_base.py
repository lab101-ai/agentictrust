"""
Base class for audit logs.
"""
import uuid
import logging
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.db import Base

logger = logging.getLogger(__name__)

class BaseAuditLog(Base):
    __abstract__ = True

    log_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow)
    log_type = Column(String(50), nullable=False)

    def __init__(self, *args, **kwargs):
        if 'log_type' not in kwargs:
            kwargs['log_type'] = self.__class__.__name__
        super().__init__(*args, **kwargs)

    @classmethod
    def log(cls, *args, **kwargs):
        logger.warning(f"{cls.__name__}.log() not implemented; please override in subclass.")
        return None

    def to_dict(self):
        """Serialize common audit log fields.

        Subclasses are encouraged to call ``super().to_dict()`` and extend the
        returned dictionary with any model-specific data.  This base
        implementation no longer emits a warning so that legitimate subclass
        calls do not pollute the logs.  If a subclass does *not* override
        ``to_dict`` it will simply inherit this common representation, which
        is usually acceptable for quick debugging but can be customised as
        needed.
        """
        return {
            'log_id': self.log_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'log_type': self.log_type,
        }
