#!/usr/bin/env bash
#
# Regenerate custom_components/ecosmart/ from the home-assistant/core working tree.
#
# The integration is written once, in core. This repo only republishes it in the
# shape a manually installed custom component needs: the two manifest keys core
# forbids (`version`, `issue_tracker`) and the translations file core generates
# but does not commit. Nothing here is ever hand-edited -- edit core, re-run this.
#
# Usage (from anywhere, inside WSL / Linux):
#     scripts/sync-from-core.sh [version]
#
#     version        release tag to stamp into manifest.json  (default 0.1.0)
#     CORE_REPO      core checkout                            (default /root/src/ha-core)
#     CORE_BRANCH    branch that must be checked out there    (default ecosmart-integration)
#     ALLOW_BRANCH_MISMATCH=1   sync anyway from another branch
#
# Idempotent: running it twice with the same arguments leaves the tree unchanged.

set -euo pipefail

VERSION="${1:-0.1.0}"
CORE_REPO="${CORE_REPO:-/root/src/ha-core}"
CORE_BRANCH="${CORE_BRANCH:-ecosmart-integration}"
ISSUE_TRACKER="${ISSUE_TRACKER:-https://github.com/ecosmart-nz/ecosmart-homeassistant/issues}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$CORE_REPO/homeassistant/components/ecosmart"
DEST="$REPO_ROOT/custom_components/ecosmart"

if [ ! -d "$SRC" ]; then
    echo "ERROR: no component at $SRC" >&2
    echo "       Set CORE_REPO to a core checkout that has the ecosmart branch." >&2
    exit 2
fi

if [ -d "$CORE_REPO/.git" ]; then
    ON="$(git -C "$CORE_REPO" branch --show-current || true)"
    if [ "$ON" != "$CORE_BRANCH" ] && [ "${ALLOW_BRANCH_MISMATCH:-0}" != "1" ]; then
        echo "ERROR: $CORE_REPO is on '$ON', expected '$CORE_BRANCH'." >&2
        echo "       Re-run with ALLOW_BRANCH_MISMATCH=1 if that is deliberate." >&2
        exit 2
    fi
    CORE_SHA="$(git -C "$CORE_REPO" rev-parse --short HEAD)"
    CORE_DIRTY="$(git -C "$CORE_REPO" status --porcelain -- homeassistant/components/ecosmart | wc -l)"
else
    CORE_SHA="(not a git checkout)"
    CORE_DIRTY=0
fi

echo "source : $SRC"
echo "branch : ${ON:-n/a} @ $CORE_SHA${CORE_DIRTY:+ (uncommitted component changes: $CORE_DIRTY)}"
echo "target : $DEST"
echo "version: $VERSION"
echo

# Keep the previous tree so the run can show what actually moved.
PREV="$(mktemp -d)"
trap 'rm -rf "$PREV"' EXIT
if [ -d "$DEST" ]; then
    cp -a "$DEST/." "$PREV/"
fi

rm -rf "$DEST"
mkdir -p "$DEST"
# tar rather than rsync: no extra dependency, and the excludes are exact.
(cd "$SRC" && tar --exclude='__pycache__' --exclude='*.pyc' --exclude='.mypy_cache' -cf - .) \
    | (cd "$DEST" && tar -xf -)

# --- manifest: add what a custom component requires and core forbids ----------
python3 - "$DEST/manifest.json" "$VERSION" "$ISSUE_TRACKER" <<'PY'
import json
import sys

path, version, issue_tracker = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path, encoding="utf-8") as handle:
    manifest = json.load(handle)

if "version" in manifest or "issue_tracker" in manifest:
    # Core rejects both keys, so seeing them here means the source is not core.
    raise SystemExit(f"ERROR: {path} already carries version/issue_tracker -- wrong source?")

manifest["version"] = version
manifest["issue_tracker"] = issue_tracker

# Home Assistant's own ordering: domain and name first, the rest alphabetical.
lead = ["domain", "name"]
ordered = {key: manifest[key] for key in lead if key in manifest}
ordered.update({key: manifest[key] for key in sorted(manifest) if key not in lead})

with open(path, "w", encoding="utf-8", newline="\n") as handle:
    json.dump(ordered, handle, indent=2)
    handle.write("\n")
print("manifest: version + issue_tracker injected")
PY

# --- translations: core generates en.json but gitignores it -------------------
# The frontend of a custom component reads translations/en.json out of the
# component folder, so it has to ship. Prefer the file core's own tooling
# generated; fall back to resolving strings.json's [%key:...%] references
# against core's shared strings.
if [ -f "$SRC/translations/en.json" ]; then
    mkdir -p "$DEST/translations"
    cp "$SRC/translations/en.json" "$DEST/translations/en.json"
    echo "translations: copied core's generated en.json"
else
    echo "translations: core has no generated en.json -- resolving from strings.json"
    python3 - "$DEST/strings.json" "$CORE_REPO/homeassistant/strings.json" \
             "$DEST/translations/en.json" <<'PY'
import json
import os
import re
import sys

component_path, common_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
REFERENCE = re.compile(r"^\[%key:([^%]+)%\]$")

with open(component_path, encoding="utf-8") as handle:
    strings = json.load(handle)
with open(common_path, encoding="utf-8") as handle:
    common = json.load(handle)


def lookup(dotted: str) -> str:
    """Resolve a `common::config_flow::error::x` style reference."""
    node = common
    for part in dotted.split("::"):
        node = node[part]
    if not isinstance(node, str):
        raise SystemExit(f"ERROR: reference {dotted} is not a string")
    return node


def resolve(node):
    if isinstance(node, dict):
        return {key: resolve(value) for key, value in node.items()}
    if isinstance(node, str):
        match = REFERENCE.match(node)
        if match:
            return lookup(match.group(1))
    return node


os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
    json.dump(resolve(strings), handle, indent=4, ensure_ascii=False)
    handle.write("\n")
print("translations: generated en.json from strings.json")
PY
fi

# --- prove the result before anyone commits it --------------------------------
echo
python3 "$REPO_ROOT/scripts/validate.py" --core "$CORE_REPO"

# --- summary diff -------------------------------------------------------------
echo
echo "--- changes against the previous synced copy ---"
if diff -ru "$PREV" "$DEST" > /dev/null 2>&1; then
    echo "(no change -- the committed copy was already current)"
else
    diff -ru "$PREV" "$DEST" || true
fi
