import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _temp_cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """テスト用の一時キャッシュディレクトリを設定する。"""
    monkeypatch.setattr("app.config.settings.cache_dir", str(tmp_path / "data"))
    monkeypatch.setattr("app.config.settings.quants_api_v2_api_key", "test_token")
    os.makedirs(tmp_path / "data", exist_ok=True)
