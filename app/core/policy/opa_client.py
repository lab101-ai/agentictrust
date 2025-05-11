import logging
from typing import Any, Dict

import httpx
from app.config import Config
import requests

logger = logging.getLogger(__name__)

class OPAClient:
    """
    Simple client for querying an Open Policy Agent (OPA) server.
    """
    def __init__(self):
        self.enabled = Config.ENABLE_OPA_POLICIES
        # Construct the full URL to the OPA policy decision endpoint
        self.url = f"{Config.OPA_HOST}:{Config.OPA_PORT}/v1/data/{Config.OPA_POLICY_PATH}"
        # Async HTTP client with a default timeout
        self._client = httpx.AsyncClient(timeout=1.0)

    async def is_allowed(self, input_data: Dict[str, Any]) -> bool:
        """
        Query OPA with the provided input. Returns True if the policy allows the action.
        """
        if not self.enabled:
            # OPA is disabled, defer to existing Python policy engine
            return True
        try:
            response = await self._client.post(self.url, json={"input": input_data})
            response.raise_for_status()
            result = response.json().get("result", False)
            return bool(result)
        except Exception as e:
            # Log and default to deny on any communication error
            logger.error(f"OPA query failed: {e}")
            return False

    async def query_bool(self, rule_path: str, input_data: Dict[str, Any]) -> bool:
        """Async helper to POST to /v1/data/<rule_path> and return boolean result."""
        if not self.enabled:
            return True  # default allow when OPA disabled
        url = f"{self.url.rsplit('/',1)[0]}/{rule_path}"
        try:
            resp = await self._client.post(url, json={"input": input_data})
            resp.raise_for_status()
            # If "result" key missing or is null/empty, treat as default allow to prevent false denial when policy not defined.
            json_data = resp.json()
            if "result" not in json_data:
                return True  # Undefined rule – default allow
            result = json_data.get("result")
            # If result is explicitly boolean, return its truthiness
            if isinstance(result, bool):
                return result
            # Empty object/array means undefined – allow
            if result in (None, {}, []):
                return True
            return bool(result)
        except Exception as e:
            logger.error(f"OPA query_bool failed ({url}): {e}")
            return False

    # ------------------------------------------------------------------
    # Synchronous helpers for pushing data documents (used by CRUD hooks)
    # ------------------------------------------------------------------

    @property
    def _data_base_url(self) -> str:
        """Return base URL for Data API (without trailing slash)."""
        return f"{Config.OPA_HOST}:{Config.OPA_PORT}/v1/data"

    def put_data(self, path: str, value: Any) -> None:
        """Synchronously PUT a document into OPA Data API.

        Example: path="admin/policies/1234" will send PUT to
        <base>/admin/policies/1234 with JSON body {"value": value}
        """
        if not self.enabled:
            return
        url = f"{self._data_base_url}/{path}"
        try:
            resp = requests.put(url, json={"value": value}, timeout=1.0)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"OPA put_data failed ({url}): {e}")

    def delete_data(self, path: str) -> None:
        """Synchronously DELETE a document in OPA."""
        if not self.enabled:
            return
        url = f"{self._data_base_url}/{path}"
        try:
            resp = requests.delete(url, timeout=1.0)
            if resp.status_code not in (200, 204):
                logger.error(f"OPA delete_data unexpected status {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"OPA delete_data failed ({url}): {e}")

    def get_data(self, path: str) -> Any:
        """GET a document (or subtree) from OPA Data API. Returns None on error."""
        if not self.enabled:
            return None
        url = f"{self._data_base_url}/{path}"
        try:
            resp = requests.get(url, timeout=1.0)
            if resp.status_code == 200:
                return resp.json().get("result")
            return None
        except Exception as e:
            logger.error(f"OPA get_data failed ({url}): {e}")
            return None

    # ------------------------------------------------------------------
    # Synchronous helper – safe to call from FastAPI thread context where
    # an event loop is already running (avoids asyncio.run()).
    # ------------------------------------------------------------------
    def query_bool_sync(self, rule_path: str, input_data: Dict[str, Any]) -> bool:
        """Blocking wrapper around the Data API returning boolean result."""
        if not self.enabled:
            return True
        url = f"{self.url.rsplit('/',1)[0]}/{rule_path}"
        try:
            resp = requests.post(url, json={"input": input_data}, timeout=1.0)
            resp.raise_for_status()
            # If "result" key missing or is null/empty, treat as default allow to prevent false denial when policy not defined.
            json_data = resp.json()
            if "result" not in json_data:
                return True  # Undefined rule – default allow
            result = json_data.get("result")
            # If result is explicitly boolean, return its truthiness
            if isinstance(result, bool):
                return result
            # Empty object/array means undefined – allow
            if result in (None, {}, []):
                return True
            return bool(result)
        except Exception as e:
            logger.error(f"OPA query_bool_sync failed ({url}): {e}")
            return False

# Singleton instance to be imported elsewhere
opa_client = OPAClient() 