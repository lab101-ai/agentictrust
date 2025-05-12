"""AuthorizationCode model stores one-time OAuth 2.1 / PKCE codes.

This is a fresh table – we are *not* using Alembic migrations yet, so the
presence of this file plus a call to `init_db()` will create it automatically.
"""
from __future__ import annotations

import uuid
import hashlib
import traceback
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union

from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from agentictrust.db import Base, db_session
from agentictrust.utils.logger import logger


class AuthorizationCode(Base):
    """DB row representing a single authorisation code awaiting exchange."""

    __tablename__ = "authorization_codes"

    code_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # store SHA-256 hash of the *plaintext* code
    code_hash = Column(String(64), nullable=False, index=True, unique=True)

    client_id = Column(String(36), ForeignKey("agents.client_id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=True)

    scope = Column(Text, nullable=False)
    redirect_uri = Column(Text, nullable=False)

    # PKCE
    code_challenge = Column(String(128), nullable=False)
    code_challenge_method = Column(String(10), nullable=False, default="S256")

    # housekeeping
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    revoked = Column(Boolean, default=False)

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    @classmethod
    def _hash(cls, plaintext: str) -> str:  # pragma: no cover
        return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()

    @classmethod
    def create(
        cls,
        *,
        code_plain: str,
        client_id: str,
        scope: List[str] | str,
        redirect_uri: str,
        code_challenge: str,
        code_challenge_method: str = "S256",
        user_id: Optional[str] = None,
        lifetime_seconds: int = 600,
    ) -> "AuthorizationCode":
        """Persist a new authorisation code row and return instance."""
        # Validate required inputs
        if not code_plain:
            logger.error("Cannot create authorization code: code_plain is required")
            raise ValueError("code_plain is required")
        if not client_id:
            logger.error("Cannot create authorization code: client_id is required")
            raise ValueError("client_id is required")
        if not scope:
            logger.error("Cannot create authorization code: scope is required")
            raise ValueError("scope is required")
        if not redirect_uri:
            logger.error("Cannot create authorization code: redirect_uri is required")
            raise ValueError("redirect_uri is required")
        if not code_challenge:
            logger.error("Cannot create authorization code: code_challenge is required")
            raise ValueError("code_challenge is required")
            
        # Validate code_challenge_method
        if code_challenge_method not in ["S256", "plain"]:
            logger.warning(f"Using non-standard code_challenge_method: {code_challenge_method}")
            
        # Convert scope list to space-separated string if needed
        try:
            if isinstance(scope, list):
                scope = " ".join(scope)
                
            now = datetime.utcnow()
            code_hash = cls._hash(code_plain)
            
            row = cls(
                code_hash=code_hash,
                client_id=client_id,
                user_id=user_id,
                scope=scope,
                redirect_uri=redirect_uri,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method,
                created_at=now,
                expires_at=now + timedelta(seconds=lifetime_seconds),
            )
            
            db_session.add(row)
            db_session.commit()
            
            # Log successful creation
            expiry_time = row.expires_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            log_msg = f"Created authorization code for client {client_id}"
            if user_id:
                log_msg += f" and user {user_id}"
            log_msg += f", expires at {expiry_time}"
            logger.info(log_msg)
            
            return row
            
        except IntegrityError as e:
            db_session.rollback()
            err_msg = f"Database integrity error creating authorization code: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            
            # Check for unique constraint violation
            if "unique constraint" in str(e).lower() and "code_hash" in str(e).lower():
                raise ValueError(f"Authorization code with this hash already exists") from e
            raise ValueError(f"Could not create authorization code due to database constraint: {str(e)}") from e
            
        except SQLAlchemyError as e:
            db_session.rollback()
            err_msg = f"Database error creating authorization code: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to create authorization code: {str(e)}") from e
            
        except Exception as e:
            db_session.rollback()
            err_msg = f"Unexpected error creating authorization code: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to create authorization code: {str(e)}") from e

    # ------------------------------------------------------------------
    # Verification / consumption
    # ------------------------------------------------------------------
    @classmethod
    def verify(
        cls,
        *,
        code_plain: str,
        client_id: str,
        redirect_uri: str,
        now: Optional[datetime] = None,
    ) -> "AuthorizationCode":
        """Return row if valid; raise ValueError otherwise."""
        # Input validation
        if not code_plain:
            logger.error("Cannot verify authorization code: code_plain is required")
            raise ValueError("invalid_grant: code is required")
        if not client_id:
            logger.error("Cannot verify authorization code: client_id is required")
            raise ValueError("invalid_grant: client_id is required")
        if not redirect_uri:
            logger.error("Cannot verify authorization code: redirect_uri is required")
            raise ValueError("invalid_grant: redirect_uri is required")
            
        try:
            code_hash = cls._hash(code_plain)
            logger.debug(f"Verifying authorization code for client: {client_id}")
            
            row = (
                db_session.query(cls)
                .filter_by(code_hash=code_hash, client_id=client_id)
                .first()
            )
            
            if not row:
                logger.warning(f"Authorization code verification failed: code not found for client {client_id}")
                raise ValueError("invalid_grant: code not found")
                
            # Check if code is already used
            if row.used_at is not None:
                logger.warning(f"Authorization code verification failed: code already used (ID: {row.code_id})")
                raise ValueError("invalid_grant: code already used")
                
            # Check if code is revoked
            if row.revoked:
                logger.warning(f"Authorization code verification failed: code revoked (ID: {row.code_id})")
                raise ValueError("invalid_grant: code revoked")
                
            # Check if code is expired
            now = now or datetime.utcnow()
            if row.expires_at < now:
                expiry_time = row.expires_at.strftime("%Y-%m-%d %H:%M:%S UTC")
                current_time = now.strftime("%Y-%m-%d %H:%M:%S UTC")
                logger.warning(f"Authorization code verification failed: code expired at {expiry_time}, current time is {current_time} (ID: {row.code_id})")
                raise ValueError("invalid_grant: code expired")
                
            # Check if redirect_uri matches
            if row.redirect_uri != redirect_uri:
                logger.warning(f"Authorization code verification failed: redirect_uri mismatch, expected '{row.redirect_uri}', got '{redirect_uri}' (ID: {row.code_id})")
                raise ValueError("invalid_grant: redirect_uri mismatch")
                
            logger.info(f"Authorization code verification successful (ID: {row.code_id})")
            return row
            
        except SQLAlchemyError as e:
            err_msg = f"Database error verifying authorization code: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to verify authorization code: {str(e)}") from e
            
        except ValueError as e:
            # Re-raise ValueError exceptions we've created (with proper OAuth error codes)
            raise
            
        except Exception as e:
            err_msg = f"Unexpected error verifying authorization code: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to verify authorization code: {str(e)}") from e

    @classmethod
    def consume(cls, row: "AuthorizationCode") -> None:
        """Mark code as used (one-time). Commit immediately."""
        if not row:
            logger.error("Cannot consume authorization code: row is None")
            raise ValueError("Authorization code row is required")
            
        try:
            # Check if already used
            if row.used_at is not None:
                logger.warning(f"Authorization code already consumed (ID: {row.code_id})")
                return
                
            # Mark as used
            row.used_at = datetime.utcnow()
            db_session.commit()
            logger.info(f"Authorization code consumed successfully (ID: {row.code_id})")
            
        except SQLAlchemyError as e:
            db_session.rollback()
            err_msg = f"Database error consuming authorization code: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to consume authorization code: {str(e)}") from e
            
        except Exception as e:
            db_session.rollback()
            err_msg = f"Unexpected error consuming authorization code: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to consume authorization code: {str(e)}") from e

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """Convert authorization code to dictionary representation."""
        try:
            return {
                "code_id": self.code_id,
                "client_id": self.client_id,
                "user_id": self.user_id,
                "scope": self.scope,
                "redirect_uri": self.redirect_uri,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "expires_at": self.expires_at.isoformat() if self.expires_at else None,
                "used_at": self.used_at.isoformat() if self.used_at else None,
                "revoked": self.revoked,
                "code_challenge_method": self.code_challenge_method,
            }
        except Exception as e:
            logger.error(f"Error converting authorization code to dict (ID: {self.code_id}): {str(e)}")
            # Return a minimal dict with just the ID if there's an error
            return {"code_id": self.code_id, "error": str(e)}