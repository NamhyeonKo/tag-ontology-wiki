"""Shared TOW plumbing and local place resolution."""

from __future__ import annotations

import contextlib
import errno
import json
import os
import shlex
import subprocess
import tempfile
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, cast

DEFAULT_CLI: Final = "npx --yes tag-ontology@0.2.0"
VaultSource = Literal["--root", "TOW_VAULT", "user", "ancestor"]
VaultLayout = Literal["tow", "legacy", "plain"]


class ConfigError(Exception):
    """Invalid or unavailable TOW configuration."""


class CliError(Exception):
    """The tag-ontology command could not be run."""


def body_bytes(content: bytes) -> bytes:
    """Body after a leading, delimiter-only frontmatter block; no YAML or Markdown interpretation."""
    lines = content.splitlines(keepends=True)
    if not lines or lines[0].removeprefix(b"\xef\xbb\xbf").rstrip(b"\r\n") != b"---":
        return content
    for index, line in enumerate(lines[1:], 1):
        if line.rstrip(b"\r\n") == b"---":
            return b"".join(lines[index + 1 :])
    raise ConfigError("can't verify body: leading frontmatter has no closing '---' line")


def run_cli(args: list[str], capture: bool) -> subprocess.CompletedProcess[str]:
    command = shlex.split(os.environ.get("TOW_TAG_ONTOLOGY", DEFAULT_CLI))
    try:
        return subprocess.run([*command, *args], capture_output=capture, text=True, check=False)
    except FileNotFoundError as e:
        raise CliError(f"can't run the tag-ontology CLI ({e.filename}); it needs Node.js") from e


def serialize_entries(entries: Mapping[str, object]) -> str:
    """Serialize dictionary entries as stable, one-entry-per-line JSON."""
    lines = [
        f"{json.dumps(key, ensure_ascii=False)}: "
        f"{json.dumps(entries[key], ensure_ascii=False, separators=(', ', ': '))}"
        for key in sorted(entries)
    ]
    return "{\n" + ",\n".join(lines) + ("\n" if lines else "") + "}\n"


def user_config_file() -> Path:
    return Path.home() / ".tow" / "config.json"


def write_text_atomic(path: Path, text: str, *, exclusive: bool = False) -> None:
    """Atomically write UTF-8 text; exclusive writes never replace an existing path."""
    if exclusive and (path.exists() or path.is_symlink()):
        raise FileExistsError(f"file exists: {path}")
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as file:
            temporary = file.name
            file.write(text)
        if exclusive:
            with open(temporary, "rb") as file:
                data = file.read()
            try:
                os.link(temporary, path)
            except OSError as e:
                if e.errno not in {errno.EPERM, errno.ENOTSUP, errno.EOPNOTSUPP, errno.EXDEV, errno.ENOSYS}:
                    raise
                fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0), 0o666)
                try:
                    with os.fdopen(fd, "wb") as file:
                        file.write(data)
                except BaseException:
                    with contextlib.suppress(OSError):
                        path.unlink()
                    raise
            os.unlink(temporary)
        else:
            os.replace(temporary, path)
    finally:
        if temporary is not None and os.path.exists(temporary):
            os.unlink(temporary)


def write_user_config(vault: Path) -> None:
    """Connect this user to a configured TOW vault."""
    if not vault.is_absolute() or not (tow_kind(vault) == "vault" or is_legacy_vault(vault)):
        raise ConfigError(f"not a TOW vault; run setup inside the vault first: {vault}")
    path = user_config_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text_atomic(path, json.dumps({"kind": "user", "vault": str(vault)}, indent=2))


def read_user_config() -> str | None:
    path = user_config_file()
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as e:
        raise ConfigError(f"invalid user config {path}: {e}") from e
    if not isinstance(raw, dict):
        raise ConfigError(f'invalid user config {path}: expected {{"kind": "user", "vault": <absolute path>}}')
    data = cast(dict[str, object], raw)
    vault = data.get("vault")
    if (
        set(data) != {"kind", "vault"}
        or data.get("kind") != "user"
        or not isinstance(vault, str)
        or not Path(vault).is_absolute()
    ):
        raise ConfigError(f'invalid user config {path}: expected {{"kind": "user", "vault": <absolute path>}}')
    return vault


def upward(start: Path) -> Iterator[Path]:
    """Yield start and ancestors, excluding home itself when start is under home."""
    current = start.resolve()
    home = Path.home().resolve()
    under_home = current.is_relative_to(home)
    while not (under_home and current == home):
        yield current
        if current.parent == current:
            break
        current = current.parent


def tow_kind(folder: Path) -> str | None:
    """Return the kind in folder/.tow/config.json, or None if unavailable."""
    try:
        raw = json.loads((folder / ".tow" / "config.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict):
        return None
    kind = cast(dict[str, object], raw).get("kind")
    return kind if isinstance(kind, str) else None


def is_empty_plugin_dictionary(folder: Path) -> bool:
    try:
        value: object = json.loads((folder / "Tag-Dictionary.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(value, dict) and not value


def is_legacy_vault(folder: Path) -> bool:
    if (folder / "tow.json").is_file() or (folder / "Category-Dictionary.md").is_file():
        return True
    tag_dictionary = folder / "Tag-Dictionary.json"
    return tag_dictionary.is_file() and not is_empty_plugin_dictionary(folder)


@dataclass(frozen=True)
class VaultRef:
    root: Path
    source: VaultSource
    layout: VaultLayout


def _configured_vault(value: str | Path, cwd: Path, source: VaultSource) -> VaultRef:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = cwd / path
    root = path.resolve()
    if not root.is_dir():
        raise ConfigError(f"configured vault does not exist or is not a directory: {root}")
    if tow_kind(root) == "vault":
        layout: Literal["tow", "legacy", "plain"] = "tow"
    elif is_legacy_vault(root):
        layout = "legacy"
    else:
        layout = "plain"
    return VaultRef(root=root, source=source, layout=layout)


def resolve_vault(cwd: Path, root_arg: Path | None, env: Mapping[str, str]) -> VaultRef:
    """Resolve the vault from an explicit root, cwd ancestors, then personal connection."""
    if root_arg is not None:
        return _configured_vault(root_arg, cwd, "--root")

    ancestors = list(upward(cwd))
    for folder in ancestors:
        if tow_kind(folder) == "vault":
            return _configured_vault(folder, cwd, "ancestor")
    for folder in ancestors:
        if is_legacy_vault(folder):
            return _configured_vault(folder, cwd, "ancestor")
    env_vault = env.get("TOW_VAULT")
    if env_vault:
        return _configured_vault(env_vault, cwd, "TOW_VAULT")
    user_vault = read_user_config()
    if user_vault is not None:
        return _configured_vault(user_vault, cwd, "user")
    raise ConfigError("no vault found; run tow-setup")


def resolve_project(cwd: Path, vault: Path | None) -> Path | None:
    """Resolve a project root, unless cwd is inside the vault."""
    current = cwd.resolve()
    if vault is not None and current.is_relative_to(vault.resolve()):
        return None
    for folder in upward(current):
        if tow_kind(folder) == "project":
            return folder
    try:
        result = subprocess.run(
            ["git", "-C", str(current), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        result = None
    if result is not None and result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    return current
