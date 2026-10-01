"""Check Python syntax, JSON/TOML, and relative documentation links; not hardware behavior."""

import ast
import json
from pathlib import Path
import re
import tomllib
from urllib.parse import unquote, urlsplit


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    for directory in (root / "src", root / "scripts", root / "tests", root / "verifier"):
        for path in directory.rglob("*.py"):
            ast.parse(path.read_text(), filename=str(path))
    tomllib.loads((root / "pyproject.toml").read_text())
    json.loads((root / "Countertrace.code-workspace").read_text())
    for path in (root / "fixtures").rglob("*.json"):
        json.loads(path.read_text())
    documents = [root / "README.md", root / "AGENTS.md", root / "THIRD_PARTY_NOTICES.md"]
    for directory in ("docs", "apps", "verifier", "fixtures", "evaluation", "recorded"):
        documents.extend(p for p in (root / directory).rglob("*.md")
                         if "node_modules" not in p.parts and "dist" not in p.parts)
    missing = []
    for path in documents:
        for target in re.findall(r"\[[^\]]*\]\(([^\s)]+)\)", path.read_text()):
            url = urlsplit(target)
            if url.scheme or url.netloc or not url.path:
                continue
            if not (path.parent / unquote(url.path)).exists():
                missing.append(f"{path.relative_to(root)}: {target}")
    if missing:
        raise SystemExit("Missing local links:\n" + "\n".join(missing))
    print("Python syntax, JSON/TOML, and local documentation links are valid.")
    print("This check performs no RTL verification, model evaluation, or hardware proof.")


if __name__ == "__main__":
    main()
