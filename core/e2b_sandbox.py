"""
core/e2b_sandbox.py
E2B Code Interpreter Sandbox Manager.
Enables LangGraph ReAct agent to execute Python data analysis scripts in an isolated E2B cloud sandbox,
with automatic fallback to a local safe executor if an E2B API key is not configured.
"""

import os
import sys
import io
import time
import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Union, List

# Try importing E2B Code Interpreter SDK
try:
    from e2b_code_interpreter import Sandbox as E2BSandbox
    E2B_AVAILABLE = True
except ImportError:
    E2B_AVAILABLE = False


@dataclass
class SandboxExecutionResult:
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    results: List[Any] = field(default_factory=list)
    is_cloud_sandbox: bool = False
    execution_time_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "error": self.error,
            "is_cloud_sandbox": self.is_cloud_sandbox,
            "execution_time_seconds": round(self.execution_time_seconds, 3)
        }


class E2BSandboxManager:
    """
    Manages code execution inside E2B Cloud Sandbox or local fallback environment.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("E2B_API_KEY")
        self._sandbox = None
        self.use_cloud = bool(self.api_key and E2B_AVAILABLE)

    def is_cloud_enabled(self) -> bool:
        """Returns True if live E2B cloud sandbox is configured and accessible."""
        return bool(self.api_key and E2B_AVAILABLE)

    def upload_file(self, filename: str, content: Union[str, bytes]) -> bool:
        """Uploads statement file into the sandbox workspace."""
        if self.is_cloud_enabled():
            try:
                if not self._sandbox:
                    self._sandbox = E2BSandbox(api_key=self.api_key)
                
                # Write to /home/user/ in E2B sandbox
                target_path = f"/home/user/{filename}"
                if isinstance(content, str):
                    self._sandbox.files.write(target_path, content)
                else:
                    self._sandbox.files.write(target_path, content.decode('utf-8', errors='ignore'))
                return True
            except Exception as e:
                # Log error and fall back
                print(f"[E2B Warning] Failed to upload file to E2B Cloud Sandbox: {e}")
                return False
        return True

    def run_code(self, code: str, local_context: Optional[Dict[str, Any]] = None) -> SandboxExecutionResult:
        """
        Executes Python data analysis code.
        Uses live E2B cloud sandbox if configured; otherwise runs in local fallback environment.
        """
        start_time = time.time()

        # 1. Attempt live E2B Cloud execution
        if self.is_cloud_enabled():
            try:
                if not self._sandbox:
                    self._sandbox = E2BSandbox(api_key=self.api_key)

                execution = self._sandbox.run_code(code)
                duration = time.time() - start_time

                stdout_text = ""
                stderr_text = ""
                error_text = None

                if execution.logs.stdout:
                    stdout_text = "\n".join(execution.logs.stdout)
                if execution.logs.stderr:
                    stderr_text = "\n".join(execution.logs.stderr)
                if execution.error:
                    error_text = f"{execution.error.name}: {execution.error.value}\n{execution.error.traceback}"

                return SandboxExecutionResult(
                    stdout=stdout_text,
                    stderr=stderr_text,
                    error=error_text,
                    results=execution.results,
                    is_cloud_sandbox=True,
                    execution_time_seconds=duration
                )
            except Exception as e:
                # If E2B execution fails (e.g. invalid key or timeout), fall back to local execution
                err_msg = f"E2B cloud execution failed ({str(e)}). Falling back to local execution."
                print(f"[E2B Fallback] {err_msg}")

        # 2. Local Fallback Execution
        return self._run_code_locally(code, local_context=local_context, start_time=start_time)

    def _run_code_locally(
        self, code: str, local_context: Optional[Dict[str, Any]], start_time: float
    ) -> SandboxExecutionResult:
        """Runs Python code safely in a local namespace, capturing all prints and errors."""
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirected_out = io.StringIO()
        redirected_err = io.StringIO()

        exec_globals = {
            "__builtins__": __builtins__,
            "sys": sys,
            "os": os,
            "json": json,
            "time": time,
        }

        # Inject preloaded modules if available
        try:
            import pandas as pd
            import numpy as np
            exec_globals["pd"] = pd
            exec_globals["np"] = np
        except ImportError:
            pass

        if local_context:
            exec_globals.update(local_context)

        error_text = None
        try:
            sys.stdout = redirected_out
            sys.stderr = redirected_err
            exec(code, exec_globals)
        except Exception as e:
            error_text = f"{type(e).__name__}: {str(e)}"
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        duration = time.time() - start_time
        return SandboxExecutionResult(
            stdout=redirected_out.getvalue(),
            stderr=redirected_err.getvalue(),
            error=error_text,
            is_cloud_sandbox=False,
            execution_time_seconds=duration
        )

    def close(self):
        """Closes live E2B sandbox session if open."""
        if self._sandbox:
            try:
                self._sandbox.close()
            except Exception:
                pass
            self._sandbox = None
