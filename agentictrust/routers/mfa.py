from fastapi import APIRouter, HTTPException, Body, Request, Depends
from typing import Dict, Any, Optional
from agentictrust.core.auth.mfa import MFAManager, MFAChallenge
from agentictrust.utils.logger import logger
from agentictrust.db import db_session
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/mfa", tags=["mfa"])

class SetupMFAResponse(BaseModel):
    """Response model for MFA setup."""
    secret: str
    qr_code: str
    provisioning_uri: str

class VerifyMFARequest(BaseModel):
    """Request model for MFA verification."""
    code: str = Field(..., description="TOTP code from authenticator app")

class MFAChallengeResponse(BaseModel):
    """Response model for MFA challenge creation."""
    challenge_id: str
    challenge_type: str
    expires_at: str

class VerifyChallengeRequest(BaseModel):
    """Request model for MFA challenge verification."""
    challenge_id: str = Field(..., description="ID of the MFA challenge")
    code: str = Field(..., description="TOTP code from authenticator app")

@router.post("/users/{user_id}/setup", response_model=SetupMFAResponse)
async def setup_mfa(user_id: str):
    """Set up MFA for a user."""
    try:
        from agentictrust.db.models.user import User
        user = User.query.get(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        setup_data = MFAManager.setup_totp(user)
        
        return SetupMFAResponse(**setup_data)
    except Exception as e:
        logger.error(f"Error setting up MFA: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users/{user_id}/verify")
async def verify_mfa(user_id: str, request: VerifyMFARequest):
    """Verify MFA code."""
    try:
        from agentictrust.db.models.user import User
        user = User.query.get(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        is_valid = MFAManager.verify_totp(user, request.code)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid MFA code")
        
        return {"verified": True, "mfa_enabled": user.mfa_enabled}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying MFA: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users/{user_id}/challenge", response_model=MFAChallengeResponse)
async def create_mfa_challenge(user_id: str, operation_type: str):
    """Create MFA challenge for critical operation."""
    try:
        from agentictrust.db.models.user import User
        user = User.query.get(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.mfa_enabled:
            raise HTTPException(status_code=400, detail="MFA not enabled for this user")
        
        challenge, challenge_data = MFAManager.create_challenge(user, operation_type)
        
        return MFAChallengeResponse(**challenge_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating MFA challenge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users/{user_id}/challenge/verify")
async def verify_mfa_challenge(user_id: str, request: VerifyChallengeRequest):
    """Verify MFA challenge."""
    try:
        is_valid = MFAManager.verify_challenge(request.challenge_id, request.code, user_id)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid MFA challenge or code")
        
        return {"verified": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying MFA challenge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
