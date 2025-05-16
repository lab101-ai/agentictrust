"""Business logic facade around UserAgentAuthorization."""
from typing import List, Dict, Any

from agentictrust.db.models.user_agent_authorization import UserAgentAuthorization
from agentictrust.utils.logger import logger


class AuthorizationEngine:
    """CRUD helper for user ↔ agent authorization."""

    # ------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------
    def create(self, *, user_id: str, agent_id: str, scopes: List[str]) -> Dict[str, Any]:
        row = UserAgentAuthorization.create(user_id=user_id, agent_id=agent_id, scopes=scopes)
        logger.info("Authorization created: %s", row.authorization_id)
        return row.to_dict()

    def revoke(self, authorization_id: str):
        row = UserAgentAuthorization.get_by_id(authorization_id)
        row.revoke()
        logger.info("Authorization revoked: %s", authorization_id)

    def list_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in UserAgentAuthorization.get_active_for_user(user_id)]
