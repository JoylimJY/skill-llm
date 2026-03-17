"""Docker sandbox management: build, create, exec, copy, destroy."""

import subprocess
import uuid
from pathlib import Path


class Sandbox:
    """Manage Docker containers for SkillBench instances."""

    def build(self, instance_dir: str) -> str:
        """Build Docker image from runtime/Dockerfile, return image tag."""
        instance_dir = Path(instance_dir)
        runtime_dir = instance_dir / "runtime"
        dockerfile = runtime_dir / "Dockerfile"

        if not dockerfile.exists():
            raise FileNotFoundError(f"No Dockerfile at {dockerfile}")

        tag = f"skillbench-{instance_dir.name}".lower().replace(" ", "-")

        result = subprocess.run(
            ["docker", "build", "-t", tag, "-f", str(dockerfile), str(runtime_dir)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Docker build failed:\n{result.stderr}")

        return tag

    def create(self, instance_dir: str) -> str:
        """Create and initialize a container.

        - docker run -d from the built image
        - copy runtime/workspace/ into container
        - run gen_inputs.py inside container to create input files
        - run setup.sh
        - return container_id
        """
        instance_dir = Path(instance_dir)
        runtime_dir = instance_dir / "runtime"
        tag = f"skillbench-{instance_dir.name}".lower().replace(" ", "-")

        # Start container
        result = subprocess.run(
            [
                "docker", "run", "-d",
                "--name", f"sb-{uuid.uuid4().hex[:12]}",
                "-w", "/workspace",
                tag,
                "tail", "-f", "/dev/null",  # Keep container alive
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"docker run failed:\n{result.stderr}")
        container_id = result.stdout.strip()

        try:
            # Copy workspace files into container
            workspace_dir = runtime_dir / "workspace"
            if workspace_dir.exists() and any(workspace_dir.iterdir()):
                subprocess.run(
                    ["docker", "cp", f"{workspace_dir}/.", f"{container_id}:/workspace/"],
                    check=True,
                    capture_output=True,
                    text=True,
                )

            # Copy and run gen_inputs.py
            gen_inputs = runtime_dir / "gen_inputs.py"
            if gen_inputs.exists():
                subprocess.run(
                    ["docker", "cp", str(gen_inputs), f"{container_id}:/workspace/gen_inputs.py"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                output, exit_code = self.exec(container_id, "python /workspace/gen_inputs.py")
                if exit_code != 0:
                    raise RuntimeError(f"gen_inputs.py failed (exit {exit_code}):\n{output}")

            # Copy and run setup.sh
            setup_sh = runtime_dir / "setup.sh"
            if setup_sh.exists():
                subprocess.run(
                    ["docker", "cp", str(setup_sh), f"{container_id}:/workspace/setup.sh"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                output, exit_code = self.exec(
                    container_id, "chmod +x /workspace/setup.sh && /workspace/setup.sh"
                )
                if exit_code != 0:
                    raise RuntimeError(f"setup.sh failed (exit {exit_code}):\n{output}")

        except Exception:
            self.destroy(container_id)
            raise

        return container_id

    def exec(self, container_id: str, cmd: str, timeout: int = 120) -> tuple[str, int]:
        """Execute a command inside the container, return (output, exit_code)."""
        result = subprocess.run(
            ["docker", "exec", container_id, "bash", "-c", cmd],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout + result.stderr
        return output, result.returncode

    def copy_out(self, container_id: str, container_path: str, host_path: str):
        """Copy files from container to host."""
        Path(host_path).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["docker", "cp", f"{container_id}:{container_path}", host_path],
            check=True,
            capture_output=True,
            text=True,
        )

    def destroy(self, container_id: str):
        """Stop and remove container."""
        subprocess.run(
            ["docker", "stop", container_id],
            capture_output=True,
            text=True,
            timeout=30,
        )
        subprocess.run(
            ["docker", "rm", "-f", container_id],
            capture_output=True,
            text=True,
            timeout=30,
        )
