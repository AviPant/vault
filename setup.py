#!/usr/bin/env python3
"""
V.A.U.L.T. — Automated Environment Setup & Launcher Script
Sovereign On-Premise Agentic AI Workbench for Industrial Operations (MRPL / SIH 26117)

Usage:
    python setup.py              # Interactive guided setup & health check
    python setup.py --auto       # Automatic unattended setup
    python setup.py --check      # Run prerequisite & environment diagnostics only
    python setup.py --models     # Pull required Ollama models
    python setup.py --sandbox    # Build Docker code execution sandbox image
    python setup.py start        # Launch backend and frontend services concurrently
"""

import os
import sys
import subprocess
import shutil
import platform
import argparse
import time
import json
import urllib.request
import urllib.error

# Configure safe console encoding on Windows
if sys.platform == "win32":
    try:
        if sys.stdout.encoding.lower() != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ANSI Color codes for clean terminal output (disabled if not supported)
USE_COLOR = os.isatty(sys.stdout.fileno()) if hasattr(sys.stdout, "fileno") else False
if sys.platform == "win32":
    os.system("") # Enable VT100 colors in Windows cmd/powershell

class Colors:
    HEADER = '\033[95m' if USE_COLOR else ''
    BLUE = '\033[94m' if USE_COLOR else ''
    CYAN = '\033[96m' if USE_COLOR else ''
    GREEN = '\033[92m' if USE_COLOR else ''
    YELLOW = '\033[93m' if USE_COLOR else ''
    RED = '\033[91m' if USE_COLOR else ''
    BOLD = '\033[1m' if USE_COLOR else ''
    UNDERLINE = '\033[4m' if USE_COLOR else ''
    RESET = '\033[0m' if USE_COLOR else ''

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
DATA_DIR = os.path.join(BACKEND_DIR, "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
OUTPUTS_DIR = os.path.join(DATA_DIR, "outputs")
VECTOR_DB_DIR = os.path.join(DATA_DIR, "vector_db")
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")

VENV_DIR = os.path.join(BACKEND_DIR, "venv")
IS_WINDOWS = platform.system().lower() == "windows"

if IS_WINDOWS:
    VENV_PYTHON = os.path.join(VENV_DIR, "Scripts", "python.exe")
    VENV_PIP = os.path.join(VENV_DIR, "Scripts", "pip.exe")
    VENV_UVICORN = os.path.join(VENV_DIR, "Scripts", "uvicorn.exe")
else:
    VENV_PYTHON = os.path.join(VENV_DIR, "bin", "python")
    VENV_PIP = os.path.join(VENV_DIR, "bin", "pip")
    VENV_UVICORN = os.path.join(VENV_DIR, "bin", "uvicorn")

REQUIRED_MODELS = [
    {"name": "llama3.1:8b", "role": "Orchestrator / Synthesis LLM", "size": "~4.7 GB"},
    {"name": "qwen2.5-coder:7b", "role": "Code Generation & Mathematical Analysis", "size": "~4.7 GB"},
    {"name": "qwen2.5vl:3b", "role": "Industrial Vision & Diagram OCR (Fast Default)", "size": "~2.2 GB"},
    {"name": "nomic-embed-text:latest", "role": "RAG Persistent Embeddings", "size": "~274 MB"}
]

OPTIONAL_MODELS = [
    {"name": "qwen2.5vl:7b", "role": "Industrial Vision (High Precision Deep Inspection)", "size": "~5.5 GB"}
]

def log_header(text: str):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 65}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}  {text}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 65}{Colors.RESET}")

def log_step(step: str, title: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}[{step}] {title}{Colors.RESET}")

def log_ok(msg: str):
    print(f"  {Colors.GREEN}[OK]{Colors.RESET} {msg}")

def log_warn(msg: str):
    print(f"  {Colors.YELLOW}[WARN]{Colors.RESET} {msg}")

def log_err(msg: str):
    print(f"  {Colors.RED}[ERR]{Colors.RESET} {msg}")

def log_info(msg: str):
    print(f"  {Colors.CYAN}[INFO]{Colors.RESET} {msg}")

def run_cmd(cmd, cwd=None, capture_output=False, check=True, env=None):
    """Utility function to run shell commands cleanly."""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    
    if isinstance(cmd, str) and IS_WINDOWS:
        shell = True
    elif isinstance(cmd, list):
        shell = False
    else:
        shell = True

    try:
        res = subprocess.run(
            cmd,
            cwd=cwd or ROOT_DIR,
            shell=shell,
            capture_output=capture_output,
            text=True,
            check=check,
            env=merged_env
        )
        return res
    except subprocess.CalledProcessError as e:
        if not capture_output:
            log_err(f"Command failed with exit code {e.returncode}: {cmd}")
        raise e

def print_banner():
    banner = f"""{Colors.CYAN}{Colors.BOLD}
 _    _       ___   _   _  _     _____ 
| |  | |     / _ \\ | | | || |   |_   _|
| |  | |    / /_\\ \\| | | || |     | |  
| |/\\| |    |  _  || | | || |     | |  
\\  /\\  /    | | | || |_| || |_____| |  
 \\/  \\/     \\_| |_/ \\___/ \\_____/\\_/   
{Colors.RESET}
{Colors.BOLD}Sovereign On-Premise Agentic AI Workbench for Industrial Operations{Colors.RESET}
{Colors.BLUE}Air-Gapped | Dynamic VRAM Routing | Docker Sandbox | ChromaDB RAG{Colors.RESET}
"""
    print(banner)

def check_python_version() -> bool:
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 10):
        log_err(f"Python 3.10+ required. Detected Python {v.major}.{v.minor}.{v.micro}")
        return False
    log_ok(f"Python version: {v.major}.{v.minor}.{v.micro} (Supported)")
    return True

def check_node_installed() -> bool:
    node_path = shutil.which("node")
    npm_path = shutil.which("npm")
    if not node_path or not npm_path:
        log_warn("Node.js / npm not found in system PATH. (Required for Frontend UI)")
        return False
    try:
        node_ver = subprocess.run(["node", "-v"], capture_output=True, text=True).stdout.strip()
        npm_ver = subprocess.run(["npm", "-v"], capture_output=True, text=True, shell=IS_WINDOWS).stdout.strip()
        log_ok(f"Node.js: {node_ver} | npm: {npm_ver}")
        return True
    except Exception:
        log_warn("Node.js detected but version check failed.")
        return False

def check_gpu_status():
    smi = shutil.which("nvidia-smi")
    if smi:
        try:
            res = subprocess.run([smi, "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"], capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                gpu_info = res.stdout.strip().split("\n")[0]
                log_ok(f"NVIDIA GPU Detected: {gpu_info}")
                return
        except Exception:
            pass
    log_info("GPU / nvidia-smi not detected or using CPU mode. Ollama will manage compute fallback.")

def is_ollama_running(url="http://127.0.0.1:11434") -> bool:
    try:
        req = urllib.request.Request(f"{url}/api/tags", headers={"User-Agent": "VAULT-Setup"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False

def get_installed_ollama_models(url="http://127.0.0.1:11434") -> list:
    try:
        req = urllib.request.Request(f"{url}/api/tags", headers={"User-Agent": "VAULT-Setup"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "") for m in data.get("models", [])]
            return models
    except Exception:
        return []

def check_ollama_status():
    ollama_cli = shutil.which("ollama")
    if not ollama_cli:
        log_warn("Ollama executable not found in PATH. Please install from https://ollama.ai")
    else:
        log_ok(f"Ollama CLI found: {ollama_cli}")

    if is_ollama_running():
        log_ok("Ollama daemon is running at http://127.0.0.1:11434")
        installed = get_installed_ollama_models()
        log_info(f"Available local models in Ollama: {len(installed)}")
        for req in REQUIRED_MODELS:
            name = req["name"]
            matched = any(m == name or m == f"{name}:latest" or (name.split(':')[0] in m and ':latest' in m) for m in installed)
            if matched:
                log_ok(f"  Model ready: {name} ({req['role']})")
            else:
                log_warn(f"  Missing model: {name} ({req['role']}) — Size: {req['size']}")
    else:
        log_warn("Ollama daemon is NOT running. Please start it with `ollama serve` or launch the Ollama app.")

def check_docker_status():
    docker_cli = shutil.which("docker")
    if not docker_cli:
        log_warn("Docker executable not found in PATH. (Air-gapped Code Sandbox will require Docker)")
        return False
    try:
        res = subprocess.run(["docker", "info"], capture_output=True, text=True)
        if res.returncode == 0:
            log_ok("Docker daemon is running and accessible.")
            return True
        else:
            log_warn("Docker CLI is installed, but the Docker daemon is not running. (Start Docker Desktop)")
            return False
    except Exception:
        log_warn("Could not communicate with Docker daemon.")
        return False

def setup_directories():
    log_step("1/6", "Initializing Project Storage Directories")
    dirs = [DATA_DIR, UPLOADS_DIR, OUTPUTS_DIR, VECTOR_DB_DIR, SESSIONS_DIR]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    log_ok(f"Created/Verified data directories in {DATA_DIR}")

def setup_env_file():
    log_step("2/6", "Verifying Backend Configuration (.env)")
    env_file = os.path.join(BACKEND_DIR, ".env")
    env_example = os.path.join(BACKEND_DIR, ".env.example")
    if not os.path.exists(env_file):
        if os.path.exists(env_example):
            shutil.copyfile(env_example, env_file)
            log_ok("Created backend/.env from .env.example")
        else:
            default_env = (
                "OLLAMA_API_URL=http://localhost:11434\n"
                "DEFAULT_GENERAL_MODEL=llama3.1:8b\n"
                "DEFAULT_CODER_MODEL=qwen2.5-coder:7b\n"
                "DEFAULT_VISION_MODEL=qwen2.5vl:3b\n"
                "EMBEDDING_MODEL=nomic-embed-text\n"
            )
            with open(env_file, "w") as f:
                f.write(default_env)
            log_ok("Generated default backend/.env")
    else:
        log_ok("backend/.env already exists.")

def setup_python_venv():
    log_step("3/6", "Setting Up Python Virtual Environment & Dependencies")
    
    # Check if existing virtualenv python works
    venv_exists = os.path.exists(VENV_PYTHON)
    if not venv_exists:
        log_info(f"Creating Python virtual environment in {VENV_DIR}...")
        try:
            run_cmd([sys.executable, "-m", "venv", VENV_DIR])
            log_ok("Virtual environment created.")
        except Exception as e:
            log_err(f"Failed to create virtual environment: {e}")
            log_info("Attempting to use system/active Python environment instead.")
    else:
        log_ok(f"Existing virtual environment found: {VENV_DIR}")

    target_pip = VENV_PIP if os.path.exists(VENV_PIP) else "pip"
    target_python = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable

    log_info("Upgrading pip and installing backend dependencies...")
    req_file = os.path.join(BACKEND_DIR, "requirements.txt")
    
    try:
        run_cmd([target_python, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], capture_output=True)
        run_cmd([target_python, "-m", "pip", "install", "-r", req_file])
        log_ok("Backend Python packages installed successfully.")
    except Exception as e:
        log_err(f"Failed to install requirements: {e}")
        log_info("You can manually run: pip install -r backend/requirements.txt")

def setup_frontend():
    log_step("4/6", "Installing Frontend Dependencies (React + Vite + Tailwind)")
    if not shutil.which("npm"):
        log_warn("npm not available; skipping frontend dependency installation.")
        return

    node_modules = os.path.join(FRONTEND_DIR, "node_modules")
    if os.path.exists(node_modules):
        log_ok("frontend/node_modules already exists. Running fast install check...")
    
    try:
        log_info("Running npm install in frontend directory...")
        run_cmd(["npm", "install"], cwd=FRONTEND_DIR)
        log_ok("Frontend dependencies installed successfully.")
    except Exception as e:
        log_err(f"npm install failed: {e}")

def build_docker_sandbox():
    log_step("5/6", "Building Air-Gapped Code Sandbox Docker Image")
    dockerfile = os.path.join(BACKEND_DIR, "Dockerfile.sandbox")
    if not os.path.exists(dockerfile):
        log_warn("Dockerfile.sandbox not found in backend/. Skipping sandbox build.")
        return

    if not check_docker_status():
        log_warn("Docker daemon unavailable. Skipping sandbox image build (will fallback to python:3.11-slim when Docker is started).")
        return

    try:
        log_info("Building Docker image 'vault-sandbox:latest' for isolated execution...")
        run_cmd(["docker", "build", "-t", "vault-sandbox:latest", "-f", dockerfile, BACKEND_DIR])
        log_ok("Docker sandbox image 'vault-sandbox:latest' built successfully.")
    except Exception as e:
        log_warn(f"Could not build sandbox image: {e}")

def pull_ollama_models(interactive=True):
    log_step("6/6", "Ollama LLM & Vision Model Verification")
    if not is_ollama_running():
        log_warn("Ollama is offline. Start 'ollama serve' in another terminal to download models.")
        return

    installed = get_installed_ollama_models()
    missing = []
    for req in REQUIRED_MODELS:
        name = req["name"]
        matched = any(m == name or m == f"{name}:latest" or (name.split(':')[0] in m and ':latest' in m) for m in installed)
        if not matched:
            missing.append(req)

    if not missing:
        log_ok("All required models are present in local Ollama storage.")
        return

    print(f"\n{Colors.YELLOW}The following core AI models are missing:{Colors.RESET}")
    for m in missing:
        print(f"  - {Colors.BOLD}{m['name']}{Colors.RESET} ({m['role']}) — Size: {m['size']}")

    should_pull = True
    if interactive:
        try:
            choice = input(f"\nWould you like to pull these missing models now? [Y/n]: ").strip().lower()
            if choice in ['n', 'no']:
                should_pull = False
        except (KeyboardInterrupt, EOFError):
            should_pull = False

    if should_pull:
        for m in missing:
            model_tag = m["name"]
            log_info(f"Pulling model: {model_tag} ({m['role']})...")
            try:
                run_cmd(["ollama", "pull", model_tag])
                log_ok(f"Successfully pulled {model_tag}")
            except Exception as e:
                log_err(f"Failed to pull {model_tag}: {e}")
    else:
        log_info("Skipped model download. You can pull them anytime with `python setup.py --models` or `ollama pull <model>`")

def start_services():
    """Launch backend and frontend concurrently."""
    log_header("LAUNCHING V.A.U.L.T. WORKBENCH")
    
    target_python = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable
    
    # 1. Check Ollama
    if not is_ollama_running():
        log_warn("Ollama is not running. Launching 'ollama serve' in background if possible...")
        if shutil.which("ollama"):
            try:
                subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2)
            except Exception:
                pass

    # 2. Start FastAPI backend
    backend_cmd = [target_python, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]
    log_info(f"Starting Backend on http://127.0.0.1:8000 (FastAPI)...")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = BACKEND_DIR
    
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=BACKEND_DIR,
        env=env
    )

    # 3. Start Vite frontend
    frontend_proc = None
    if shutil.which("npm"):
        log_info("Starting Frontend on http://localhost:5173 (React / Vite)...")
        frontend_proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=FRONTEND_DIR,
            shell=IS_WINDOWS
        )
    else:
        log_warn("npm not found. Please start frontend manually.")

    print(f"\n{Colors.GREEN}{Colors.BOLD}======================================================{Colors.RESET}")
    print(f"{Colors.GREEN}{Colors.BOLD}  V.A.U.L.T. Mission Control is Online!{Colors.RESET}")
    print(f"  • Frontend Dashboard: {Colors.CYAN}http://localhost:5173{Colors.RESET}")
    print(f"  • Backend REST API:   {Colors.CYAN}http://127.0.0.1:8000{Colors.RESET}")
    print(f"  • API Documentation:  {Colors.CYAN}http://127.0.0.1:8000/docs{Colors.RESET}")
    print(f"{Colors.GREEN}{Colors.BOLD}======================================================{Colors.RESET}")
    print(f"\n{Colors.YELLOW}Press Ctrl+C in this terminal to shut down all services.{Colors.RESET}\n")

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                log_err("Backend server stopped unexpectedly.")
                break
            if frontend_proc and frontend_proc.poll() is not None:
                log_warn("Frontend server stopped.")
                break
    except KeyboardInterrupt:
        print(f"\n{Colors.CYAN}Shutting down V.A.U.L.T. services gracefully...{Colors.RESET}")
    finally:
        if backend_proc:
            backend_proc.terminate()
            try:
                backend_proc.wait(timeout=3)
            except Exception:
                backend_proc.kill()
        if frontend_proc:
            frontend_proc.terminate()
            try:
                frontend_proc.wait(timeout=3)
            except Exception:
                frontend_proc.kill()
        log_ok("Services stopped. Goodbye!")

def run_diagnostics_only():
    log_header("V.A.U.L.T. ENVIRONMENT DIAGNOSTICS")
    check_python_version()
    check_gpu_status()
    check_node_installed()
    check_docker_status()
    check_ollama_status()
    
    log_step("PATHS", "Storage & Environment Status")
    for name, p in [
        ("Backend Directory", BACKEND_DIR),
        ("Frontend Directory", FRONTEND_DIR),
        (".env Configuration", os.path.join(BACKEND_DIR, ".env")),
        ("Virtual Environment", VENV_DIR),
        ("Uploads Storage", UPLOADS_DIR),
        ("Outputs Storage", OUTPUTS_DIR),
        ("ChromaDB Vector Store", VECTOR_DB_DIR),
    ]:
        status = f"{Colors.GREEN}EXISTS{Colors.RESET}" if os.path.exists(p) else f"{Colors.YELLOW}MISSING{Colors.RESET}"
        print(f"  {name:25}: {status} ({p})")

def main():
    parser = argparse.ArgumentParser(
        description="V.A.U.L.T. Sovereign On-Premise AI Workbench Setup & Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("action", nargs="?", choices=["setup", "start", "run", "check", "models", "sandbox"], default="setup",
                        help="Action to perform: 'setup' (default), 'start'/'run' (launch app), 'check' (diagnostics), 'models' (pull LLMs), 'sandbox' (build Docker)")
    parser.add_argument("--auto", action="store_true", help="Run unattended non-interactive setup without prompts")
    parser.add_argument("--check", action="store_true", help="Run system diagnostics and exit")
    parser.add_argument("--models", action="store_true", help="Pull required Ollama models and exit")
    parser.add_argument("--sandbox", action="store_true", help="Build Docker sandbox and exit")
    parser.add_argument("--start", action="store_true", help="Start application servers after setup")
    
    args = parser.parse_args()

    print_banner()

    # Route specific flags/actions
    if args.check or args.action == "check":
        run_diagnostics_only()
        return

    if args.models or args.action == "models":
        pull_ollama_models(interactive=False)
        return

    if args.sandbox or args.action == "sandbox":
        build_docker_sandbox()
        return

    if args.start or args.action in ["start", "run"]:
        start_services()
        return

    # Standard / Full Setup Flow
    log_header("RUNNING AUTOMATED SETUP")
    interactive = not args.auto

    # 1. System checks
    check_python_version()
    check_gpu_status()
    check_node_installed()
    check_docker_status()
    check_ollama_status()

    # 2. Folder structures
    setup_directories()

    # 3. Environment configuration
    setup_env_file()

    # 4. Backend Python virtualenv & packages
    setup_python_venv()

    # 5. Frontend node packages
    setup_frontend()

    # 6. Docker Sandbox
    build_docker_sandbox()

    # 7. Model check & pull
    pull_ollama_models(interactive=interactive)

    log_header("SETUP COMPLETE!")
    print(f"""
{Colors.GREEN}{Colors.BOLD}Project V.A.U.L.T. is ready for operation!{Colors.RESET}

To launch the entire workbench with a single command:
  {Colors.CYAN}{Colors.BOLD}python setup.py start{Colors.RESET}

Or run the services individually:
  {Colors.BOLD}Backend:{Colors.RESET}
    cd backend
    uvicorn app.main:app --reload --port 8000
    
  {Colors.BOLD}Frontend:{Colors.RESET}
    cd frontend
    npm run dev

  {Colors.BOLD}Ollama Models:{Colors.RESET}
    python setup.py --models
""")

    if interactive:
        try:
            choice = input(f"Would you like to start the V.A.U.L.T. application now? [Y/n]: ").strip().lower()
            if choice not in ['n', 'no']:
                start_services()
        except (KeyboardInterrupt, EOFError):
            pass

if __name__ == "__main__":
    main()
