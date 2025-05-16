"""Mock IssuedToken class for testing."""
import uuid
from datetime import datetime, timedelta

class MockIssuedToken:
    """Mock IssuedToken class for testing."""
    _tokens = {}
    
    def __init__(self, token_id=None, client_id=None, scope=None, granted_tools=None, 
                 task_id=None, agent_instance_id=None, agent_type=None, agent_model=None, 
                 agent_provider=None, agent_version=None, delegator_sub=None, 
                 delegation_chain=None, delegation_purpose=None, delegation_constraints=None,
                 parent_task_id=None, task_description=None, scope_inheritance_type=None,
                 code_challenge=None, code_challenge_method=None, launch_reason=None,
                 launched_by=None, agent_capabilities=None, agent_trust_level=None,
                 agent_attestation=None, agent_context_id=None):
        """Initialize a mock token."""
        self.token_id = token_id or str(uuid.uuid4())
        self.client_id = client_id
        self.scope = ' '.join(scope) if isinstance(scope, list) else scope
        self.scopes = self.scope
        self.granted_tools = ' '.join(granted_tools) if isinstance(granted_tools, list) else granted_tools or ''
        self.task_id = task_id or str(uuid.uuid4())
        self.agent_instance_id = agent_instance_id or str(uuid.uuid4())
        self.agent_type = agent_type
        self.agent_model = agent_model
        self.agent_provider = agent_provider
        self.agent_version = agent_version
        self.delegator_sub = delegator_sub
        self.delegation_chain = delegation_chain
        self.delegation_purpose = delegation_purpose
        self.delegation_constraints = delegation_constraints
        self.parent_task_id = parent_task_id
        self.task_description = task_description
        self.scope_inheritance_type = scope_inheritance_type or 'restricted'
        self.code_challenge = code_challenge
        self.code_challenge_method = code_challenge_method
        self.launch_reason = launch_reason
        self.launched_by = launched_by
        self.agent_capabilities = agent_capabilities
        self.agent_trust_level = agent_trust_level
        self.agent_attestation = agent_attestation
        self.agent_context_id = agent_context_id
        
        self.issued_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(hours=1)
        self.is_revoked = False
        self.revoked_at = None
        self.revocation_reason = None
        self.access_token_hash = "mock_access_token_hash"
        self.refresh_token_hash = "mock_refresh_token_hash"
        
        self.agent = type('obj', (object,), {
            'is_active': True,
            'roles': []
        })
        
        MockIssuedToken._tokens[self.token_id] = self
    
    @classmethod
    def create(cls, client_id, scope, granted_tools=None, task_id=None, agent_instance_id=None,
               agent_type=None, agent_model=None, agent_provider=None, agent_version=None,
               delegator_sub=None, delegation_chain=None, delegation_purpose=None,
               delegation_constraints=None, parent_task_id=None, task_description=None,
               scope_inheritance_type=None, code_challenge=None, code_challenge_method=None,
               launch_reason=None, launched_by=None, agent_capabilities=None,
               agent_trust_level=None, agent_attestation=None, agent_context_id=None):
        """Create a new token."""
        token_id = str(uuid.uuid4())
        access_token = f"mock_access_token_{token_id}"
        refresh_token = f"mock_refresh_token_{token_id}"
        
        token = cls(
            token_id=token_id,
            client_id=client_id,
            scope=scope,
            granted_tools=granted_tools,
            task_id=task_id,
            agent_instance_id=agent_instance_id,
            agent_type=agent_type,
            agent_model=agent_model,
            agent_provider=agent_provider,
            agent_version=agent_version,
            delegator_sub=delegator_sub,
            delegation_chain=delegation_chain,
            delegation_purpose=delegation_purpose,
            delegation_constraints=delegation_constraints,
            parent_task_id=parent_task_id,
            task_description=task_description,
            scope_inheritance_type=scope_inheritance_type,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            launch_reason=launch_reason,
            launched_by=launched_by,
            agent_capabilities=agent_capabilities,
            agent_trust_level=agent_trust_level,
            agent_attestation=agent_attestation,
            agent_context_id=agent_context_id
        )
        
        return token, access_token, refresh_token
    
    @classmethod
    def query(cls):
        """Mock query method."""
        class MockQuery:
            @classmethod
            def filter_by(cls, **kwargs):
                """Mock filter_by method."""
                class MockFilterResult:
                    @classmethod
                    def first(cls):
                        """Mock first method."""
                        for token in MockIssuedToken._tokens.values():
                            match = True
                            for key, value in kwargs.items():
                                if getattr(token, key, None) != value:
                                    match = False
                                    break
                            if match:
                                return token
                        return None
                    
                    @classmethod
                    def all(cls):
                        """Mock all method."""
                        results = []
                        for token in MockIssuedToken._tokens.values():
                            match = True
                            for key, value in kwargs.items():
                                if getattr(token, key, None) != value:
                                    match = False
                                    break
                            if match:
                                results.append(token)
                        return results
                
                return MockFilterResult
            
            @classmethod
            def get(cls, token_id):
                """Mock get method."""
                return MockIssuedToken._tokens.get(token_id)
        
        return MockQuery
    
    @classmethod
    def delete_by_id(cls, token_id):
        """Delete a token by its ID."""
        if token_id in cls._tokens:
            del cls._tokens[token_id]
            return True
        return False
    
    def is_valid(self):
        """Check if the token is valid."""
        from datetime import datetime
        return not self.is_revoked and self.expires_at > datetime.utcnow()
    
    def revoke(self, reason=None, _cascade=False):
        """Revoke the token."""
        from datetime import datetime
        self.is_revoked = True
        self.revoked_at = datetime.utcnow()
        self.revocation_reason = reason
        return True
