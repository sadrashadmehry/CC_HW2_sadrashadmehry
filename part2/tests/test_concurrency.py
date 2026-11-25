"""Real process contention and a subprocess check of the concurrent-next tool."""
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

from app.queue import join, take
from test_queue import _start


def test_processes_share_join_and_take_lock(tmp_path):
    path = tmp_path / "queue.txt"
    names = [f"student-{i:03d}" for i in range(40)]
    with ProcessPoolExecutor(max_workers=4) as pool:
        tickets = list(pool.map(join, [path] * len(names), names))
        assert sorted(tickets) == list(range(1, len(names) + 1))
        taken = list(pool.map(take, [path] * len(names)))
    assert sorted(taken) == names
    assert path.read_text(encoding="utf-8") == ""


def test_next_tool_checks_exact_names_and_final_empty(tmp_path):
    port = _start(tmp_path)
    for i in range(12):
        join(tmp_path / "queue.txt", f"student-{i:03d}")
    tool = Path(__file__).resolve().parents[1] / "tools" / "concurrent_next.py"
    result = subprocess.run([sys.executable, str(tool), "--url", f"http://127.0.0.1:{port}",
                             "--count", "12", "--workers", "4"],
                            capture_output=True, text=True, timeout=30)
    report = json.loads(result.stdout)
    assert result.returncode == 0, result.stderr + result.stdout
    assert report["successful"] == 12
    assert report["duplicate_names"] == {}
    assert report["final_next"] == {"status": 404, "body": "empty"}
    assert report["passed"] is True
    # Re-running on the now-empty queue must fail, not claim another success.
    result = subprocess.run([sys.executable, str(tool), "--url", f"http://127.0.0.1:{port}",
                             "--count", "1", "--workers", "1"],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 1
    assert json.loads(result.stdout)["passed"] is False
