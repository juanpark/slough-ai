"""Unified entrypoint — routes to the correct process based on SERVICE_TYPE."""

import os
import subprocess
import sys

SERVICE_TYPE = os.environ.get("SERVICE_TYPE", "web")

COMMANDS = {
    "web": ["python", "src/app.py"],
    "worker": ["celery", "-A", "src.worker", "worker", "--loglevel=info"],
    "beat": ["celery", "-A", "src.worker", "beat", "--loglevel=info"],
}

cmd = COMMANDS.get(SERVICE_TYPE)
if cmd is None:
    print(f"Unknown SERVICE_TYPE: {SERVICE_TYPE!r}. Must be one of: {', '.join(COMMANDS)}")
    sys.exit(1)

print(f"Starting {SERVICE_TYPE}: {' '.join(cmd)}")
os.execvp(cmd[0], cmd)
