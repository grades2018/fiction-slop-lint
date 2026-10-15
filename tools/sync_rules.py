#!/usr/bin/env python3
"""Copy the packaged rules.json to docs/ so the browser version uses the same file."""
import shutil
from pathlib import Path

root = Path(__file__).resolve().parent.parent
shutil.copyfile(root / "fiction_slop_lint" / "data" / "rules.json", root / "docs" / "rules.json")
print("synced docs/rules.json")
