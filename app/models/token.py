import uuid
import secrets
from datetime import datetime, timedelta
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class IssuedToken(db.Model):
    """Model for issued OAuth tokens."""
    __tablename__ = 'issued_tokens'
    
    token_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('agents.client_id'), nullable=False)
    
    # Token values (hashed for security)
    access_token_hash = db.Column(db.String(256), nullable=False)
    refresh_token_hash = db.Column(db.String(256), nullable=True)
    
    # PKCE fields for OAuth 2.1
    code_challenge = db.Column(db.String(128), nullable=True)
    code_challenge_method = db.Column(db.String(10), nullable=True)
    authorization_code = db.Column(db.String(100), nullable=True)
    authorization_code_hash = db.Column(db.String(256), nullable=True)
    
    # Token metadata
    scope = db.Column(db.JSON, nullable=False)
    granted_tools = db.Column(db.JSON, nullable=False)
    task_id = db.Column(db.String(36), nullable=False)
    parent_task_id = db.Column(db.String(36), nullable=True)
    parent_token_id = db.Column(db.String(36), db.ForeignKey('issued_tokens.token_id'), nullable=True)
    task_description = db.Column(db.Text, nullable=True)
    scope_inheritance_type = db.Column(db.String(20), default='restricted')
    
    # Token lifecycle
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_revoked = db.Column(db.Boolean, default=False)
    revoked_at = db.Column(db.DateTime, nullable=True)
    revocation_reason = db.Column(db.String(100), nullable=True)
    
    # Self-referential relationship for parent-child tokens
    child_tokens = db.relationship(
        'IssuedToken', 
        backref=db.backref('parent_token', remote_side=[token_id]),
        lazy=True,
        cascade='all, delete-orphan'
    )
    
    # Relationship with audit logs
    audit_logs = db.relationship(
        'TaskAuditLog', 
        backref='token', 
        lazy=True, 
        cascade='all, delete-orphan',
        primaryjoin="and_(IssuedToken.token_id == TaskAuditLog.token_id, not_(TaskAuditLog.token_id.startswith('error-')))",
        foreign_keys="TaskAuditLog.token_id"
    )
    
    @classmethod
    def create(cls, client_id, scope, granted_tools, task_id, 
              task_description=None, parent_task_id=None, parent_token_id=None,
              scope_inheritance_type='restricted', expires_in=None, 
              code_challenge=None, code_challenge_method=None):
        """Create a new token with generated access and refresh tokens."""
        
        # Set expiry time (default from config if not specified)
        if not expires_in:
            from flask import current_app
            expires_in = current_app.config.get('ACCESS_TOKEN_EXPIRY', timedelta(hours=1))
            
        expires_at = datetime.utcnow() + expires_in
        
        # Convert scope to list if it's a string
        if isinstance(scope, str):
            scope = [s.strip() for s in scope.split(' ') if s.strip()]
            
        # Ensure granted_tools is a list
        if not isinstance(granted_tools, list):
            granted_tools = list(granted_tools) if granted_tools else []
            
        # Create token record first with placeholder hash
        token = cls(
            token_id=str(uuid.uuid4()),
            client_id=client_id,
            access_token_hash="placeholder",
            refresh_token_hash="placeholder",
            scope=scope,
            granted_tools=granted_tools,
            task_id=task_id,
            parent_task_id=parent_task_id,
            parent_token_id=parent_token_id,
            task_description=task_description,
            scope_inheritance_type=scope_inheritance_type,
            expires_at=expires_at,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method
        )
        
        # Generate JWT token with token_id in payload
        # Add token to session and commit
        from flask import current_app
        import jwt
        try:
            db.session.add(token)
            db.session.commit()
            current_app.logger.debug(f"Created token {token.token_id} for client {client_id} and task {task_id}")
            
            # Create JWT token with all necessary information
            # Use exact datetime objects from token record for consistency
            current_time = token.issued_at
            current_timestamp = int(current_time.timestamp())
            expire_timestamp = int(token.expires_at.timestamp())
            
            # Debug timestamp calculation
            current_app.logger.debug(f"JWT Token timestamps: current_time={current_time.isoformat()}, expires_at={token.expires_at.isoformat()}")
            current_app.logger.debug(f"JWT Token timestamps (unix): iat={current_timestamp}, exp={expire_timestamp}")
            
            jwt_payload = {
                "token_id": token.token_id,
                "client_id": client_id,
                "task_id": task_id,
                "exp": expire_timestamp,
                "iat": current_timestamp,
                "nbf": current_timestamp,  # Not valid before current time
                "scope": scope,
                "granted_tools": granted_tools
            }
            
            # Create the actual JWT token
            access_token = jwt.encode(
                jwt_payload, 
                current_app.config.get('SECRET_KEY', 'default-secret'), 
                algorithm='HS256'
            )
            
            # For non-JWT applications, generate a refresh token
            refresh_token = secrets.token_urlsafe(48)
            
            # Update the token with the hashes
            token.access_token_hash = generate_password_hash(access_token)
            token.refresh_token_hash = generate_password_hash(refresh_token)
            db.session.commit()
            
            # Test token decoding to verify it's valid
            try:
                # Try decoding the token we just created to ensure it's valid
                test_decode = jwt.decode(
                    access_token,
                    current_app.config.get('SECRET_KEY', 'default-secret'),
                    algorithms=['HS256'],
                    options={"verify_nbf": False, "verify_iat": False}  # Skip timestamp verification for this test
                )
                current_app.logger.debug(f"JWT test decode successful: {test_decode}")
            except Exception as decode_err:
                current_app.logger.error(f"JWT test decode failed: {str(decode_err)}")
            
            # Debug token verification
            verification_check = check_password_hash(token.access_token_hash, access_token)
            if not verification_check:
                current_app.logger.error(f"CRITICAL: Token verification check failed immediately after creation!")
                db.session.rollback()
                raise ValueError("Token verification check failed after creation")
            
            # Log token creation success
            current_app.logger.info(f"Token created and verified successfully: {token.token_id}")
            
            return token, access_token, refresh_token
        except Exception as e:
            current_app.logger.error(f"Error creating token: {str(e)}", exc_info=True)
            db.session.rollback()
            raise
    
    @classmethod
    def create_authorization_code(cls, client_id, scope, granted_tools, task_id,
                                 code_challenge, code_challenge_method, 
                                 task_description=None, parent_task_id=None, parent_token_id=None,
                                 scope_inheritance_type='restricted', expires_in=None):
        """Create an authorization code with PKCE challenge."""
        
        # Generate authorization code
        authorization_code = secrets.token_urlsafe(24)
        authorization_code_hash = generate_password_hash(authorization_code)
        
        # Set short expiry time for auth code (10 minutes)
        if not expires_in:
            from flask import current_app
            expires_in = current_app.config.get('AUTHORIZATION_CODE_EXPIRY', timedelta(minutes=10))
            
        expires_at = datetime.utcnow() + expires_in
        
        # Create token record with auth code
        token = cls(
            client_id=client_id,
            authorization_code_hash=authorization_code_hash,
            scope=scope,
            granted_tools=granted_tools,
            task_id=task_id,
            parent_task_id=parent_task_id,
            parent_token_id=parent_token_id,
            task_description=task_description,
            scope_inheritance_type=scope_inheritance_type,
            expires_at=expires_at,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method
        )
        
        db.session.add(token)
        db.session.commit()
        
        # Return both the token object and the authorization code
        return token, authorization_code
        
    def exchange_code_for_tokens(self, code_verifier):
        """Exchange authorization code for access token using PKCE."""
        from flask import current_app
        import hashlib
        import base64
        
        # Verify code challenge
        if self.code_challenge_method == 'S256':
            # SHA256 hash the verifier
            hash_obj = hashlib.sha256(code_verifier.encode())
            calculated_challenge = base64.urlsafe_b64encode(hash_obj.digest()).decode().rstrip('=')
            is_valid = (calculated_challenge == self.code_challenge)
        elif self.code_challenge_method == 'plain':
            # Plain comparison
            is_valid = (code_verifier == self.code_challenge)
        else:
            is_valid = False
            
        if not is_valid:
            return False, "Invalid code verifier"
            
        # Generate new tokens
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(48)
        
        # Update token record
        self.access_token_hash = generate_password_hash(access_token)
        self.refresh_token_hash = generate_password_hash(refresh_token)
        self.authorization_code_hash = None  # Clear the used authorization code
        
        # Set standard token expiry
        expires_in = current_app.config.get('ACCESS_TOKEN_EXPIRY', timedelta(hours=1))
        self.expires_at = datetime.utcnow() + expires_in
        
        db.session.commit()
        
        return True, (access_token, refresh_token)

    def revoke(self, reason=None):
        """Revoke this token and optionally all child tokens."""
        self.is_revoked = True
        self.revoked_at = datetime.utcnow()
        self.revocation_reason = reason
        
        # Recursively revoke all child tokens
        for child_token in self.child_tokens:
            child_token.revoke(reason=f"Parent token revoked: {reason}")
            
        db.session.commit()
        
    def is_valid(self):
        """Check if token is valid (not expired, not revoked)."""
        return not self.is_revoked and self.expires_at > datetime.utcnow()
    
    def to_dict(self, include_children=False):
        """Convert token to dictionary representation."""
        data = {
            'token_id': self.token_id,
            'client_id': self.client_id,
            'scope': self.scope,
            'granted_tools': self.granted_tools,
            'task_id': self.task_id,
            'parent_task_id': self.parent_task_id,
            'parent_token_id': self.parent_token_id,
            'task_description': self.task_description,
            'scope_inheritance_type': self.scope_inheritance_type,
            'issued_at': self.issued_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'is_revoked': self.is_revoked,
            'is_valid': self.is_valid()
        }
        
        if self.revoked_at:
            data['revoked_at'] = self.revoked_at.isoformat()
            data['revocation_reason'] = self.revocation_reason
            
        if include_children:
            data['child_tokens'] = [child.to_dict() for child in self.child_tokens]
            
        return data

    def verify_against_parent_tokens(self, parent_tokens_data):
        """
        Verify this token against a list of parent tokens.
        
        Args:
            parent_tokens_data: List of dictionaries containing parent token information
                                Format: [{'token': 'token_str', 'task_id': 'task_id'}, ...]
                                
        Returns:
            Dictionary with verification results for each parent in the chain
        """
        if not parent_tokens_data:
            return {"success": True, "message": "No parent tokens to verify against"}
            
        from app.utils import verify_token, verify_task_lineage, verify_scope_inheritance
            
        results = {
            "success": True,
            "parent_verifications": []
        }
            
        # Get the current parent token
        current_parent = None
        if self.parent_token_id:
            current_parent = IssuedToken.query.get(self.parent_token_id)
            
        # Verify against provided parent tokens
        for parent_data in parent_tokens_data:
            parent_token_str = parent_data.get('token')
            parent_task_id = parent_data.get('task_id')
            
            # Skip if no token provided
            if not parent_token_str:
                continue
                
            parent_result = {
                "task_id": parent_task_id,
                "verified": False
            }
            
            # Verify token
            parent_token_obj = verify_token(parent_token_str)
            if not parent_token_obj:
                parent_result["error"] = "Invalid or expired parent token"
                results["parent_verifications"].append(parent_result)
                results["success"] = False
                continue
                
            # Store token_id for reference
            parent_result["token_id"] = parent_token_obj.token_id
                
            # Verify direct parent first (if this is a direct child)
            if current_parent and current_parent.token_id == parent_token_obj.token_id:
                parent_result["is_direct_parent"] = True
                
                # Verify task ID matches
                if parent_task_id and parent_token_obj.task_id != parent_task_id:
                    parent_result["error"] = "Parent token task_id mismatch"
                    results["parent_verifications"].append(parent_result)
                    results["success"] = False
                    continue
                    
                # Verify lineage
                if not verify_task_lineage(self, parent_token=parent_token_obj):
                    parent_result["error"] = "Task lineage verification failed"
                    results["parent_verifications"].append(parent_result)
                    results["success"] = False
                    continue
                    
                # Verify scope inheritance
                if not verify_scope_inheritance(self, parent_token_obj):
                    parent_result["error"] = "Scope inheritance verification failed"
                    results["parent_verifications"].append(parent_result)
                    results["success"] = False
                    continue
                    
                parent_result["verified"] = True
                results["parent_verifications"].append(parent_result)
                continue
                
            # For non-direct parents, verify if they're in the chain
            # Get full lineage of this token to see if the provided token is in the chain
            ancestors = []
            current = self
            while current.parent_token_id:
                ancestor = IssuedToken.query.get(current.parent_token_id)
                if not ancestor:
                    break
                ancestors.append(ancestor)
                current = ancestor
                
            # Check if this parent token is in the lineage
            found_in_lineage = False
            for ancestor in ancestors:
                if ancestor.token_id == parent_token_obj.token_id:
                    found_in_lineage = True
                    
                    # Verify task ID
                    if parent_task_id and ancestor.task_id != parent_task_id:
                        parent_result["error"] = f"Ancestor token task_id mismatch. Expected: {ancestor.task_id}, Got: {parent_task_id}"
                        results["parent_verifications"].append(parent_result)
                        results["success"] = False
                        found_in_lineage = False
                        break
                        
                    parent_result["is_ancestor"] = True
                    parent_result["verified"] = True
                    results["parent_verifications"].append(parent_result)
                    break
                    
            if not found_in_lineage and not parent_result.get("verified"):
                # This token is not in our lineage
                parent_result["error"] = "Token is not in the ancestry chain"
                parent_result["verified"] = False
                results["parent_verifications"].append(parent_result)
                results["success"] = False
                
        return results

    def has_tool_permission(self, tool_name):
        """
        Check if this token has permission to use a specific tool.
        
        Args:
            tool_name: The name of the tool to check
            
        Returns:
            Boolean indicating if the token has permission
        """
        return tool_name in self.granted_tools 