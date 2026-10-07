# Render Assignment API

This version targets Render Free Docker Web Services. It serves POST /code-interpreter, GET /health, and interactive /docs. Add more assignment endpoints to main.py; they share one service URL.

## Setup

1. Put the files in this directory at the root of a GitHub repository. Never commit tokens.
2. In Render choose New > Web Service and select the repository (or its public Git URL).
3. Choose Docker and the Free instance type. Health check path: /health.
4. Add AIPIPE_TOKEN as a secret environment variable, using your token from https://aipipe.org/login. Optional AI_MODEL defaults to gpt-4.1-mini.
5. Deploy, wait for Live, then open the displayed onrender.com URL plus /docs.
6. Test success, runtime error, syntax error, timeout, and browser CORS before submitting the displayed URL plus /code-interpreter.

Example successful request: {"code":"print(15)"}; expected result is "15\n" and error is []. Error request: {"code":"x = 10\ny = 0\nresult = x / y"}; expected error is [3].

Free hosting sleeps after 15 minutes without traffic. The public URL remains the same, but the first request after sleep may wait for startup. This service does not implement artificial keep-alive traffic. AI analysis uses your separate API credits and can fail if those are exhausted.

## Execution restrictions

Submitted code runs as a separate unprivileged user with a clean environment, CPU/memory/time limits, and Linux seccomp restrictions on network access, new processes, filesystem writes, and cross-process access. API credentials remain in the privileged parent process. No secret files should be mounted or committed. The worker may read world-readable files, so keep this service dedicated to assignments. This is defense in depth, not a hardened multi-tenant sandbox or a guarantee against kernel vulnerabilities.

The Docker image is required. Native Python hosting cannot use this execution configuration. If seccomp or privilege dropping fails, requests fail closed.

## Verification status

Runner output and traceback tests can run with `python -m unittest test_runner.py -v`. Linux restrictions and live AI behavior must be verified in the deployed Docker environment before submission.
