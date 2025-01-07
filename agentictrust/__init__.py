# agentictrust/__init__.py
import sys
from typing import Optional, List, Union, Text

from .client import Client

def init(
    api_key: Optional[Text] = None,
    endpoint: Optional[Text] = None,
    max_wait_time: Optional[int] = None,
    max_queue_size: Optional[int] = None,
    tags: Optional[List[Text]] = None,
    default_tags: Optional[List[Text]] = None,
    auto_start_session: Optional[bool] = None,
    inherited_session_id: Optional[Text] = None,
    auto_end_session: Optional[bool] = None,
) -> None:
    """
    Initializes the agentictrust singleton instance.

    Args:
        api_key: The API key for the agentictrust platform.
        endpoint: The endpoint for the agentictrust platform.
        max_wait_time: The maximum wait time for the agentictrust platform.
        max_queue_size: The maximum queue size for the agentictrust platform.
        tags: The tags for the agentictrust platform.
        default_tags: The default tags for the agentictrust platform.
        auto_start_session: Whether to automatically start a session.
        inherited_session_id: The session ID to inherit.
        auto_end_session: Whether to automatically end a session.

    Attributes:
    """
    Client().unsupress_logs()