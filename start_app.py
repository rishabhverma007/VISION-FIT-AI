"""
VisionFit AI launcher: starts Ollama (if needed) and the Flask app.
Everything runs on a single address: http://localhost:5000
(Voice Assistant is a feature at /voice-assistant on the same port.)
Run via: run_visionfit.bat  (or: python start_app.py)
"""
import atexit
import os
import subprocess
import sys
import time

try:
    import requests
except ImportError:
    requests = None

_flask_proc = None
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_FLASK_LOG = os.path.join(_PROJECT_ROOT, "visionfit_flask.log")


def _kill_flask():
    global _flask_proc
    if _flask_proc is not None and _flask_proc.poll() is None:
        try:
            _flask_proc.terminate()
            _flask_proc.wait(timeout=5)
        except Exception:
            try:
                _flask_proc.kill()
            except Exception:
                pass
        print("  Flask stopped.")
    _flask_proc = None


def is_ollama_running():
    if requests is None:
        return False
    try:
        r = requests.get("http://localhost:11434", timeout=2)
        return r.status_code == 200
    except requests.exceptions.RequestException:
        return False


def start_ollama():
    print("Ollama is not running. Starting Ollama...")
    try:
        if sys.platform == "win32":
            subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen(["ollama", "serve"])
        print("Waiting for Ollama to start...")
        for _ in range(30):
            if is_ollama_running():
                print("Ollama started successfully.")
                return True
            time.sleep(1)
        print("Timed out waiting for Ollama.")
        return False
    except FileNotFoundError:
        print("Error: 'ollama' not found. Install Ollama and add it to PATH.")
        return False


def main():
    global _flask_proc

    if not is_ollama_running():
        if not start_ollama():
            print("Ollama failed to start. Yoga/Voice features may use fallbacks.")
    else:
        print("Ollama is already running.")

    print("Starting VisionFit Flask app...")
    flask_out = open(_FLASK_LOG, "w", encoding="utf-8", errors="replace")
    try:
        _flask_proc = subprocess.Popen(
            [sys.executable, "app.py"],
            cwd=_PROJECT_ROOT,
            stdout=flask_out,
            stderr=subprocess.STDOUT,
            env=os.environ.copy(),
        )
    except Exception as e:
        print(f"Failed to start Flask: {e}")
        flask_out.close()
        _flask_proc = None
    else:
        time.sleep(1.5)
        if _flask_proc.poll() is not None:
            print("Flask exited immediately. Check visionfit_flask.log")
        else:
            print("  VisionFit AI at http://localhost:5000")
            print("  Voice Assistant: http://localhost:5000/voice-assistant")

    atexit.register(_kill_flask)
    print("")
    print("Press Enter to stop and exit...")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        # EOFError can occur in non-interactive environments; treat it like a normal exit.
        pass
    _kill_flask()


if __name__ == "__main__":
    main()
