"""Lab queue stored as UTF-8 names, one per line."""
from contextlib import contextmanager
from pathlib import Path
import os
import tempfile


@contextmanager
def _locked(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Lock a stable file: replacing the queue must not replace its lock inode.
    with path.with_name(path.name + ".lock").open("a+b") as lock:
        if os.name == "nt":
            import msvcrt
            if lock.seek(0, os.SEEK_END) == 0:
                lock.write(b"\0")
                lock.flush()
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        # Closing the independently opened handle releases the lock on all exits.
        yield


def join(path: str | Path, name: str) -> int:
    """Validate and append a name; return the resulting queue length."""
    if not isinstance(name, str) or name.splitlines() != [name]:
        raise ValueError("Name must be a single line")
    name = name.strip()
    if not name or len(name) > 40:
        raise ValueError("Name must contain 1 to 40 characters")
    path = Path(path)
    with _locked(path):
        with path.open("a+", encoding="utf-8", newline="\n") as queue:
            queue.write(name + "\n")
            queue.flush()
            queue.seek(0)
            return sum(1 for _ in queue)


def take(path: str | Path) -> str:
    """Remove the first person, or raise LookupError for a missing/empty queue."""
    path = Path(path)
    with _locked(path):
        try:
            names = path.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            raise LookupError("empty") from None
        if not names:
            raise LookupError("empty")
        # Replace only after writing succeeds, preserving the queue on write failure.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                             dir=path.parent, delete=False) as output:
                temporary = Path(output.name)
                output.writelines(name + "\n" for name in names[1:])
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return names[0]
