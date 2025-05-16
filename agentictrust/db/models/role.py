"""Role model for RBAC.

Each Role groups a set of scope IDs which can be granted to agents.  Agents may
be assigned multiple roles via the `AgentRoleAssignment` link table.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Dict, Any

from sqlalchemy import Column, String, Text, DateTime, JSON, UniqueConstraint
from sqlalchemy.exc import SQLAlchemyError

from agentictrust.db import Base, db_session
from agentictrust.utils.logger import logger


class Role(Base):
    __tablename__ = "roles"

    role_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    scopes = Column(JSON, nullable=False, default=list)  # list[str]

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("name", name="uq_role_name"),
    )

    # ------------------------------------------------------------------
    # CRUD helpers
    # ------------------------------------------------------------------
    @classmethod
    def create(cls, *, name: str, description: str | None = None, scopes: List[str] | None = None) -> "Role":
        try:
            inst = cls(name=name, description=description, scopes=scopes or [])
            db_session.add(inst)
            db_session.commit()
            logger.info("Created role %s", name)
            return inst
        except SQLAlchemyError as e:
            db_session.rollback()
            raise RuntimeError(f"DB error creating role: {e}") from e

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if v is not None:
                setattr(self, k, v)
        db_session.commit()

    def delete(self):
        db_session.delete(self)
        db_session.commit()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_id": self.role_id,
            "name": self.name,
            "description": self.description,
            "scopes": self.scopes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
