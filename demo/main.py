import subprocess
import os
from pathlib import Path
import time
import shutil

def main():
    project_root = Path(__file__).resolve().parent.parent # agentictrust_v1/
    
    # Path to FastAPI app (cisco_app.py)
    cisco_app_script = project_root / "demo" / "ui" / "cisco_app.py"
    
    # Path to Streamlit app (crewai_chat_ui.py)
    streamlit_app_script = project_root / "demo" / "ui" / "crewai_chat_ui.py"
    
    # --- Commands ---
    # Command to run FastAPI app (cisco_app.py will use uvicorn on port 8501 as defined in its main)
    fastapi_command = ["python", str(cisco_app_script)]
    
    # Command to run Streamlit app on a different port (e.g., 8502)
    streamlit_command = ["streamlit", "run", str(streamlit_app_script), "--server.port", "8502"]
    
    print(f"Project root: {project_root}")
    print("----------------------------------------------------------------------")
    print("Attempting to launch FastAPI Cisco DB UI (expected on http://localhost:8501)...")
    print(f"Command: {' '.join(fastapi_command)}")
    print("----------------------------------------------------------------------")
    print("Attempting to launch Streamlit CrewAI Chat UI (expected on http://localhost:8502)...")
    print(f"Command: {' '.join(streamlit_command)}")
    print("----------------------------------------------------------------------")
    
    project_root_str = str(project_root)
    
    # Prepare environment for subprocesses
    sub_env = os.environ.copy()
    sub_env["PYTHONUTF8"] = "1"
    
    # Add project_root to PYTHONPATH for the subprocesses
    # This helps Python find the 'demo' package for imports like 'from demo.agents import ...'
    if "PYTHONPATH" in sub_env:
        sub_env["PYTHONPATH"] = f"{project_root_str}{os.pathsep}{sub_env['PYTHONPATH']}"
    else:
        sub_env["PYTHONPATH"] = project_root_str

    processes = []
    try:
        # Ensure critical dependencies are present before launching
        missing_fastapi = False
        try:
            import fastapi  # noqa: F401
        except ImportError:
            missing_fastapi = True

        if missing_fastapi:
            print(
                "\nERROR: 'fastapi' is not installed in the current environment, "
                "so the Cisco DB UI cannot be started.\n"
                "Fix: activate your project environment and run:\n"
                "   pip install fastapi uvicorn jinja2 pydantic\n"
                "or use 'poetry install' if you are using Poetry."
            )
            # Still attempt to launch Streamlit UI if present (it may not depend on fastapi)

        # --- FastAPI APP ---
        if not missing_fastapi:
            p_fastapi = subprocess.Popen(fastapi_command, cwd=project_root, env=sub_env)
            processes.append(p_fastapi)
            print(f"FastAPI app process started (PID: {p_fastapi.pid})...")
            time.sleep(3)  # Give it a moment to start
        else:
            print("Skipping FastAPI app launch due to missing dependency.")

        # --- Streamlit APP (optional) ---
        # If Streamlit isn't installed (or not on PATH), we gracefully skip starting
        if shutil.which("streamlit") is None:
            print(
                "Streamlit executable not found in PATH. "
                "Skipping launch of CrewAI Chat UI.\n"
                "To enable the chat UI, install dependencies with:\n"
                "   pip install streamlit crewai crewai-tools\n"
                "and ensure your environment has an OPENAI_API_KEY configured."
            )
        else:
            p_streamlit = subprocess.Popen(streamlit_command, cwd=project_root, env=sub_env)
            processes.append(p_streamlit)
            print(f"Streamlit app process started (PID: {p_streamlit.pid})...")
            time.sleep(3)  # Give it a moment to start

        print("\nApplications currently running:")
        print("  FastAPI Cisco DB UI: http://localhost:8501")
        if shutil.which("streamlit") is not None:
            print("  Streamlit AI Chat UI: http://localhost:8502")
        else:
            print("  (Streamlit UI not started)")

        print("\nPress Ctrl+C in this terminal to stop both applications.")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down applications...")
    except FileNotFoundError as e:
        print(f"Error: A command was not found (e.g., 'python' or 'streamlit'). Please ensure they are installed and in your PATH. Details: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        for p in reversed(processes): # Terminate in reverse order of creation
            if p.poll() is None: # If process is still running
                print(f"Terminating process {p.pid}...")
                p.terminate() 
                try:
                    p.wait(timeout=5) 
                except subprocess.TimeoutExpired:
                    print(f"Process {p.pid} did not terminate, killing...")
                    p.kill() 
        print("All application processes have been requested to stop.")

if __name__ == "__main__":
    main()
