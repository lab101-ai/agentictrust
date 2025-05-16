"""Utility helpers for user authentication: password hashing and JWT handling."""
from datetime import datetime, timedelta
from typing import Optional

import jwt
from werkzeug.security import generate_password_hash, check_password_hash

from agentictrust.config import Config


ALGORITHM: str = "HS256"  # HS256 for simple session tokens (separate from RS256 agent tokens)


def hash_password(password: str) -> str:
    """Return a salted hash for the supplied password."""
    return generate_password_hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Return True if the supplied password matches the stored hash."""
    return check_password_hash(hashed, password)


def create_access_token(subject: str, *, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT for the given user ID (``sub``).

    Parameters
    ----------
    subject: str
        The user_id to embed in the ``sub`` claim.
    expires_delta: timedelta | None
        Relative expiry.  Defaults to 1 hour if omitted.
    """
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=1))
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, Config.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode a user JWT and return its claims dict, or ``None`` if invalid/expired."""
    try:
        return jwt.decode(token, Config.SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
