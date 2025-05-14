import os
import json
from typing import Optional
import time
import requests
from dotenv import load_dotenv
from uuid import uuid4
from passlib.context import CryptContext
from agents import Agent, Runner, function_tool, RunContextWrapper  # OpenAI Agents SDK

# ---------------------------------------------------------------------------
# AgenticTrust OAuth utilities (no SDK)
# ---------------------------------------------------------------------------

load_dotenv(dotenv_path="demo/.env", override=True)

# Read client credentials from environment – set via .env or shell
AGENTICTRUST_CLIENT_ID = os.getenv("AGENTICTRUST_CLIENT_ID")
AGENTICTRUST_CLIENT_SECRET = os.getenv("AGENTICTRUST_CLIENT_SECRET")

# Password hashing for creating demo users
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Cache token in module-level var so we don’t hit the server for every call
_cached_token: Optional[str] = None
_token_expiry: float = 0.0  # Unix timestamp

# ---------------------------------------------------------------------------
# Helper: Ensure user exists (create anonymous on demand)
# ---------------------------------------------------------------------------

def _ensure_user(email: str, full_name: Optional[str] = None) -> str:
    """Return user_id for given email, creating the user if necessary."""

    # 1. List users
    try:
        resp = requests.get("http://localhost:8000/api/users", timeout=10)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Could not list users: {exc}") from exc

    for user in resp.json():
        if user.get("email") == email:
            return user["user_id"]

    # 2. Create user
    user_payload = {
        "username": email,
        "email": email,
        "full_name": full_name or email,
        "hashed_password": pwd_context.hash("changeme"),
        "is_external": True,
    }

    resp = requests.post("http://localhost:8000/api/users", json=user_payload, timeout=10)
    if resp.status_code not in {200, 201}:
        raise RuntimeError(f"Failed to create user {email}: {resp.status_code} {resp.text}")

    return resp.json()["user"]["user_id"] if "user" in resp.json() else resp.json()["user_id"]

# ---------------------------------------------------------------------------
# Modified token fetch to be per-delegator
# ---------------------------------------------------------------------------

def _get_token_for_user(user_sub: str) -> str:
    """Issue a *new* access token delegated from the given user_sub."""

    payload = {
        "grant_type": "client_credentials",
        "client_id": AGENTICTRUST_CLIENT_ID,
        "client_secret": AGENTICTRUST_CLIENT_SECRET,
        "agent_type": "assistant",
        "agent_model": "demo-app",
        "agent_provider": "demo-local",
        "agent_instance_id": str(uuid4()),  # unique per call
        "scope": "read:basic",
        "delegator_sub": user_sub,
        "launch_reason": "agent_delegated",
        "launched_by": user_sub,
    }

    resp = requests.post("http://localhost:8000/api/oauth/token", json=payload, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError(f"Token request failed: {resp.status_code} {resp.text}")

    return resp.json()["access_token"]

# ---------------------------------------------------------------------------
# OpenAI integration – use token to tag user context (custom header example)
# ---------------------------------------------------------------------------

# Agents SDK uses the default OpenAI client and env var OPENAI_API_KEY

def get_agent_response(prompt: str, first_name: Optional[str] = None, last_name: Optional[str] = None):
    # Determine delegator (end-user) identity
    if first_name or last_name:
        email_local = "".join(filter(None, [first_name, last_name])).lower().replace(" ", "-")
        user_email = f"{email_local or 'anon'}@example.com"
        full_name = " ".join(filter(None, [first_name, last_name]))
    else:
        # Anonymous user – create if not exists
        user_email = f"anon-{uuid4()}@example.com"
        full_name = "Anonymous"

    user_sub = _ensure_user(user_email, full_name=full_name)

    personalized_prompt = f"[Message from user: {full_name}] {prompt}"

    # Run agent via Agents SDK – DB queries will happen via `query_database` tool
    result = Runner.run_sync(demo_agent, personalized_prompt, context={"user_sub": user_sub})
    return result.final_output

# ---------------------------------------------------------------------------
# run_db_query helper (still used by tool)
# ---------------------------------------------------------------------------

def run_db_query(sql: str, user_sub: Optional[str] = None) -> list[dict]:
    # This is a placeholder for a real DB query function
    return []

# ---------------------------------------------------------------------------
# DB query tool and agent definition
# ---------------------------------------------------------------------------

@function_tool
def query_database(ctx: RunContextWrapper[dict], sql: str) -> list[dict]:  # noqa: ANN001
    """Execute a read-only SQL query via MCP server as the *current* user.

    Args:
        ctx: Agents run context – we expect a `user_sub` key in ctx.context.
        sql: The SELECT query to run.
    Returns:
        List of rows (dicts).
    """

    # Very naive read-only guard
    if not sql.strip().lower().startswith("select"):
        raise ValueError("Only SELECT queries are allowed from this tool")

    user_sub: Optional[str] = ctx.context.get("user_sub") if ctx else None
    return run_db_query(sql, user_sub=user_sub)


# Main agent object used by the demo app
demo_agent = Agent(
    name="Demo Support Agent",
    instructions=(
        "You are a customer-support assistant. Use the `query_database` tool to look up "
        "information from the ticketing system when needed before you answer."
    ),
    tools=[query_database],
)