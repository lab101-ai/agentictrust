import os
from sdk.client import AgenticTrustClient
from openai import OpenAI
from typing import Optional

# Initialize the AgenticTrustClient with API base
client = AgenticTrustClient(
    api_base="http://localhost:8000"
)

def get_agent_response(prompt: str, first_name: Optional[str] = None, last_name: Optional[str] = None):
    # Get your OpenAI API key from environment variables to avoid hard-coding secrets
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # noqa: S105 – handled via env var; fallback empty
    openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None  # Lazily initialise if key is present
    
    # Personalize greeting if names are provided
    personalized_prompt = prompt
    user_identifier = ""
    if first_name and last_name:
        user_identifier = f"{first_name} {last_name}"
    elif first_name:
        user_identifier = first_name
    elif last_name:
        user_identifier = last_name
    
    if user_identifier:
        # Add user information to the prompt for context
        personalized_prompt = f"[Message from user: {user_identifier}] {prompt}"
    
    # Call the OpenAI chat endpoint
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": personalized_prompt}]
        # Note: We removed oauth_token parameter as it's not supported by OpenAI API
        # The AgenticTrust integration should be handled separately
    )
    # Extract assistant message
    return response.choices[0].message.content