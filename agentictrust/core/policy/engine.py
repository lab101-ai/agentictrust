"""High-level helper to evaluate, cache and audit policy decisions via OPA."""
from __future__ import annotations

from typing import Any, Dict, Optional
from functools import lru_cache

from agentictrust.core.policy.opa_client import opa_client
from agentictrust.db.models.audit.policy_audit import PolicyAuditLog
from agentictrust.utils.logger import logger


class PolicyEngine:  # noqa: D101
    def __init__(self):
        # Could embed LRU for recent decisions to reduce OPA trips
        self._decision_cache: Dict[str, bool] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def is_allowed(self, *, client_id: str, action: str, input_ctx: Dict[str, Any]) -> bool:
        """Evaluate a policy decision via OPA & audit the outcome.

        `input_ctx` should already contain everything the Rego expects (user_id,
        scopes, etc.).  We will just forward and then log.
        """
        try:
            cache_key = self._cache_key(client_id, action, input_ctx)
            if cache_key in self._decision_cache:
                return self._decision_cache[cache_key]

            allowed = opa_client.query_bool_sync("agentictrust/authz/allow", input_ctx)
            # Simple LRU sized 256
            if len(self._decision_cache) > 256:
                self._decision_cache.clear()
            self._decision_cache[cache_key] = allowed
            PolicyAuditLog.log(
                client_id=client_id,
                decision="allow" if allowed else "deny",
                action=action,
                policy_path="agentictrust/authz/allow",
                details=input_ctx,
            )
            return allowed
        except Exception as e:
            logger.error("PolicyEngine.is_allowed failed: %s", e)
            # Conservative deny on error
            PolicyAuditLog.log(
                client_id=client_id,
                decision="deny",
                action=action,
                reason="exception",
                details={"error": str(e), **input_ctx},
            )
            return False

    # ------------------------------------------------------------------
    @staticmethod
    def _cache_key(client_id: str, action: str, ctx: Dict[str, Any]) -> str:  # noqa: D401
        return f"{client_id}:{action}:{hash(frozenset(ctx.items()))}"


# ----------------------------------------------------------------------------
# Singleton accessor
# ----------------------------------------------------------------------------
@lru_cache(maxsize=None)
def get_policy_engine() -> PolicyEngine:  # pragma: no cover
    return PolicyEngine()
