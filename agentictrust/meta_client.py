from .log_config import logger
import traceback

from .host_env import get_host_env
from .http_client import HttpClient
from .helpers import safe_serialize, get_agentictrust_version

def handle_exceptions(method):
    """Decorator within the metaclass to wrap method execution in try-except block."""
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception as e:
            logger.warning(f"Error: {e}")
            config = getattr(self, "config", None)
            if config is not None:
                session = None
                if len(self._sessions) > 0:
                    session = self._sessions[0]
                type(self).send_exception_to_server(e, self.config._api_key, session)
            raise e

    return wrapper

class MetaClient(type):
    """Metaclass to automatically decorate methods with exception handling and provide a shared exception handler."""

    def __new__(cls, name, bases, dct):

        for method_name, method in dct.items():
            if (callable(method) and not method_name.startswith("__")) or method_name == "__init__":
                dct[method_name] = handle_exceptions(method)

        return super().__new__(cls, name, bases, dct)
    
    def send_exception_to_server(self, exception, api_key, session):
        if api_key:
            exception_type = type(exception).__name__
            exception_message = str(exception)
            exception_traceback = traceback.format_exc()
            developer_error = {
                "sdk_version": get_agentictrust_version(),
                "type": exception_type,
                "message": exception_message,
                "stack_trace": exception_traceback,
                "host_env": get_host_env(),
            }

            if session:
                developer_error["session_id"] = session.session_id
            try:
                HttpClient.post(
                    "https://api.agentictrust.ai/v2/developer_errors",
                    safe_serialize(developer_error).encode("utf-8"),
                    api_key=api_key,
                )
            except Exception as e:
                logger.warning(f"Error sending exception to server: {e}")
                pass
