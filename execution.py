"""Credential-free worker process; Linux syscall restrictions live in sandbox.py."""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

RUNNER = Path(__file__).with_name("runner.py")


async def execute_isolated(code, timeout=8):
    if sys.platform != "linux" or os.geteuid() != 0:
        raise RuntimeError("The execution service requires its configured Linux Docker image")
    with tempfile.TemporaryDirectory() as directory:
        os.chmod(directory, 0o755)
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-I", str(RUNNER), "--restricted",
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE, cwd=directory,
            env={"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8"},
            user=65534, group=65534, extra_groups=[], start_new_session=True,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(json.dumps({"code": code}).encode()), timeout
            )
            if process.returncode:
                raise RuntimeError("Restricted execution worker failed")
            result = json.loads(stdout)
            if len(result["output"].encode()) > 1_000_000:
                raise ValueError("Output exceeds the 1 MB limit")
            return result
        finally:
            if process.returncode is None:
                try:
                    process.kill()
                except PermissionError:
                    # Render drops CAP_KILL. A trusted helper with the worker's
                    # own UID can terminate it without granting new privileges.
                    helper = await asyncio.create_subprocess_exec(
                        sys.executable, "-I", "-c",
                        "import os,sys;\ntry: os.kill(int(sys.argv[1]), 9)\nexcept ProcessLookupError: pass",
                        str(process.pid), user=65534, group=65534, extra_groups=[],
                        env={"PATH": "/usr/local/bin:/usr/bin:/bin"},
                        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
                    )
                    await helper.wait()
                    if helper.returncode:
                        raise RuntimeError("Cannot stop the execution worker")
                except ProcessLookupError:
                    pass
                await process.wait()
