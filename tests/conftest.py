import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


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
