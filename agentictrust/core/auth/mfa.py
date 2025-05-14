import uuid
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from agentictrust.db import Base, db_session
from agentictrust.utils.logger import logger
from typing import Optional, Dict, Any, Tuple

class MFAChallenge(Base):
    """Model for MFA challenges."""
    __tablename__ = 'mfa_challenges'
    
    challenge_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.user_id'), nullable=False)
    challenge_type = Column(String(20), nullable=False)  # 'totp', 'sms', etc.
    challenge_data = Column(String(256), nullable=True)  # For TOTP: the expected code
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    operation_type = Column(String(50), nullable=True)  # Type of operation requiring MFA
    
    @classmethod
    def create(cls, user_id: str, challenge_type: str, challenge_data: str, 
               operation_type: Optional[str] = None, ttl_minutes: int = 10) -> 'MFAChallenge':
        """Create a new MFA challenge."""
        try:
            expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
            
            challenge = cls(
                user_id=user_id,
                challenge_type=challenge_type,
                challenge_data=challenge_data,
                operation_type=operation_type,
                expires_at=expires_at
            )
            
            db_session.add(challenge)
            db_session.commit()
            
            logger.info(f"Created MFA challenge for user {user_id} of type {challenge_type}")
            
            return challenge
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error creating MFA challenge: {str(e)}")
            raise
    
    def complete(self) -> None:
        """Mark challenge as completed."""
        self.completed = True
        self.completed_at = datetime.utcnow()
        db_session.commit()
        logger.info(f"Completed MFA challenge {self.challenge_id}")
    
    def is_valid(self) -> bool:
        """Check if challenge is valid (not expired and not completed)."""
        return not self.completed and datetime.utcnow() < self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'challenge_id': self.challenge_id,
            'user_id': self.user_id,
            'challenge_type': self.challenge_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'completed': self.completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'operation_type': self.operation_type
        }

class MFAManager:
    """Manager for MFA operations."""
    
    @staticmethod
    def setup_totp(user) -> Dict[str, Any]:
        """Set up TOTP for a user."""
        try:
            secret = pyotp.random_base32()
            
            totp = pyotp.TOTP(secret)
            
            provisioning_uri = totp.provisioning_uri(
                name=user.email,
                issuer_name="AgenticTrust"
            )
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            user.mfa_secret = secret
            user.mfa_type = 'totp'
            user.mfa_enabled = False  # Will be enabled after verification
            db_session.commit()
            
            logger.info(f"Set up TOTP for user {user.user_id}")
            
            return {
                'secret': secret,
                'qr_code': img_str,
                'provisioning_uri': provisioning_uri
            }
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error setting up TOTP: {str(e)}")
            raise
    
    @staticmethod
    def verify_totp(user, code: str) -> bool:
        """Verify TOTP code."""
        try:
            if not user.mfa_secret or user.mfa_type != 'totp':
                logger.error(f"User {user.user_id} does not have TOTP set up")
                return False
            
            totp = pyotp.TOTP(user.mfa_secret)
            
            is_valid = totp.verify(code)
            
            if is_valid and not user.mfa_enabled:
                user.mfa_enabled = True
                db_session.commit()
                logger.info(f"Enabled MFA for user {user.user_id}")
            
            return is_valid
        except Exception as e:
            logger.error(f"Error verifying TOTP: {str(e)}")
            return False
    
    @staticmethod
    def create_challenge(user, operation_type: str) -> Tuple[MFAChallenge, Dict[str, Any]]:
        """Create MFA challenge for critical operation."""
        try:
            if not user.mfa_enabled:
                logger.error(f"User {user.user_id} does not have MFA enabled")
                raise ValueError("MFA not enabled for this user")
            
            if user.mfa_type == 'totp':
                challenge = MFAChallenge.create(
                    user_id=user.user_id,
                    challenge_type='totp',
                    challenge_data='',
                    operation_type=operation_type
                )
                
                return challenge, {
                    'challenge_id': challenge.challenge_id,
                    'challenge_type': 'totp',
                    'expires_at': challenge.expires_at.isoformat()
                }
            else:
                logger.error(f"Unsupported MFA type: {user.mfa_type}")
                raise ValueError(f"Unsupported MFA type: {user.mfa_type}")
        except Exception as e:
            logger.error(f"Error creating MFA challenge: {str(e)}")
            raise
    
    @staticmethod
    def verify_challenge(challenge_id: str, code: str, user_id: Optional[str] = None) -> bool:
        """Verify MFA challenge."""
        try:
            challenge = db_session.query(MFAChallenge).get(challenge_id)
            
            if not challenge:
                logger.error(f"Challenge not found: {challenge_id}")
                return False
            
            if user_id and challenge.user_id != user_id:
                logger.error(f"Challenge {challenge_id} does not belong to user {user_id}")
                return False
            
            if not challenge.is_valid():
                logger.error(f"Challenge {challenge_id} is not valid (expired or already completed)")
                return False
            
            from agentictrust.db.models.user import User
            user = User.query.get(challenge.user_id)
            
            if not user:
                logger.error(f"User not found: {challenge.user_id}")
                return False
            
            if challenge.challenge_type == 'totp':
                is_valid = MFAManager.verify_totp(user, code)
                
                if is_valid:
                    challenge.complete()
                
                return is_valid
            else:
                logger.error(f"Unsupported challenge type: {challenge.challenge_type}")
                return False
        except Exception as e:
            logger.error(f"Error verifying MFA challenge: {str(e)}")
            return False
