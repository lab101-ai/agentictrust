# Ensure project root in path
import sys, os
from pathlib import Path # Import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import streamlit as st
from dotenv import load_dotenv
from crewai import Crew, Task

# Path adjustment for being in 'ui' subdirectory, accessing 'agents.py' in 'demo/'
from demo.agents import get_workspan_data_agent, get_cisco_integration_agent 

# Construct the path to demo/.env relative to this file's location (demo/ui/crewai_chat_ui.py)
dotenv_path = Path(__file__).parent.parent / ".env" 
print(f"Looking for .env file at: {dotenv_path}")
print(f".env file exists: {dotenv_path.exists()}")

# Try all possible locations for .env
possible_env_paths = [
    dotenv_path,  # demo/.env
    PROJECT_ROOT / ".env",  # project_root/.env
    Path(".env"),  # current directory/.env
]

for env_path in possible_env_paths:
    if env_path.exists():
        print(f"Loading environment from: {env_path}")
        load_dotenv(dotenv_path=env_path)
        break
else:
    print("No .env file found in any of the expected locations!")
    # Create a basic .env file with instructions
    print("Creating a placeholder .env file in demo directory")
    with open(dotenv_path, "w") as f:
        f.write("# Add your OpenAI API key here\n")
        f.write("OPENAI_API_KEY=\n")

def run_crewai_chat_ui():
    st.title("AI Assistant Chat: Cisco & WorkSpan Integration")

    # Check for API key after loading .env
    openai_api_key = os.getenv("OPENAI_API_KEY")
    print(f"OPENAI_API_KEY found: {bool(openai_api_key)}")
    if not openai_api_key:
        st.error("OPENAI_API_KEY not found. Please set it in your .env file or environment variables.")
        # Show specific instructions
        st.info("""
        To add your OpenAI API key:
        1. Create a file named `.env` in the `demo` directory
        2. Add the line: `OPENAI_API_KEY=your_api_key_here`
        3. Restart the application
        """)
        st.stop()

    try:
        print("Initializing WorkSpan data agent...")
        workspan_agent = get_workspan_data_agent()
        print("WorkSpan data agent created successfully")
        
        print("Initializing Cisco integration agent...")
        cisco_agent = get_cisco_integration_agent()
        print("Cisco integration agent created successfully")
    except Exception as e:
        error_msg = f"Error initializing agents: {e}"
        print(f"ERROR: {error_msg}")
        st.error(error_msg)
        st.stop()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask the Cisco agent (e.g., 'Get Cisco devices for Acme Corp'):"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    user_query_task = Task(
                        description=f"""User's query: '{prompt}'.
                        Your primary goal is to answer this user query comprehensively.
                        If the query mentions a partner, company, or requires any information that might reside in the WorkSpan database 
                        (e.g., specific details about a partner name, their ID, activities, etc.), 
                        you MUST first formulate a precise question or sub-task for the 'WorkSpan Data Specialist' 
                        and delegate it to them to retrieve that specific WorkSpan information.
                        After receiving the necessary information from the WorkSpan Data Specialist, 
                        use that context to inform your queries to the Cisco database (using your CiscoDataTool) 
                        and then synthesize a final, consolidated answer for the user.""",
                        expected_output="A comprehensive answer to the user's query, integrating WorkSpan and Cisco data as necessary. If WorkSpan data is needed, it should be fetched first and then used to query Cisco data.",
                        agent=cisco_agent
                    )

                    print("Creating crew with Cisco and WorkSpan agents...")
                    query_crew = Crew(
                        agents=[cisco_agent], 
                        tasks=[user_query_task],
                        verbose=True 
                    )

                    print("Initiating crew kickoff...")
                    result = query_crew.kickoff()
                    # CrewOutput object doesn't have len() - get the result content directly
                    print(f"Crew successfully completed task")
                    
                    # Handle the result based on its type
                    if hasattr(result, 'raw'):
                        # For newer versions that return CrewOutput with a raw attribute
                        result_text = result.raw
                    elif hasattr(result, 'content'):
                        # For versions that might use a content attribute
                        result_text = result.content
                    else:
                        # Fallback to string conversion
                        result_text = str(result)
                    
                    st.markdown(result_text)
                    st.session_state.messages.append({"role": "assistant", "content": result_text})
                except Exception as e:
                    error_message = f"An error occurred: {e}"
                    print(f"ERROR during crew execution: {e}")
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})

if __name__ == "__main__":
    run_crewai_chat_ui()
