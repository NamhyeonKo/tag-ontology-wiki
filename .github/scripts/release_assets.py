"""Build and check TOW release archives from one committed revision.

Writes `tow-<version>.zip` (portable/Claude/Codex), `tow-antigravity-<version>.zip` (native
Antigravity manifest at the root) and `SHA256SUMS` into `--out`, following the distribution
procedure in docs/release-readiness.md. Uses only git and the Python standard library.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import subprocess
import sys
import zipfile
from pathlib import Path

PREFIX = "tow/"
MANIFESTS = ("plugin.json", ".claude-plugin/plugin.json", ".antigravity-plugin/plugin.json")
OVERLAY = f"{PREFIX}.antigravity-plugin/plugin.json"
HELPER = f"{PREFIX}scripts/tow.py"


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout


def versions(ref: str) -> dict[str, str]:
    """The version each project file declares at `ref`."""
    pyproject = git("show", f"{ref}:pyproject.toml").decode()
    found = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
    result = {"pyproject.toml": found.group(1) if found else ""}
    for path in MANIFESTS:
        result[path] = str(json.loads(git("show", f"{ref}:{path}"))["version"])
    return result


def antigravity(portable: Path, target: Path) -> None:
    """Copy `portable` with the native overlay as its root manifest and no nested overlay copy."""
    with zipfile.ZipFile(portable) as source, zipfile.ZipFile(target, "w") as out:
        out.comment = source.comment
        overlay = source.read(OVERLAY)
        for info in source.infolist():
            if info.filename != OVERLAY:
                out.writestr(info, overlay if info.filename == f"{PREFIX}plugin.json" else source.read(info))


def problems(archive: Path, *, native: bool) -> list[str]:
    found: list[str] = []
    with zipfile.ZipFile(archive) as z:
        if (bad := z.testzip()) is not None:
            found.append(f"{archive.name}: corrupt entry {bad}")
        names = z.namelist()
        if HELPER not in names or stat.S_IMODE(z.getinfo(HELPER).external_attr >> 16) != 0o755:
            found.append(f"{archive.name}: {HELPER} is missing or not executable")
        links = [i.filename for i in z.infolist() if stat.S_ISLNK(i.external_attr >> 16)]
        if links:
            found.append(f"{archive.name}: symbolic links {links}")
        if native and OVERLAY in names:
            found.append(f"{archive.name}: still contains the nested overlay")
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="release version without the leading v, e.g. 0.4.2")
    parser.add_argument("--ref", default="HEAD", help="committed revision to archive (default: HEAD)")
    parser.add_argument("--out", required=True, type=Path, help="output directory (created if missing)")
    args = parser.parse_args(argv)

    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version):
        print(f"release_assets: version must look like 0.4.2, got {args.version!r}", file=sys.stderr)
        return 1
    declared = versions(args.ref)
    if mismatched := {path: value for path, value in declared.items() if value != args.version}:
        print(f"release_assets: {args.ref} does not declare {args.version}: {mismatched}", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    portable = args.out / f"tow-{args.version}.zip"
    native = args.out / f"tow-antigravity-{args.version}.zip"
    git("archive", "--format=zip", f"--prefix={PREFIX}", f"--output={portable}", args.ref)
    antigravity(portable, native)
    with zipfile.ZipFile(portable) as z:
        overlay = z.read(OVERLAY)
    with zipfile.ZipFile(native) as z:
        same_root = z.read(f"{PREFIX}plugin.json") == overlay
    found = [*problems(portable, native=False), *problems(native, native=True)]
    if not same_root:
        found.append(f"{native.name}: root manifest differs from the Antigravity overlay")
    if found:
        print("release_assets: " + "; ".join(found), file=sys.stderr)
        return 1

    sums = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in (portable, native))
    (args.out / "SHA256SUMS").write_text(sums)
    commit = git("rev-parse", f"{args.ref}^{{commit}}").decode().strip()
    print(f"Archived {commit} as {args.version}")
    print(sums, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
