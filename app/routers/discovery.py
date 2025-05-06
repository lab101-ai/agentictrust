from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.config import Config
from app.utils.keys import get_public_jwks

router = APIRouter(prefix="/api", tags=["discovery"])

@router.get("/.well-known/openid-configuration")
def openid_configuration():
    issuer = Config.ISSUER
    discovery = {
        "issuer": issuer,
        "jwks_uri": f"{issuer}/.well-known/jwks.json",
        "token_endpoint": f"{issuer}/api/oauth/token",
        "revocation_endpoint": f"{issuer}/api/oauth/revoke",
        "introspection_endpoint": f"{issuer}/api/oauth/introspect",
        # Standard OIDC fields
        "response_types_supported": ["token", "id_token"], # Adjust if supporting code flow
        "subject_types_supported": ["public", "pairwise"], # Added pairwise, check if implemented
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": ["openid", "profile", "email", "agent:read", "agent:write"], # Example agent scopes
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "claims_supported": [
            "sub",
            "iss",
            "aud",
            "exp",
            "iat",
            "jti",
            # OIDC-A Core Agent Claims (Proposal 2.1)
            "agent_type",
            "agent_model",
            "agent_version", # Assuming supported
            "agent_provider",
            "agent_instance_id",
            # OIDC-A Delegation Claims (Proposal 2.2)
            "delegator_sub",
            "delegation_chain",
            "delegation_purpose",
            "delegation_constraints",
            # OIDC-A Capability/Trust/Attestation Claims (Proposal 2.3)
            "agent_capabilities",
            "agent_trust_level",
            "agent_attestation",
            "agent_context_id"
        ],
        "grant_types_supported": ["client_credentials", "refresh_token"],
        # OIDC-A Specific Discovery (Proposal 3.2 - Add more as implemented)
        "agent_claims_supported": [
            "agent_type", "agent_model", "agent_version", "agent_provider",
            "agent_instance_id", "delegator_sub", "delegation_chain",
            "delegation_purpose", "delegation_constraints", "agent_capabilities",
            "agent_trust_level", "agent_attestation", "agent_context_id"
        ],
        "attestation_formats_supported": ["jwt"], # Example: Specify supported formats
        # "delegation_chain_validation_endpoint": f"{issuer}/api/oauth/validate_delegation", # Example if endpoint exists
        "code_challenge_methods_supported": ["S256", "plain"] # If supporting PKCE
    }
    return JSONResponse(discovery)

@router.get("/.well-known/jwks.json")
def jwks():
    jwks = get_public_jwks()
    return JSONResponse(jwks)
