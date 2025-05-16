"""Link table assigning Roles to Agents."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, Any

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.exc import SQLAlchemyError

from agentictrust.db import Base, db_session
from agentictrust.utils.logger import logger


class AgentRoleAssignment(Base):
    __tablename__ = "agent_role_assignments"

    assignment_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), ForeignKey("agents.client_id"), nullable=False)
    role_id = Column(String(36), ForeignKey("roles.role_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("agent_id", "role_id", name="uq_agent_role"),
    )

    @classmethod
    def assign(cls, *, agent_id: str, role_id: str) -> "AgentRoleAssignment":
        try:
            inst = cls(agent_id=agent_id, role_id=role_id)
            db_session.add(inst)
            db_session.commit()
            logger.info("Assigned role %s to agent %s", role_id, agent_id)
            return inst
        except SQLAlchemyError as e:
            db_session.rollback()
            raise RuntimeError(f"DB error assigning role: {e}") from e

    def unassign(self):
        db_session.delete(self)
        db_session.commit()
        logger.info("Unassigned role %s from agent %s", self.role_id, self.agent_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assignment_id": self.assignment_id,
            "agent_id": self.agent_id,
            "role_id": self.role_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
