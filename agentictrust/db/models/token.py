import uuid
import os
import json
import traceback
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import jwt
from werkzeug.security import generate_password_hash
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from agentictrust.db import Base, db_session
from agentictrust.config import Config
from agentictrust.utils.keys import get_private_key
from agentictrust.db.models.audit.token_audit import TokenAuditLog

from agentictrust.utils.logger import logger

class IssuedToken(Base):
    """Model for issued OAuth tokens."""
    __tablename__ = 'issued_tokens'
    
    token_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String(36), ForeignKey('agents.client_id'), nullable=False)
    
    # Agent identity linked to this specific token issuance
    agent_instance_id = Column(String(100), nullable=False) # Added explicit column

    # Token values (hashed for security)
    access_token_hash = Column(String(256), nullable=False)
    refresh_token_hash = Column(String(256), nullable=True)
    
    # PKCE fields for OAuth 2.1
    code_challenge = Column(String(128), nullable=True)
    code_challenge_method = Column(String(10), nullable=True)
    authorization_code = Column(String(100), nullable=True)
    authorization_code_hash = Column(String(256), nullable=True)
    
    # Token metadata
    scopes = Column(Text, nullable=False)  # Space-separated scope strings
    granted_tools = Column(Text, nullable=False)  # Space-separated tool IDs
    scope_inheritance_type = Column(String(20), default='restricted')
    issued_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
    revocation_reason = Column(String(100), nullable=True)
    
    # Parent token tracking for delegation
    parent_token_id = Column(String(36), ForeignKey('issued_tokens.token_id'), nullable=True)
    
    # Token context information
    task_id = Column(String(36), nullable=False)
    parent_task_id = Column(String(36), nullable=True)
    task_description = Column(Text, nullable=True)

    # --- OIDC-A Claims Storage --- 
    # Core Agent Identity (snapshot at time of token issuance)
    agent_type = Column(String(100), nullable=True)          # Added
    agent_model = Column(String(100), nullable=True)         # Added
    agent_provider = Column(String(100), nullable=True)      # Added
    agent_version = Column(String(50), nullable=True)       # Added (Recommended claim)

    # Delegation and Authority
    delegator_sub = Column(String(255), nullable=True)      # Added (Subject ID of delegator)
    delegation_chain = Column(Text, nullable=True)          # Stored as JSON string
    delegation_purpose = Column(Text, nullable=True)
    delegation_constraints = Column(Text, nullable=True)    # Stored as JSON string

    # Capability, Trust, Attestation
    agent_capabilities = Column(Text, nullable=True)        # Stored as JSON array string
    agent_trust_level = Column(String(50), nullable=True)   # Changed to String for flexibility
    agent_attestation = Column(Text, nullable=True)         # Stored as JSON string
    agent_context_id = Column(String(100), nullable=True)

    # Launch context (new)
    launch_reason = Column(String(32), nullable=False, default="user_interactive")
    launched_by = Column(String(64), nullable=True)

    # Self-referential relationships for parent/child tokens
    parent_token = relationship(
        'IssuedToken',
        remote_side=[token_id],
        foreign_keys=[parent_token_id],
        back_populates='child_tokens'
    )
    child_tokens = relationship(
        'IssuedToken',
        back_populates='parent_token',
        lazy='select',
        cascade='all, delete-orphan',
        foreign_keys=[parent_token_id]
    )
    
    # Relationship with audit logs
    audit_logs = relationship(
        'TaskAuditLog', 
        backref='token', 
        lazy=True, 
        cascade='all, delete-orphan',
        primaryjoin="and_(IssuedToken.token_id == TaskAuditLog.token_id, not_(TaskAuditLog.token_id.startswith('error-')))",
        foreign_keys="TaskAuditLog.token_id"
    )
    
    @classmethod
    def create(cls, client_id, scope, granted_tools, task_id,
               agent_instance_id, # Now required
               # OIDC-A Required Claims
               agent_type, 
               agent_model, 
               agent_provider, 
               delegator_sub,
               # OIDC-A Optional/Recommended Claims
               agent_version=None,
               delegation_chain=None, 
               delegation_purpose=None, 
               delegation_constraints=None,
               agent_capabilities=None, 
               agent_trust_level=None, 
               agent_attestation=None, 
               agent_context_id=None,
               # Launch context
               launch_reason: str = "user_interactive", 
               launched_by: str | None = None,
               # Other parameters
               task_description=None, parent_task_id=None, parent_token_id=None,
               scope_inheritance_type='restricted', expires_in=None,
               code_challenge=None, code_challenge_method=None) -> Tuple["IssuedToken", str, str]:
        """Create a new token with generated access and refresh tokens.
        
        Args:
            client_id: Agent client ID
            scope: List of scope strings or space-separated scope string
            granted_tools: List of tool IDs granted to this token
            task_id: Task ID associated with this token
            agent_instance_id: Unique ID for this agent instance
            agent_type: Type of agent (OIDC-A claim)
            agent_model: Model of agent (OIDC-A claim)
            agent_provider: Provider of agent (OIDC-A claim)
            delegator_sub: Subject ID of delegator (OIDC-A claim)
            agent_version: Version of agent (OIDC-A claim)
            delegation_chain: Chain of delegation (OIDC-A claim)
            delegation_purpose: Purpose of delegation (OIDC-A claim)
            delegation_constraints: Constraints on delegation (OIDC-A claim)
            agent_capabilities: Capabilities of agent (OIDC-A claim)
            agent_trust_level: Trust level of agent (OIDC-A claim)
            agent_attestation: Attestation of agent (OIDC-A claim)
            agent_context_id: Context ID of agent (OIDC-A claim)
            launch_reason: Reason for launching the agent
            launched_by: Entity that launched the agent
            task_description: Description of the task
            parent_task_id: ID of the parent task
            parent_token_id: ID of the parent token
            scope_inheritance_type: Type of scope inheritance
            expires_in: Token expiry time delta
            code_challenge: PKCE code challenge
            code_challenge_method: PKCE code challenge method
            
        Returns:
            Tuple of (token_object, access_token_string, refresh_token_string)
            
        Raises:
            ValueError: For validation errors
            RuntimeError: For database or token generation errors
        """
        # Import here to avoid circular imports
        from agentictrust.db.models.audit.token_audit import TokenAuditLog
        from agentictrust.db.models.audit.task_audit import TaskAuditLog
        from agentictrust.db.models.audit.policy_audit import PolicyAuditLog
        from agentictrust.db.models.audit.scope_audit import ScopeAuditLog
        
        # Validate required parameters
        if not client_id:
            logger.error("Cannot create token: client_id is required")
            raise ValueError("client_id is required")
            
        if not task_id:
            logger.error("Cannot create token: task_id is required")
            raise ValueError("task_id is required")
            
        if not agent_instance_id:
            logger.error("Cannot create token: agent_instance_id is required")
            raise ValueError("agent_instance_id is required")
            
        # Validate required OIDC-A claims
        if not agent_type:
            logger.error("Cannot create token: agent_type is required")
            raise ValueError("agent_type is required")
            
        if not agent_model:
            logger.error("Cannot create token: agent_model is required")
            raise ValueError("agent_model is required")
            
        if not agent_provider:
            logger.error("Cannot create token: agent_provider is required")
            raise ValueError("agent_provider is required")
            
        if not delegator_sub:
            logger.error("Cannot create token: delegator_sub is required")
            raise ValueError("delegator_sub is required")
        
        try:
            # Set expiry time (default from config if not specified)
            if not expires_in:
                expires_in = timedelta(hours=int(os.environ.get('ACCESS_TOKEN_EXPIRY_HOURS', 1)))
                
            expires_at = datetime.utcnow() + expires_in
            
            # Convert scope to list if it's a string
            if isinstance(scope, str):
                scope = [s.strip() for s in scope.split(' ') if s.strip()]
                
            # Ensure we have at least one scope
            if not scope:
                logger.error("Cannot create token: at least one scope is required")
                raise ValueError("At least one scope is required")
                
            # Ensure granted_tools is a list
            if not isinstance(granted_tools, list):
                granted_tools = list(granted_tools) if granted_tools else []
                
            # Validate launch_reason
            valid_launch_reasons = ["user_interactive", "automated", "scheduled", "delegated"]
            if launch_reason not in valid_launch_reasons:
                logger.warning(f"Using non-standard launch_reason: {launch_reason}")
                
            # Validate scope_inheritance_type
            valid_inheritance_types = ["restricted", "full", "delegated"]
            if scope_inheritance_type not in valid_inheritance_types:
                logger.warning(f"Using non-standard scope_inheritance_type: {scope_inheritance_type}")
                scope_inheritance_type = "restricted"  # Default to restricted if invalid
                
            logger.info(f"Creating token for client {client_id} with {len(scope)} scopes and {len(granted_tools)} tools")
                
            # Generate JWT token with token_id in payload
            issued_at = datetime.now(timezone.utc)
            expires_in_hours = expires_in if expires_in is not None else Config.ACCESS_TOKEN_EXPIRY_HOURS
            
            # Create a unique token identifier
            token_uuid = str(uuid.uuid4())
            
            # Build access token payload
            access_token_payload = {
                'iss': Config.ISSUER,
                'sub': client_id,
                'aud': client_id, # Audience might be the resource server later
                'exp': expires_at,
                'iat': issued_at,
                'nbf': issued_at,
                'jti': token_uuid, # Unique token identifier
                'scope': ' '.join(scope),
                'agent_instance_id': agent_instance_id, # Include instance ID
                'token_use': 'access', # Explicitly state token type
                'launch_reason': launch_reason,
                'launched_by': launched_by,
            }
            
            # Get private key for signing
            try:
                private_key = get_private_key()
            except Exception as e:
                err_msg = f"Failed to retrieve private key for token signing: {str(e)}"
                logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
                raise RuntimeError(err_msg) from e
                
            # Sign the JWT token
            try:
                access_token = jwt.encode(
                    access_token_payload,
                    private_key,
                    algorithm='RS256',
                    headers={'kid': Config.JWKS_KID}
                )
            except Exception as e:
                err_msg = f"Failed to encode JWT token: {str(e)}"
                logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
                raise RuntimeError(err_msg) from e

            # Calculate hash of the access token
            access_token_hash = generate_password_hash(access_token)

            # Generate a unique Refresh Token
            raw_refresh_token = str(uuid.uuid4())

            # Prepare complex types for storage (JSON serialization if needed)
            try:
                if delegation_chain and isinstance(delegation_chain, (dict, list)):
                    delegation_chain = json.dumps(delegation_chain)
                    
                if delegation_constraints and isinstance(delegation_constraints, (dict, list)):
                    delegation_constraints = json.dumps(delegation_constraints)
                    
                if agent_capabilities and isinstance(agent_capabilities, (dict, list)):
                    agent_capabilities = json.dumps(agent_capabilities)
                    
                if agent_attestation and isinstance(agent_attestation, (dict, list)):
                    agent_attestation = json.dumps(agent_attestation)
            except json.JSONDecodeError as e:
                logger.error(f"JSON serialization error for token claims: {str(e)}")
                raise ValueError(f"Invalid format for JSON claim: {str(e)}") from e

            # Create the IssuedToken record
            new_token = cls(
                token_id=token_uuid,
                client_id=client_id,
                agent_instance_id=agent_instance_id,
                access_token_hash=access_token_hash,
                refresh_token_hash=raw_refresh_token,
                scopes=' '.join(scope) if isinstance(scope, list) else scope,
                granted_tools=' '.join(granted_tools) if isinstance(granted_tools, list) else granted_tools,
                task_id=task_id,
                parent_task_id=parent_task_id,
                parent_token_id=parent_token_id,
                task_description=task_description,
                scope_inheritance_type=scope_inheritance_type,
                issued_at=issued_at,
                expires_at=expires_at,
                # --- OIDC-A Claims Assignment --- 
                agent_type=agent_type,
                agent_model=agent_model,
                agent_provider=agent_provider,
                agent_version=agent_version,
                delegator_sub=delegator_sub,
                delegation_chain=delegation_chain, 
                delegation_purpose=delegation_purpose,
                delegation_constraints=delegation_constraints, 
                agent_capabilities=agent_capabilities, 
                agent_trust_level=agent_trust_level,
                agent_attestation=agent_attestation, 
                agent_context_id=agent_context_id,
                # Launch context
                launch_reason=launch_reason,
                launched_by=launched_by,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method
            )

            # Add token to session (but don't commit yet - caller will commit)
            db_session.add(new_token)
            
            # Log audit events
            audit_success = True
            audit_errors = []
            
            # Log ALL audit events in proper sequence
            try:
                # 1. First log token audit
                TokenAuditLog.log(
                    token_id=new_token.token_id,
                    client_id=new_token.client_id,
                    event_type="issued",
                    task_id=new_token.task_id,
                    parent_task_id=new_token.parent_task_id,
                    details={"scopes": scope, "granted_tools": granted_tools},
                    delegator_sub=delegator_sub,
                    delegation_chain=delegation_chain if isinstance(delegation_chain, list) else None,
                )
            except Exception as e:
                audit_success = False
                audit_errors.append(f"TokenAuditLog failed: {str(e)}")
                logger.error(f"Failed to log token audit: {str(e)}\nTrace: {traceback.format_exc()}")

            try:
                # 2. Then log task audit
                TaskAuditLog.log_event(
                    client_id=new_token.client_id,
                    token_id=new_token.token_id,
                    access_token_hash=new_token.access_token_hash,
                    task_id=new_token.task_id,
                    parent_task_id=new_token.parent_task_id,
                    event_type="token_created",
                    status="success",
                    details={"scopes": scope, "granted_tools": granted_tools},
                )
            except Exception as e:
                audit_success = False
                audit_errors.append(f"TaskAuditLog failed: {str(e)}")
                logger.error(f"Failed to log task audit: {str(e)}\nTrace: {traceback.format_exc()}")

            try:
                # 3. Then log policy audit
                PolicyAuditLog.log(
                    client_id=new_token.client_id,
                    action="token_issued",
                    decision="success",
                    resource_type="token",
                    task_id=new_token.task_id,
                    parent_task_id=new_token.parent_task_id,
                    details={"scopes": scope, "granted_tools": granted_tools}
                )
            except Exception as e:
                audit_success = False
                audit_errors.append(f"PolicyAuditLog failed: {str(e)}")
                logger.error(f"Failed to log policy audit: {str(e)}\nTrace: {traceback.format_exc()}")

            try:
                # 4. Finally log scope audits
                for scope_name in scope:
                    ScopeAuditLog.log(
                        scope_id=scope_name,
                        client_id=new_token.client_id,
                        action="granted",
                        task_id=new_token.task_id,
                        parent_task_id=new_token.parent_task_id,
                        details={"token_id": new_token.token_id}
                    )
            except Exception as e:
                audit_success = False
                audit_errors.append(f"ScopeAuditLog failed: {str(e)}")
                logger.error(f"Failed to log scope audit: {str(e)}\nTrace: {traceback.format_exc()}")

            # Log summary of audit status
            if not audit_success:
                logger.error(f"Some token issuance audit logs failed for {new_token.token_id}: {', '.join(audit_errors)}")
            else:
                logger.info(f"Successfully logged all audit events for token {new_token.token_id}")

            # Final logging for token creation
            expiry_time = expires_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            logger.info(f"Successfully created token for client {client_id}, expires at {expiry_time} (ID: {token_uuid})")

            # Return the DB object (already added to session), the signed JWT access token, and the raw refresh token
            return new_token, access_token, raw_refresh_token
            
        except SQLAlchemyError as e:
            db_session.rollback()  # Rollback on database errors
            err_msg = f"Database error creating token for client {client_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
            
        except Exception as e:
            # If this isn't a ValueError we raised during validation, wrap it
            if not isinstance(e, ValueError) or "required" not in str(e):
                err_msg = f"Unexpected error creating token for client {client_id}: {str(e)}"
                logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
                raise RuntimeError(err_msg) from e
            raise  # Re-raise validation errors

    def revoke(self, reason: Optional[str] = None, *, _cascade: bool = False) -> None:
        """Mark this token as revoked and optionally record a reason.

        Parameters
        ----------
        reason: Optional[str]
            Textual explanation for why the token is revoked.
        _cascade: bool
            Internal flag used by `revoke_children` to avoid duplicate audit
            logs when this method is invoked recursively.
        """
        from datetime import datetime as _dt

        # If already revoked, nothing to do –
        if self.is_revoked:
            return

        self.is_revoked = True
        self.revoked_at = _dt.utcnow()
        if reason:
            self.revocation_reason = reason

        # Persist changes – the outer caller (e.g., OAuthEngine) will commit.
        # But we add the object to the session so that flush/commit works.
        db_session.add(self)

        # Only create audit logs for the root call (avoid duplicates for children)
        if not _cascade:
            try:
                # 1. First token audit
                TokenAuditLog.log(
                    token_id=self.token_id,
                    client_id=self.client_id,
                    event_type="revoked",
                    task_id=self.task_id,
                    parent_task_id=self.parent_task_id,
                    details={"reason": reason} if reason else {},
                    delegator_sub=self.delegator_sub,
                    delegation_chain=None,
                )
                
                # 2. Add secondary token_revoked event
                TokenAuditLog.log(
                    token_id=self.token_id,
                    client_id=self.client_id,
                    event_type="token_revoked",
                    task_id=self.task_id,
                    parent_task_id=self.parent_task_id,
                    details={"revoked_children": False}, # No children by default
                    delegator_sub=self.delegator_sub,
                    delegation_chain=None,
                )
                
                # 3. Task audit
                from agentictrust.db.models.audit.task_audit import TaskAuditLog
                TaskAuditLog.log_event(
                    client_id=self.client_id,
                    token_id=self.token_id,
                    access_token_hash="N/A", # Not needed for revocation
                    task_id=self.task_id,
                    parent_task_id=self.parent_task_id,
                    event_type="token_revoked",
                    status="success",
                    details={"revoked_children": False}, # No children by default
                )
            except Exception as _e:
                # Do not break revocation if audit logging fails
                logger.error(f"Failed to log token revocation audit for {self.token_id}: {_e}", exc_info=True)

    def revoke_children(self, reason: Optional[str] = None) -> None:
        """Recursively revoke all descendant tokens of this token."""
        children_revoked = False
        
        # Iterate through direct children first
        for child in list(self.child_tokens):
            children_revoked = True
            # Revoke child (cascade flag to suppress duplicate audit logs)
            child.revoke(reason=reason, _cascade=True)
            # Recursively revoke its children
            child.revoke_children(reason=reason)

        # Ensure children updates are persisted (outer commit will finalise)
        db_session.flush()
        
        # Log the fact that children were revoked (if any)
        if children_revoked:
            try:
                # 1. First token audit with revoked_children=True
                TokenAuditLog.log(
                    token_id=self.token_id,
                    client_id=self.client_id,
                    event_type="token_revoked",
                    task_id=self.task_id,
                    parent_task_id=self.parent_task_id,
                    details={"revoked_children": True},
                    delegator_sub=self.delegator_sub,
                    delegation_chain=None,
                )
                
                # 2. Task audit with revoked_children=True
                from agentictrust.db.models.audit.task_audit import TaskAuditLog
                TaskAuditLog.log_event(
                    client_id=self.client_id,
                    token_id=self.token_id,
                    access_token_hash="N/A", # Not needed for revocation
                    task_id=self.task_id,
                    parent_task_id=self.parent_task_id,
                    event_type="token_revoked",
                    status="success",
                    details={"revoked_children": True},
                )
            except Exception as _e:
                # Do not break revocation if audit logging fails
                logger.error(f"Failed to log child token revocation audit for {self.token_id}: {_e}", exc_info=True)

    def refresh(
            self,
            requested_scope_str: Optional[str] = None,
            launch_reason: Optional[str] = None,
            launched_by: Optional[str] = None,
        ) -> tuple['IssuedToken', str, str]:
        """Refresh this token (which must be a valid refresh token).

        Revokes the current token and issues a new access/refresh token pair
        with potentially narrowed scopes. Logs audit events for revocation
        and issuance.

        Parameters
        ----------
        requested_scope_str : Optional[str]
            Space-separated string of scopes requested for the new token.
            If None or empty, the scopes from the original token are used.
            The new scopes MUST be a subset of the original scopes.
        launch_reason: Optional[str]
            Reason for launching the new token.
        launched_by: Optional[str]
            The entity that launched the new token.

        Returns
        -------
        tuple[IssuedToken, str, str]
            A tuple containing the new IssuedToken database object,
            the new JWT access token string, and the new raw refresh token string.

        Raises
        ------
        ValueError
            If the requested scopes are invalid or broader than the original.
        """
        from agentictrust.db.models.audit.token_audit import TokenAuditLog # Local import

        # Validate requested scopes
        original_scopes = set(self.scopes.split()) if self.scopes else set()
        if requested_scope_str:
            requested_scopes = set(requested_scope_str.split())
            if not requested_scopes.issubset(original_scopes):
                raise ValueError("invalid_scope: Requested scopes exceed original grant.")
        else:
            requested_scopes = original_scopes

        # 1. Revoke the old token
        self.revoke(reason="Used for refresh")
        # Audit log for revocation is handled within self.revoke()

        # 2. Create the new token pair using the old token's details
        # Note: create() handles its own "issued" audit log.
        new_token_obj, new_access_token, new_refresh_token = IssuedToken.create(
            client_id=self.client_id,
            scope=list(requested_scopes), # Pass as list
            granted_tools=self.granted_tools.split() if self.granted_tools else [], # Pass as list
            task_id=self.task_id, # Inherit task context
            agent_instance_id=self.agent_instance_id,
            agent_type=self.agent_type,
            agent_model=self.agent_model,
            agent_provider=self.agent_provider,
            delegator_sub=self.delegator_sub,
            agent_version=self.agent_version,
            delegation_chain=self.delegation_chain,
            delegation_purpose=self.delegation_purpose,
            delegation_constraints=self.delegation_constraints,
            agent_capabilities=self.agent_capabilities,
            agent_trust_level=self.agent_trust_level,
            agent_attestation=self.agent_attestation,
            agent_context_id=self.agent_context_id,
            # Launch context
            launch_reason=launch_reason or self.launch_reason,
            launched_by=launched_by or self.launched_by,
            task_description=self.task_description,
            parent_task_id=self.parent_task_id, # Inherit parent task
            parent_token_id=self.parent_token_id, # Inherit original parent token ID
            scope_inheritance_type=self.scope_inheritance_type,
            # expires_in will default in create()
        )

        # The caller (OAuthEngine) is responsible for db_session.commit()
        return new_token_obj, new_access_token, new_refresh_token

    def to_dict(self, include_children=False, include_parent=False):
        """Serialize the token object to a dictionary."""
        logger.debug(f"Serializing token {self.token_id} to dict. Include children: {include_children}, include parent: {include_parent}")
        try: # Wrap the serialization logic
            token_data = {
                'token_id': self.token_id,
                'client_id': self.client_id,
                'agent_instance_id': self.agent_instance_id,
                'scopes': self.scopes.split(' ') if self.scopes else [],
                'granted_tools': self.granted_tools.split(' ') if self.granted_tools else [],
                'scope_inheritance_type': self.scope_inheritance_type,
                'issued_at': self.issued_at.isoformat() if self.issued_at else None,
                'expires_at': self.expires_at.isoformat() if self.expires_at else None,
                'is_revoked': self.is_revoked,
                'revoked_at': self.revoked_at.isoformat() if self.revoked_at else None,
                'revocation_reason': self.revocation_reason,
                'parent_token_id': self.parent_token_id,
                'task_id': self.task_id,
                'parent_task_id': self.parent_task_id,
                'task_description': self.task_description,
                
                # OIDC-A Claims
                'agent_type': self.agent_type,
                'agent_model': self.agent_model,
                'agent_provider': self.agent_provider,
                'agent_version': self.agent_version,
                'delegator_sub': self.delegator_sub,
                # For JSON string fields, return as-is for now (parsing could be added)
                'delegation_chain': self.delegation_chain,
                'delegation_purpose': self.delegation_purpose,
                'delegation_constraints': self.delegation_constraints,
                'agent_capabilities': self.agent_capabilities,
                'agent_trust_level': self.agent_trust_level,
                'agent_attestation': self.agent_attestation,
                'agent_context_id': self.agent_context_id,
                'launch_reason': self.launch_reason,
                'launched_by': self.launched_by,
                
                # Add calculated fields if useful
                'is_valid': not self.is_revoked and (self.expires_at > datetime.utcnow() if self.expires_at else False)
            }
            logger.debug(f"Base token data created for {self.token_id}")

            # Optionally include relationships (careful with recursion)
            if include_children:
                logger.debug(f"Including child tokens for {self.token_id}")
                try:
                    # Handle potential lazy loading issues or recursion depth
                    token_data['child_tokens'] = [child.to_dict(include_children=False, include_parent=False) for child in self.child_tokens]
                    logger.debug(f"Successfully serialized {len(token_data['child_tokens'])} child tokens for {self.token_id}")
                except Exception as e:
                    logger.error(f"Error serializing child tokens for {self.token_id}: {e}", exc_info=True)
                    token_data['child_tokens'] = [] # Or some indicator of error/incompleteness

            if include_parent and self.parent_token:
                logger.debug(f"Including parent token for {self.token_id}")
                try:
                    token_data['parent_token'] = self.parent_token.to_dict(include_children=False, include_parent=False)
                    logger.debug(f"Successfully serialized parent token for {self.token_id}")
                except Exception as e:
                     logger.error(f"Error serializing parent token for {self.token_id}: {e}", exc_info=True)
                     token_data['parent_token'] = None

            logger.debug(f"Finished serializing token {self.token_id}")
            return token_data
        except Exception as e_dict: # Catch errors during serialization itself
            logger.error(f"Error within to_dict for token {self.token_id}: {e_dict}", exc_info=True)
            raise # Re-raise to be caught by core_list_tokens or router

    def __repr__(self):
        return f'<IssuedToken(token_id={self.token_id}, client_id={self.client_id}, task_id={self.task_id}, valid={not self.is_revoked and self.expires_at > datetime.utcnow()})>'

    def is_valid(self) -> bool:
        """Return whether the token is still valid (not revoked and not expired)."""
        return not self.is_revoked and (self.expires_at > datetime.utcnow() if self.expires_at else False)

    def verify(self, source_ip=None) -> bool:
        """Verify if token is still valid, alias of is_valid."""
        return self.is_valid()