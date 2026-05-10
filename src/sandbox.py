"""Docker sandbox management: build, create, exec, copy, destroy."""

import json
import subprocess
import uuid
from pathlib import Path


class BuildFailedError(RuntimeError):
    """Raised when Docker build/create fails after all retry attempts."""
    pass


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
            raise RuntimeError(f"Docker build failed:\n{result.stdout}\n{result.stderr}")

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
            skill_context_dir = runtime_dir / "skill_context"
            if skill_context_dir.exists() and any(skill_context_dir.iterdir()):
                # 将其拷贝到容器的 /workspace/skill_context 目录下，方便 Agent 查阅
                subprocess.run(
                    ["docker", "cp", f"{skill_context_dir}/.", f"{container_id}:/workspace/skill_context/"],
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
                output, exit_code = self.exec(container_id, "python3 /workspace/gen_inputs.py")
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

    def build_with_retry(self, instance_dir: str, max_retries: int = 3) -> tuple[str, str]:
        """Build image and create container with LLM-assisted environment repair on failure.

        Returns (image_tag, container_id).
        Raises BuildFailedError after max_retries failures.
        """
        from .synthesizer import fix_environment 

        instance_dir = Path(instance_dir)
        runtime_dir = instance_dir / "runtime"
        
        dockerfile_path = runtime_dir / "Dockerfile"
        gen_inputs_path = runtime_dir / "gen_inputs.py"
        setup_sh_path = runtime_dir / "setup.sh"

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                print(f"  Build attempt {attempt}/{max_retries}...")
                
                tag = self.build(str(instance_dir))
                container_id = self.create(str(instance_dir))
                
                return tag, container_id

            except RuntimeError as e:
                last_error = e
                error_msg = str(e)
                print(f"  Attempt {attempt} failed: {error_msg[:200]}")

                if attempt < max_retries:
                    print(f"  Requesting LLM to diagnose and fix the error...")
                    result = fix_environment(
                        dockerfile=dockerfile_path.read_text() if dockerfile_path.exists() else "",
                        error_log=error_msg,
                        gen_inputs_script=gen_inputs_path.read_text() if gen_inputs_path.exists() else "",
                        setup_script=setup_sh_path.read_text() if setup_sh_path.exists() else "",
                    )
                    if "dockerfile" in result["changed"]:
                        dockerfile_path.write_text(result["dockerfile"])
                        print(f"    - Fixed: Dockerfile")
                        
                    if "gen_inputs" in result["changed"]:
                        gen_inputs_path.write_text(result["gen_inputs_script"])
                        print(f"    - Fixed: gen_inputs.py")
                        
                    if "setup" in result["changed"]:
                        setup_sh_path.write_text(result["setup_script"])
                        print(f"    - Fixed: setup.sh")
                
                    print(f"  Environment patched, retrying build...")
    

        task_json_path = instance_dir / "task.json"
        if task_json_path.exists():
            task_data = json.loads(task_json_path.read_text())
            task_data["build_status"] = "failed"
            task_json_path.write_text(json.dumps(task_data, indent=2))

        raise BuildFailedError(
            f"Docker environment setup failed after {max_retries} attempts. "
            f"Last error: {last_error}"
        )

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

    def list_containers(self, all: bool = True) -> list[dict]:
        """List skillbench containers. Returns list of {id, name, status, image}."""
        cmd = ["docker", "ps", "--filter", "name=sb-", "--format", "{{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}"]
        if all:
            cmd.insert(2, "-a")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        containers = []
        for line in result.stdout.strip().splitlines():
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 4:
                containers.append({
                    "id": parts[0],
                    "name": parts[1],
                    "status": parts[2],
                    "image": parts[3],
                })
        return containers

    def cleanup_all(self) -> int:
        """Stop and remove all skillbench containers. Returns number of cleaned containers."""
        containers = self.list_containers(all=True)
        for c in containers:
            self.destroy(c["id"])
        return len(containers)
