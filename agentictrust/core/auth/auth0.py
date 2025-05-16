from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from fastapi import HTTPException
from agentictrust.utils.logger import logger

auth0_config = {
    'client_id': None,  # Will be loaded from environment
    'client_secret': None,  # Will be loaded from environment
    'api_base_url': None,  # Will be constructed from domain
    'access_token_url': None,  # Will be constructed from domain
    'authorize_url': None,  # Will be constructed from domain
    'client_kwargs': {
        'scope': 'openid profile email',
    },
}

oauth = OAuth()

def configure_auth0(domain, client_id, client_secret):
    """Configure Auth0 with provided credentials."""
    global auth0_config
    
    auth0_config['client_id'] = client_id
    auth0_config['client_secret'] = client_secret
    auth0_config['api_base_url'] = f'https://{domain}'
    auth0_config['access_token_url'] = f'https://{domain}/oauth/token'
    auth0_config['authorize_url'] = f'https://{domain}/authorize'
    
    oauth.register(
        name='auth0',
        **auth0_config
    )
    
    logger.info(f"Auth0 client configured with domain: {domain}")

async def verify_auth0_token(token, domain):
    """Verify Auth0 token and extract user information."""
    try:
        jwks_url = f'https://{domain}/.well-known/jwks.json'
        
        from authlib.jose import jwt
        jwks = await oauth.auth0.get(jwks_url)
        
        claims = jwt.decode(token, jwks)
        claims.validate()
        
        return claims
    except Exception as e:
        logger.error(f"Error verifying Auth0 token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def extract_user_from_claims(claims):
    """Extract user information from Auth0 claims."""
    auth0_id = claims.get('sub')
    email = claims.get('email')
    name = claims.get('name')
    picture = claims.get('picture')
    
    return {
        'auth0_id': auth0_id,
        'email': email,
        'name': name,
        'picture': picture,
        'metadata': {
            'nickname': claims.get('nickname'),
            'locale': claims.get('locale'),
            'updated_at': claims.get('updated_at'),
        }
    }
