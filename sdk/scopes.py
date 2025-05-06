from typing import Any, Dict, List, Optional
from .api_resources.scopes import ScopesResource


class ScopesClient:
    """Client for scope management."""
    def __init__(self, parent):
        """Initialize with parent client."""
        self._api = ScopesResource(parent)

    def list(self, category: Optional[str] = None, is_active: Optional[bool] = None, is_sensitive: Optional[bool] = None) -> List[Dict[str, Any]]:
        """List all scopes with optional filters."""
        response = self._api.list(category=category, is_active=is_active, is_sensitive=is_sensitive)
        return response.get('scopes', [])

    def get(self, scope_id: str) -> Dict[str, Any]:
        """Get scope details by ID."""
        return self._api.get(scope_id)

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        is_sensitive: Optional[bool] = None,
        requires_approval: Optional[bool] = None,
        is_default: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Create a new scope."""
        return self._api.create(
            name=name,
            description=description,
            category=category,
            is_sensitive=is_sensitive,
            requires_approval=requires_approval,
            is_default=is_default
        )

    def update(
        self,
        scope_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        is_sensitive: Optional[bool] = None,
        requires_approval: Optional[bool] = None,
        is_default: Optional[bool] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Update an existing scope."""
        return self._api.update(
            scope_id=scope_id,
            name=name,
            description=description,
            category=category,
            is_sensitive=is_sensitive,
            requires_approval=requires_approval,
            is_default=is_default,
            is_active=is_active
        )

    def delete(self, scope_id: str) -> Dict[str, Any]:
        """Delete a scope by ID."""
        return self._api.delete(scope_id)

    def get_default(self) -> List[Dict[str, Any]]:
        """Get all default scopes."""
        return self._api.get_default()

    def get_categories(self) -> List[str]:
        """Get all scope categories."""
        return self._api.get_categories()
