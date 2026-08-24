#!/usr/bin/env python3
"""Prove scripts/validate.py refuses what it is supposed to refuse.

A validator that only ever passes is decoration. This copies the real synced
component into a scratch directory, breaks it one way at a time, and checks
that each break is actually caught -- and that the untouched copy still passes.

Usage:
    python scripts/test_validate.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPONENT = REPO_ROOT / "custom_components" / "ecosmart"


def run_validate(root: Path) -> tuple[int, str]:
    """Run validate.py against a scratch copy of the repo."""
    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "validate.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout + result.stderr


def scratch_copy(into: Path) -> Path:
    """Lay out a minimal repo -- the validator only needs these two folders."""
    (into / "scripts").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "scripts" / "validate.py", into / "scripts" / "validate.py")
    shutil.copytree(COMPONENT, into / "custom_components" / "ecosmart")
    return into


def drop_translations(root: Path) -> None:
    (root / "custom_components" / "ecosmart" / "translations" / "en.json").unlink()


def add_stray_file(root: Path) -> None:
    (root / "custom_components" / "ecosmart" / "notes.txt").write_text("stray\n")


def strip_version(root: Path) -> None:
    path = root / "custom_components" / "ecosmart" / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    del manifest["version"]
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def strip_issue_tracker(root: Path) -> None:
    path = root / "custom_components" / "ecosmart" / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    del manifest["issue_tracker"]
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def break_json(root: Path) -> None:
    (root / "custom_components" / "ecosmart" / "icons.json").write_text("{ not json", encoding="utf-8")


def desync_translation(root: Path) -> None:
    """Change literal English so it no longer matches strings.json."""
    path = root / "custom_components" / "ecosmart" / "translations" / "en.json"
    english = json.loads(path.read_text(encoding="utf-8"))
    english["config"]["step"]["user"]["description"] = "Something else entirely."
    path.write_text(json.dumps(english, indent=4) + "\n", encoding="utf-8")


CASES: list[tuple[str, Callable[[Path], None], str]] = [
    ("translations/en.json deleted", drop_translations, "translations/en.json"),
    ("stray file added", add_stray_file, "unexpected file notes.txt"),
    ("manifest version removed", strip_version, "missing required key 'version'"),
    ("manifest issue_tracker removed", strip_issue_tracker, "issue_tracker"),
    ("icons.json corrupted", break_json, "does not parse"),
    ("en.json text drifted from strings.json", desync_translation, "differs from strings.json"),
]


def main() -> int:
    """Run the control case and every refusal case."""
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        code, output = run_validate(scratch_copy(Path(tmp) / "control"))
        if code == 0:
            print("PASS  control: an untouched copy validates")
        else:
            failures.append("control copy did not validate")
            print(f"FAIL  control: expected pass, got exit {code}\n{output}")

    for index, (name, mutate, expected) in enumerate(CASES):
        with tempfile.TemporaryDirectory() as tmp:
            root = scratch_copy(Path(tmp) / f"case{index}")
            mutate(root)
            code, output = run_validate(root)
            if code != 0 and expected in output:
                print(f"PASS  refused: {name}")
            elif code == 0:
                failures.append(f"{name}: validator passed a broken copy")
                print(f"FAIL  accepted: {name}")
            else:
                failures.append(f"{name}: failed for the wrong reason")
                print(f"FAIL  wrong reason: {name} -- wanted {expected!r}\n{output}")

    print()
    if failures:
        print(f"FAIL: {len(failures)} case(s)")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(f"PASS: 1 control + {len(CASES)} refusal cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
