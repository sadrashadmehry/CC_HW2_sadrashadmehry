"""Render a publication copy without changing the version placeholder in Git."""
import argparse
from pathlib import Path
import re


def render(version: str, output: Path) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", version):
        raise ValueError("Invalid release version")
    source = Path(__file__).resolve().parents[1] / "site" / "index.html"
    html = source.read_text(encoding="utf-8-sig")
    if html.count("__VERSION__") != 1:
        raise ValueError("Expected exactly one version placeholder")
    output.mkdir(parents=True, exist_ok=True)
    (output / "index.html").write_text(html.replace("__VERSION__", version), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    render(args.version, args.output)
