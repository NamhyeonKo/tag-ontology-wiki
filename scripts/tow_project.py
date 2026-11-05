"""Project-session operations that write approved content to a TOW vault."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from tow_core import ConfigError, body_bytes

NOTE_FOLDERS = ("projects", "areas", "resources", "inbox")


def cmd_send(
    vault: Path,
    cfg: Mapping[str, str],
    draft: Path,
    dest: str,
    source: Path | None,
    transformed: bool,
    apply: bool,
) -> int:
    """Preview or create a new vault note from an approved project draft."""
    root = vault.resolve()
    relative = Path(dest)
    if (
        relative.is_absolute()
        or not relative.parts
        or relative.parts[0] not in {cfg[key] for key in NOTE_FOLDERS}
        or ".." in relative.parts
        or len(relative.parts) < 2
    ):
        raise ConfigError("send destination must be a vault-relative file under a configured note folder")
    target = root / relative
    if not target.resolve().is_relative_to(root):
        raise ConfigError(f"send destination must stay inside the vault: {dest}")

    if source is None:
        raise ConfigError("send requires --source")
    try:
        content = draft.read_bytes()
        source_content = source.read_bytes()
        if not transformed and body_bytes(content) != source_content:
            raise ConfigError("send draft body does not match the source")
    except OSError as e:
        raise ConfigError(f"send can't read its input: {e}") from e

    if not apply:
        print(f"would create {dest}")
        return 0

    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.parent.resolve().is_relative_to(root) or not target.resolve().is_relative_to(root):
        raise ConfigError(f"send destination must stay inside the vault: {dest}")
    fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0), 0o666)
    with os.fdopen(fd, "wb") as output:
        output.write(content)
    if target.read_bytes() != content:
        raise ConfigError(f"send verification failed: {dest}")
    print(f"created {dest}")
    return 0
