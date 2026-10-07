import os
import sys
import subprocess
import time

def main():
    print("=" * 65)
    print("Starting AUTOSAR HLD Document Analysis Assistant")
    print("=" * 65)

    python_exe = sys.executable
    env = os.environ.copy()
    env["PYTHONPATH"] = "."

    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    print("[1/2] Launching FastAPI Backend on http://127.0.0.1:8000...")
    backend_proc = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        env=env
    )

    time.sleep(2)

    print("[2/2] Launching Streamlit Frontend on http://127.0.0.1:8501...")
    frontend_proc = subprocess.Popen(
        [python_exe, "-m", "streamlit", "run", "frontend/streamlit_app.py", "--server.port", "8501", "--server.headless", "true"],
        env=env
    )

    print("\n[SUCCESS] System active!")
    print(" - Streamlit UI: http://127.0.0.1:8501")
    print(" - Backend API:  http://127.0.0.1:8000/docs\n")
    print("Press Ctrl+C to stop both processes.")

    try:
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping services...")
        backend_proc.terminate()
        frontend_proc.terminate()

if __name__ == "__main__":
    main()
