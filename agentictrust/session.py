from __future__ import annotations

import functools
import json
import threading
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, List, Text, Optional, Sequence, Union
from uuid import UUID, uuid4

from .config import Configuration

class Session:
    def __init__(
        self,
        session_id: UUID,
        config: Configuration,
        tags: Optional[List[Text]] = None,
        host_env: Optional[Dict[Text, Any]] = None,
    ):
        pass

active_sessions: List[Session] = []