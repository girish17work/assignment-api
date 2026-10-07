"""Runs inside an ephemeral container with no credentials or network."""
import contextlib
import io
import json
import sys
import traceback


def execute_python_code(code):
    output = io.StringIO()
    success = True
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        try:
            exec(compile(code, "<student>", "exec"), {"__name__": "__main__"})
        except BaseException as exc:
            success = False
            # Exclude this runner's frame; retain submitted-code frames.
            traceback.print_exception(type(exc), exc, exc.__traceback__.tb_next)
    return {"success": success, "output": output.getvalue()}


if __name__ == "__main__":
    request = json.load(sys.stdin)
    if "--restricted" in sys.argv:
        # -I excludes the script directory; load only our fixed trusted module.
        import importlib.util
        from pathlib import Path
        spec = importlib.util.spec_from_file_location("sandbox", Path(__file__).with_name("sandbox.py"))
        sandbox = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sandbox)
        sandbox.restrict_worker()
    result = execute_python_code(request["code"])
    sys.__stdout__.write(json.dumps(result))
