#!/usr/bin/env python3
"""Prove the generated custom component is shippable.

Run it after every sync and in CI. It answers four questions:

1. Does every JSON file parse?
2. Does manifest.json carry what a *custom* component needs -- domain, version,
   issue_tracker, a `documentation` URL pointing at this repo rather than at the
   core documentation page, requirements -- as well as the keys core requires?
3. Is translations/en.json there, and does it actually say what strings.json
   says? (Core generates this file and gitignores it; a custom component that
   ships without it shows raw translation keys in the config dialog.)
4. Is the file set exactly what it should be -- core's component files plus the
   generated translations, and nothing else?

Point 4 is a hardcoded list on purpose. If a future core change adds a file, this
fails and a human decides whether it belongs here, rather than a stray file
riding along unnoticed. With ``--core <path>`` it additionally compares against
the live core checkout, which is the stronger check when it is available.

Usage:
    python scripts/validate.py [--core /root/src/ha-core]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPONENT = REPO_ROOT / "custom_components" / "ecosmart"

#: Exactly what a synced copy contains: core's ten files plus generated English.
EXPECTED_FILES = frozenset(
    {
        "__init__.py",
        "config_flow.py",
        "const.py",
        "coordinator.py",
        "entity.py",
        "icons.json",
        "manifest.json",
        "quality_scale.yaml",
        "sensor.py",
        "strings.json",
        "translations/en.json",
    }
)

#: Keys core requires, plus the two only a custom component may carry.
REQUIRED_MANIFEST_KEYS = (
    "domain",
    "name",
    "codeowners",
    "documentation",
    "requirements",
    "version",
    "issue_tracker",
)

#: Where a *custom* component's documentation must point. hassfest refuses a
#: custom component that claims the core page on home-assistant.io.
DOCUMENTATION_URL = "https://github.com/ecosmart-nz/ecosmart-homeassistant"

#: The only manifest keys the sync may differ from core on.
EXPECTED_MANIFEST_DELTAS = frozenset({"version", "issue_tracker", "documentation"})

#: A `[%key:common::config_flow::error::cannot_connect%]` style reference.
REFERENCE = re.compile(r"^\[%key:[^%]+%\]$")

VERSION = re.compile(r"^\d+\.\d+\.\d+([.\-+][0-9A-Za-z.\-+]+)?$")

problems: list[str] = []


def fail(message: str) -> None:
    """Record a problem instead of stopping, so one run reports everything."""
    problems.append(message)


def present_files() -> set[str]:
    """Every shipped file, as a POSIX path relative to the component folder."""
    return {
        path.relative_to(COMPONENT).as_posix()
        for path in COMPONENT.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }


def check_json_parses() -> dict[str, object]:
    """Parse every JSON file; return the ones later checks need."""
    parsed: dict[str, object] = {}
    for path in sorted(COMPONENT.rglob("*.json")):
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(COMPONENT).as_posix()
        try:
            parsed[relative] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            fail(f"{relative}: does not parse -- {error}")
    return parsed


def check_manifest(manifest: object) -> None:
    """The manifest must name the domain, a version and where to file bugs."""
    if not isinstance(manifest, dict):
        fail("manifest.json: not a JSON object")
        return

    for key in REQUIRED_MANIFEST_KEYS:
        if key not in manifest:
            fail(f"manifest.json: missing required key '{key}'")

    if manifest.get("domain") != "ecosmart":
        fail(f"manifest.json: domain is {manifest.get('domain')!r}, expected 'ecosmart'")

    version = manifest.get("version")
    if isinstance(version, str):
        if not VERSION.match(version):
            fail(f"manifest.json: version {version!r} is not a release-looking version")
    elif version is not None:
        fail("manifest.json: version must be a string")

    documentation = manifest.get("documentation")
    if documentation is not None and documentation != DOCUMENTATION_URL:
        fail(
            f"manifest.json: documentation is {documentation!r}, expected "
            f"{DOCUMENTATION_URL!r} -- a custom component may not claim the core "
            "documentation page, and hassfest refuses one that does"
        )

    tracker = manifest.get("issue_tracker")
    if isinstance(tracker, str):
        if not tracker.startswith("https://"):
            fail(f"manifest.json: issue_tracker {tracker!r} is not an https URL")
    elif tracker is not None:
        fail("manifest.json: issue_tracker must be a string")

    requirements = manifest.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        fail("manifest.json: requirements must be a non-empty list")
    elif not any(str(item).startswith("aioecosmart") for item in requirements):
        fail(f"manifest.json: requirements {requirements!r} does not pin aioecosmart")


def compare_translations(strings: object, english: object) -> None:
    """en.json must say what strings.json says, with references resolved.

    Literal text has to match exactly. Where strings.json holds a
    `[%key:...%]` pointer at Home Assistant's shared wording, en.json is only
    required to hold some real English in its place -- the shared text is core's
    to change, not ours.
    """
    if not isinstance(strings, dict) or not isinstance(english, dict):
        fail("strings.json / translations/en.json: not JSON objects")
        return

    def walk(left: object, right: object, path: str) -> None:
        if isinstance(left, dict):
            if not isinstance(right, dict):
                fail(f"translations/en.json: {path} should be an object")
                return
            missing = set(left) - set(right)
            extra = set(right) - set(left)
            for key in sorted(missing):
                fail(f"translations/en.json: missing {path}.{key}")
            for key in sorted(extra):
                fail(f"translations/en.json: unexpected {path}.{key}")
            for key in sorted(set(left) & set(right)):
                walk(left[key], right[key], f"{path}.{key}")
            return
        if isinstance(left, str):
            if REFERENCE.match(left):
                if not isinstance(right, str) or not right.strip():
                    fail(f"translations/en.json: {path} did not resolve to English")
            elif left != right:
                fail(f"translations/en.json: {path} differs from strings.json")

    # The config step is the one the brief names, but the whole tree is cheap.
    walk(strings, english, "")


def compare_with_core(core: Path) -> None:
    """Byte-compare against the core checkout -- the real source of truth."""
    source = core / "homeassistant" / "components" / "ecosmart"
    if not source.is_dir():
        fail(f"--core: no component at {source}")
        return

    core_files = {
        path.relative_to(source).as_posix()
        for path in source.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
    here = present_files()

    # translations/en.json is gitignored in core; it may or may not exist there.
    expected = core_files | {"translations/en.json"}
    if here != expected:
        for name in sorted(expected - here):
            fail(f"core comparison: {name} is in core but not synced")
        for name in sorted(here - expected):
            fail(f"core comparison: {name} is synced but not in core")

    for name in sorted(core_files & here):
        if name == "manifest.json":
            continue  # deliberately differs: version, issue_tracker, documentation
        if (source / name).read_bytes() != (COMPONENT / name).read_bytes():
            fail(f"core comparison: {name} differs from core")

    # The manifest may differ from core's on exactly three keys and no others:
    # the two core forbids, plus documentation, which a custom component must
    # point at its own repo.
    try:
        core_manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
        here_manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"core comparison: cannot read a manifest -- {error}")
        return

    sentinel = object()
    deltas = {
        key
        for key in set(core_manifest) | set(here_manifest)
        if core_manifest.get(key, sentinel) != here_manifest.get(key, sentinel)
    }
    if deltas != set(EXPECTED_MANIFEST_DELTAS):
        for key in sorted(deltas - EXPECTED_MANIFEST_DELTAS):
            fail(f"core comparison: manifest key '{key}' was changed by the sync")
        for key in sorted(EXPECTED_MANIFEST_DELTAS - deltas):
            fail(f"core comparison: manifest key '{key}' was NOT changed by the sync")

    if here_manifest.get("documentation") != DOCUMENTATION_URL:
        fail(
            f"core comparison: manifest documentation is "
            f"{here_manifest.get('documentation')!r}, expected {DOCUMENTATION_URL!r}"
        )


def main() -> int:
    """Run every check and print a single verdict."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", type=Path, help="core checkout to compare against")
    args = parser.parse_args()

    if not COMPONENT.is_dir():
        print(f"FAIL: no component at {COMPONENT} -- run scripts/sync-from-core.sh")
        return 1

    files = present_files()
    print(f"component: {COMPONENT.relative_to(REPO_ROOT).as_posix()} ({len(files)} files)")
    for name in sorted(files):
        print(f"  {name}")

    parsed = check_json_parses()

    if files != set(EXPECTED_FILES):
        for name in sorted(EXPECTED_FILES - files):
            fail(f"file set: expected {name}, not found")
        for name in sorted(files - set(EXPECTED_FILES)):
            fail(f"file set: unexpected file {name}")

    if "manifest.json" in parsed:
        check_manifest(parsed["manifest.json"])

    if "translations/en.json" not in files:
        fail("translations/en.json is missing -- the config dialog would show raw keys")
    elif "strings.json" in parsed and "translations/en.json" in parsed:
        compare_translations(parsed["strings.json"], parsed["translations/en.json"])

    if args.core:
        compare_with_core(args.core)

    print()
    if problems:
        print(f"FAIL: {len(problems)} problem(s)")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    manifest = parsed.get("manifest.json", {})
    assert isinstance(manifest, dict)
    print(
        f"PASS: {len(files)} files, JSON valid, manifest v{manifest.get('version')} "
        f"({manifest.get('requirements')}), translations match strings"
        + (", byte-identical to core" if args.core else "")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
