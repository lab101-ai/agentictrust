"""Model linking human users with the agents they have authorised."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Dict, Any

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Boolean, Index
from sqlalchemy.exc import SQLAlchemyError
from agentictrust.db import Base, db_session
from agentictrust.utils.logger import logger


class UserAgentAuthorization(Base):
    """Records that *user_id* has granted *agent_id* a subset of scopes."""

    __tablename__ = "user_agent_authorizations"

    authorization_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False, index=True)
    agent_id = Column(String(36), ForeignKey("agents.client_id"), nullable=False, index=True)
    scopes = Column(JSON, nullable=False)  # list[str] – scope IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("idx_user_agent", "user_id", "agent_id", "is_active"),
    )

    # ------------------------------------------------------------------
    # CRUD helpers
    # ------------------------------------------------------------------
    @classmethod
    def create(cls, *, user_id: str, agent_id: str, scopes: List[str]) -> "UserAgentAuthorization":
        if not scopes:
            raise ValueError("scopes must be provided")
        try:
            inst = cls(user_id=user_id, agent_id=agent_id, scopes=scopes)
            db_session.add(inst)
            db_session.commit()
            logger.info("Created authorization %s (user=%s → agent=%s)", inst.authorization_id, user_id, agent_id)
            return inst
        except SQLAlchemyError as e:
            db_session.rollback()
            raise RuntimeError(f"DB error creating authorization: {e}") from e

    def revoke(self):
        if not self.is_active:
            return
        self.is_active = False
        self.revoked_at = datetime.utcnow()
        db_session.commit()
        logger.info("Revoked authorization %s", self.authorization_id)

    # Convenience
    def to_dict(self) -> Dict[str, Any]:
        return {
            "authorization_id": self.authorization_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "scopes": self.scopes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "is_active": self.is_active,
        }

    @classmethod
    def get_active_for_user(cls, user_id: str) -> List["UserAgentAuthorization"]:
        return cls.query.filter_by(user_id=user_id, is_active=True).all()

    @classmethod
    def get_by_id(cls, aid: str) -> "UserAgentAuthorization":
        row = cls.query.get(aid)
        if not row:
            raise ValueError("authorization_not_found")
        return row
