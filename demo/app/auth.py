import os
import uuid
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
import jwt
from passlib.context import CryptContext
import requests

# Change relative imports to absolute imports
from .database import get_session
from .models import User, UserProfile

# OAuth2 scheme for token retrieval
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token", auto_error=False)

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Password hashing context - support both bcrypt and sha256_crypt
pwd_context = CryptContext(schemes=["sha256_crypt", "bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Authenticate user with hashed password
def authenticate_user(session: Session, username: str, password: str) -> User | None:
    user = session.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# Create JWT access token via AgenticTrust API
def create_access_token(data: dict, expires_delta: timedelta = None):
    # Extract username from data (subject claim)
    username = data.get("sub")
    if not username:
        raise ValueError("Missing 'sub' claim in token data")
        
    # Request client_credentials token from AgenticTrust
    try:
        payload = {
            "grant_type": "client_credentials",
            "client_id": os.getenv("AGENTICTRUST_CLIENT_ID"),
            "client_secret": os.getenv("AGENTICTRUST_CLIENT_SECRET"),
            "delegator_sub": username,  # Associate token with this user
            "agent_type": "webapp",
            "agent_model": "demo-app",
            "agent_provider": "demo-local",
            "agent_instance_id": f"demo-{uuid.uuid4()}",
            "scope": "read:basic",
        }
        
        resp = requests.post(
            "http://localhost:8000/api/oauth/token", 
            json=payload,
            timeout=5.0
        )
        
        if not resp.ok:
            # Fallback to local JWT creation if AgenticTrust is unavailable
            print(f"Error getting token from AgenticTrust: {resp.status_code} {resp.text}")
            to_encode = data.copy()
            expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
            to_encode.update({"exp": expire})
            return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            
        token_data = resp.json()
        return token_data["access_token"]
        
    except Exception as e:
        # Fallback to local JWT creation if AgenticTrust is unavailable
        print(f"Error connecting to AgenticTrust: {e}")
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Helper to resolve an AgenticTrust token to local User row (auto-create)
def _user_from_agentictrust_token(token_str: str, session: Session) -> User | None:
    """Return a `demo.app.models.User` (creating one if necessary) from a
    validated AgenticTrust access token. Returns None if token is invalid."""
    
    # Quick check - if token is using HS256 (our local tokens), skip AgenticTrust validation
    # This avoids log spam from the expected 'kid' missing errors
    try:
        header = jwt.get_unverified_header(token_str)
        if header.get('alg') == 'HS256':
            # This is a local token, not an AgenticTrust token
            return None
    except Exception:
        # If we can't even parse the header, it's definitely not valid
        return None
        
    # Call AgenticTrust API to verify token instead of direct library call
    try:
        response = requests.post(
            "http://localhost:8000/api/oauth/verify",
            json={"token": token_str},
            timeout=2.0
        )
        
        if response.status_code != 200:
            return None
            
        token_data = response.json()
        if not token_data.get("verified"):
            return None
            
        # Extract user information from token data
        user_sub = token_data.get("subject") or token_data.get("delegator_sub")
        if not user_sub:
            return None
    except Exception as e:
        print(f"Error verifying token with AgenticTrust API: {e}")
        return None

    # user_sub was already extracted from token_data above

    user = session.exec(select(User).where(User.username == user_sub)).first()
    if user:
        return user

    # Create a stub user so rest of demo app works
    user = User(username=user_sub, hashed_password=pwd_context.hash(""))
    session.add(user)
    session.commit()
    session.refresh(user)
    # Also create empty profile to satisfy joins in templates
    profile = UserProfile(user_id=user.id, first_name="", last_name="")
    session.add(profile)
    session.commit()
    return user

# Dependency to get current user from token
def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    # 1) Try AgenticTrust RS256 token verification first
    user = _user_from_agentictrust_token(token, session)
    if user:
        return user

    # 2) Fallback to legacy demo HS256 JWT for local login only
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    statement = (
        select(User)
        .where(User.username == username)
        .options(selectinload(User.profile))
    )
    user = session.exec(statement).first()
    if not user:
        raise credentials_exception
    return user

# Optional dependency that allows anonymous access
def get_optional_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    try:
        return get_current_user(token, session)
    except HTTPException:
        return None

# Token endpoint using OAuth2PasswordRequestForm
def create_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username or password")
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}