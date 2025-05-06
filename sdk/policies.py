from typing import Any, Dict, List, Optional
from .api_resources.policies import PoliciesResource


class PoliciesClient:
    """Client for policy management."""
    def __init__(self, parent):
        """Initialize with parent client."""
        self._api = PoliciesResource(parent)

    def list(self) -> List[Dict[str, Any]]:
        """List all policies."""
        response = self._api.list()
        return response.get('policies', [])

    def get(self, policy_id: str) -> Dict[str, Any]:
        """Get policy details by ID."""
        return self._api.get(policy_id)

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        conditions: Any = None,
        effect: str = "allow",
        scope_id: Optional[str] = None,
        priority: int = 10
    ) -> Dict[str, Any]:
        """Create a new policy."""
        return self._api.create(
            name=name,
            description=description,
            scopes=scopes,
            conditions=conditions,
            effect=effect,
            scope_id=scope_id,
            priority=priority
        )

    def update(self, policy_id: str, **kwargs) -> Dict[str, Any]:
        """Update a policy."""
        return self._api.update(policy_id, **kwargs)

    def delete(self, policy_id: str) -> Dict[str, Any]:
        """Delete a policy."""
        return self._api.delete(policy_id)

    def activate(self, policy_id: str) -> Dict[str, Any]:
        """Activate a policy."""
        return self._api.activate(policy_id)

    def deactivate(self, policy_id: str) -> Dict[str, Any]:
        """Deactivate a policy."""
        return self._api.deactivate(policy_id)

    def evaluate(self, context: Any, scope: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate policies against a context."""
        return self._api.evaluate(context, scope)

    def test(self, policy: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Test a policy without saving."""
        return self._api.test(policy, context)

    def get_metrics(self) -> Dict[str, Any]:
        """Get policy usage metrics."""
        return self._api.get_metrics()
