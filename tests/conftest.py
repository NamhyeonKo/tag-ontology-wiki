import json
import shutil
import sys
import tempfile
from collections.abc import Generator, Mapping
from pathlib import Path
from typing import Any

import pytest


def fake_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, scan: dict[str, Any], outputs: Mapping[str, str] | None = None
) -> Path:
    """Point TOW_TAG_ONTOLOGY at a script that records its arguments and prints JSON.

    It prints `outputs[command]` when given, else `scan`, and exits 1 when that JSON has `"ok": false`.
    The last call's arguments go to args.json, every call's to calls.json.
    """
    (tmp_path / "scan.json").write_text(json.dumps(scan))
    (tmp_path / "outputs.json").write_text(json.dumps(dict(outputs or {})))
    script = tmp_path / "fake_cli.py"
    script.write_text(
        "import json, pathlib, sys\n"
        f"d = pathlib.Path({str(tmp_path)!r})\n"
        "(d / 'args.json').write_text(json.dumps(sys.argv[1:]))\n"
        "calls = d / 'calls.json'\n"
        "calls.write_text(json.dumps([*(json.loads(calls.read_text()) if calls.exists() else []), sys.argv[1:]]))\n"
        "text = json.loads((d / 'outputs.json').read_text()).get(sys.argv[1]) or (d / 'scan.json').read_text()\n"
        "print(text)\n"
        "sys.exit(0 if json.loads(text).get('ok', True) else 1)\n"
    )
    monkeypatch.setenv("TOW_TAG_ONTOLOGY", f"{sys.executable} {script}")
    return tmp_path


@pytest.fixture(autouse=True)
def isolate_user_config(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> Generator[None, None, None]:
    home = Path(tempfile.mkdtemp(prefix="home-", dir=tmp_path_factory.getbasetemp()))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv("TOW_VAULT", raising=False)
    try:
        yield
    finally:
        shutil.rmtree(home)
