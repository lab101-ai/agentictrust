from typing import Any, Dict, List, Optional
from .abstract import APIResource


class ScopesResource(APIResource):
    """API resource for scope management."""
    def list(
        self,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_sensitive: Optional[bool] = None
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if category is not None:
            params["category"] = category
        if is_active is not None:
            params["is_active"] = str(is_active).lower()
        if is_sensitive is not None:
            params["is_sensitive"] = str(is_sensitive).lower()
        return self._request("GET", "/api/scopes", params=params)

    def get(self, scope_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/api/scopes/{scope_id}")

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        is_sensitive: Optional[bool] = None,
        requires_approval: Optional[bool] = None,
        is_default: Optional[bool] = None
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {"name": name}
        if description is not None:
            body["description"] = description
        if category is not None:
            body["category"] = category
        if is_sensitive is not None:
            body["is_sensitive"] = is_sensitive
        if requires_approval is not None:
            body["requires_approval"] = requires_approval
        if is_default is not None:
            body["is_default"] = is_default
        return self._request("POST", "/api/scopes", json_data=body)

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
        body: Dict[str, Any] = {}
        for key, value in {
            "name": name,
            "description": description,
            "category": category,
            "is_sensitive": is_sensitive,
            "requires_approval": requires_approval,
            "is_default": is_default,
            "is_active": is_active
        }.items():
            if value is not None:
                body[key] = value
        return self._request("PUT", f"/api/scopes/{scope_id}", json_data=body)

    def delete(self, scope_id: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/api/scopes/{scope_id}")

    def get_default(self) -> List[Any]:
        return self._request("GET", "/api/scopes/default").get("scopes", [])

    def get_categories(self) -> List[str]:
        return self._request("GET", "/api/scopes/categories").get("categories", [])
