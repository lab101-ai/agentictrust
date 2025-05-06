from typing import Any, Dict, List, Optional
from .abstract import APIResource


class PoliciesResource(APIResource):
    """API resource for policy management."""

    def list(self) -> Dict[str, Any]:
        """List all policies."""
        return self._request("GET", "/api/policies")

    def get(self, policy_id: str) -> Dict[str, Any]:
        """Get a policy by ID."""
        return self._request("GET", f"/api/policies/{policy_id}")

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
        body: Dict[str, Any] = {"name": name}
        if description is not None:
            body["description"] = description
        if scopes is not None:
            body["scopes"] = scopes
        if conditions is not None:
            body["conditions"] = conditions
        if effect is not None:
            body["effect"] = effect
        if scope_id is not None:
            body["scope_id"] = scope_id
        if priority is not None:
            body["priority"] = priority
        return self._request("POST", "/api/policies", json_data=body)

    def update(self, policy_id: str, **kwargs) -> Dict[str, Any]:
        """Update a policy."""
        return self._request("PUT", f"/api/policies/{policy_id}", json_data=kwargs)

    def delete(self, policy_id: str) -> Dict[str, Any]:
        """Delete a policy."""
        return self._request("DELETE", f"/api/policies/{policy_id}")

    def activate(self, policy_id: str) -> Dict[str, Any]:
        """Activate a policy."""
        return self._request("PUT", f"/api/policies/{policy_id}/activate")

    def deactivate(self, policy_id: str) -> Dict[str, Any]:
        """Deactivate a policy."""
        return self._request("PUT", f"/api/policies/{policy_id}/deactivate")

    def evaluate(self, context: Any, scope: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate policies against a context."""
        payload: Dict[str, Any] = {"context": context}
        if scope is not None:
            payload["scope"] = scope
        return self._request("POST", "/api/policies/evaluate", json_data=payload)

    def test(self, policy: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Test a policy without saving."""
        return self._request("POST", "/api/policies/test", json_data={"policy": policy, "context": context})

    def get_metrics(self) -> Dict[str, Any]:
        """Get policy usage and evaluation metrics."""
        return self._request("GET", "/api/policies/metrics")
