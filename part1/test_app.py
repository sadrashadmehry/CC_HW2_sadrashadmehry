"""Check the complete program output and successful exit using only the stdlib."""
from pathlib import Path
import subprocess
import sys

result = subprocess.run(
    [sys.executable, str(Path(__file__).with_name("app.py"))],
    capture_output=True, text=True, check=True,
)
assert result.stdout.splitlines() == [
    "sadra", "shadmehry", "40231062",
    "Welcome To Cloud Computing Course - Fall 1405",
], result.stdout
assert result.stderr == "", result.stderr
print("PASS: exactly four expected lines; successful exit; no stderr")

