import os
import docker
from typing import Dict, Any

# Define the absolute path to your host's outputs folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def execute_code(code: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Execute Python code in an ephemeral, air-gapped Docker container.
    Mapped directly to the host's output directory so generated files survive.
    """
    client = None
    container = None
    try:
        client = docker.from_env()

        # Use our custom MRPL data science image if available
        image_name = "vault-sandbox:latest"
        try:
            client.images.get(image_name)
        except docker.errors.ImageNotFound:
            # Fallback to slim (warning: pandas won't work in slim without install)
            image_name = "python:3.11-slim"

        # Create and start the container
        container = client.containers.run(
            image=image_name,
            command=["python", "-c", code],
            network_mode="none",        # Air-gapped: no network access
            mem_limit="256m",           # Memory cap for RTX 3050 system
            cpu_period=100000,
            cpu_quota=50000,            # Limit to 50% of one CPU core
            # Mount the Windows outputs folder into the Linux container
            volumes={
                OUTPUT_DIR: {
                    'bind': '/sandbox',
                    'mode': 'rw'
                }
            },
            working_dir="/sandbox",     # Forces all saved files to drop directly into the volume
            detach=True,
            stdin_open=False,
            stdout=True,
            stderr=True,
            remove=False                # We remove manually after reading logs
        )

        # Wait for completion with timeout
        result = container.wait(timeout=timeout)
        exit_code = result.get("StatusCode", -1)

        stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
        stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")

        return {
            "stdout": stdout.strip(),
            "stderr": stderr.strip(),
            "exit_code": exit_code,
            "timed_out": False
        }

    except docker.errors.ContainerError as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": e.exit_status if hasattr(e, "exit_status") else -1,
            "timed_out": False
        }
    except Exception as e:
        error_msg = str(e)
        timed_out = "timed out" in error_msg.lower() or "read timed out" in error_msg.lower()
        return {
            "stdout": "",
            "stderr": f"Sandbox error: {error_msg}",
            "exit_code": -1,
            "timed_out": timed_out
        }
    finally:
        # Always clean up the container
        if container:
            try:
                container.remove(force=True)
            except Exception:
                pass