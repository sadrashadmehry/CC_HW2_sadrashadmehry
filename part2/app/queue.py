"""Lab queue stored as UTF-8 names, one per line."""
from pathlib import Path
import os
import tempfile
import time


def join(path: str | Path, name: str) -> int:
    """Validate and append a name; return the resulting queue length."""
    if not isinstance(name, str) or name.splitlines() != [name]:
        raise ValueError("Name must be a single line")
    name = name.strip()
    if not name or len(name) > 40:
        raise ValueError("Name must contain 1 to 40 characters")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # shortcut: no cross-process lock yet; add shared locking in section 5.3.
    with path.open("a+", encoding="utf-8", newline="\n") as queue:
        queue.write(name + "\n")
        queue.flush()
        # shortcut: expose the unlocked race with 10 ms delay; remove with the 5.3 lock.
        time.sleep(0.01)
        queue.seek(0)
        return sum(1 for _ in queue)


def take(path: str | Path) -> str:
    """Remove the first person, or raise LookupError for a missing/empty queue."""
    path = Path(path)
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

