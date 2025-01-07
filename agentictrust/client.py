"""
AgenticTrust client module that provides a client class with public interfaces and configuration options.

Classes:
    Client: Provides methods to interact with the AgenticTrust platform.
"""

import atexit
import inspect
import logging
import os
import signal
import sys
import threading
import traceback
from decimal import Decimal
from functools import cached_property
from typing import List, Optional, Text, Union
from uuid import UUID, uuid4

from .log_config import logger
from .host_env import get_host_env
from .meta_client import MetaClient
from .session import Session, active_sessions
from .singleton import conditional_singleton


@conditional_singleton
class Client(metaclass=MetaClient):
    def __init__(self):
        self._pre_init_messages: List[Text] = []
        self._initialized: bool = False
        self._sessions: List[Session] = active_sessions
        self._config: Config = Config()
        pass



    def unsupress_logs(self):
        logging_level = os.getenv("AGENTICTRUST_LOGGING_LEVEL", "INFO")
        log_levels = {
            "CRITICAL": logging.CRITICAL,
            "ERROR": logging.ERROR,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "DEBUG": logging.DEBUG,
        }
        logger.setLevel(log_levels.get(logging_level, "INFO"))

        for message in self._pre_init_messages:
            logger.warning(message)

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def has_sessions(self) -> bool:
        return len(self._sessions) > 0

    @property
    def is_multi_session(self) -> bool:
        return len(self._sessions) > 1

    @property
    def session_count(self) -> int:
        return len(self._sessions)

    @property
    def current_session_ids(self) -> List[str]:
        return [str(s.session_id) for s in self._sessions]

    @property
    def api_key(self):
        return self._config.api_key

    @property
    def parent_key(self):
        return self._config.parent_key

    @cached_property
    def host_env(self):
        """Cache and reuse host environment data"""
        return get_host_env(self._config.env_data_opt_out)
