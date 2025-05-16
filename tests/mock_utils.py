"""Mock utility functions for testing."""
from tests.mock_issued_token import MockIssuedToken
from agentictrust.utils.logger import logger
import uuid

def mock_verify_token(token_str, allow_clock_skew=True, max_clock_skew_seconds=86400):
    """Mock implementation of verify_token for testing."""
    logger.debug(f"mock_verify_token called with token: {token_str}")
    
    mock_token = MockIssuedToken(
        token_id=str(uuid.uuid4()),
        client_id="mock_client",
        scope="read:data write:data",
        delegator_sub="mock_user_id"
    )
    return mock_token
