from typing import Any, Dict, List, Optional
from .abstract import APIResource

class DelegationsResource(APIResource):
    """API resource for delegation grants."""

    def create(
        self,
        principal_type: str,
        principal_id: str,
        delegate_id: str,
        scope: List[str],
        max_depth: int = 1,
        constraints: Optional[Dict[str, Any]] = None,
        ttl_hours: int = 24,
    ) -> Dict[str, Any]:
        """Create a new delegation grant."""
        data = {
            "principal_type": principal_type,
            "principal_id": principal_id,
            "delegate_id": delegate_id,
            "scope": scope,
            "max_depth": max_depth,
            "constraints": constraints,
            "ttl_hours": ttl_hours,
        }
        return self._request("POST", "/api/delegations", json_data=data)

    def delete(self, grant_id: str) -> Dict[str, Any]:
        """Delete a delegation grant."""
        return self._request("DELETE", f"/api/delegations/{grant_id}")

    def get(self, grant_id: str) -> Dict[str, Any]:
        """Get a delegation grant by ID."""
        return self._request("GET", f"/api/delegations/{grant_id}")

    def list_for_principal(self, principal_id: str) -> List[Dict[str, Any]]:
        """List all delegation grants for a principal."""
        return self._request("GET", f"/api/delegations/principal/{principal_id}") 