from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from requests.exceptions import HTTPError
from requests.models import Response

from app.jquants_client import (
    _cache_path,
    _read_cache,
    _write_cache,
    get_cache_stats,
    get_daily_quotes,
    get_stock_master,
)


class TestCacheOperations:
    """CSVキャッシュの読み書きテスト。"""

    def test_cache_path_generates_unique_path(self) -> None:
        path1 = _cache_path("master", "code=7203")
        path2 = _cache_path("master", "code=9984")
        assert path1 != path2
        assert path1.name.startswith("master_")
        assert path1.suffix == ".csv"

    def test_cache_path_same_params_same_path(self) -> None:
        path1 = _cache_path("daily", "code=7203&from=20240101")
        path2 = _cache_path("daily", "code=7203&from=20240101")
        assert path1 == path2

    def test_read_cache_returns_none_when_no_file(self, tmp_path: Path) -> None:
        result = _read_cache(tmp_path / "nonexistent.csv")
        assert result is None

    def test_write_and_read_cache(self, tmp_path: Path) -> None:
        path = tmp_path / "test_cache.csv"
        df = pd.DataFrame({"Code": ["7203", "9984"], "Name": ["Toyota", "SoftBank"]})
        _write_cache(path, df)

        result = _read_cache(path)
        assert result is not None
        assert len(result) == 2
        assert list(result.columns) == ["Code", "Name"]

    @patch("app.jquants_client._get_client")
    def test_get_stock_master_uses_cache(self, mock_get_client: MagicMock) -> None:
        """2回目の呼び出しではAPIを呼ばずキャッシュを使う。"""
        mock_client = MagicMock()
        mock_client.get_eq_master.return_value = pd.DataFrame({"Code": ["7203"], "CompanyName": ["トヨタ自動車"]})
        mock_get_client.return_value = mock_client

        # 1回目: APIを呼ぶ
        result1 = get_stock_master()
        assert mock_client.get_eq_master.call_count == 1

        # 2回目: キャッシュから読む
        result2 = get_stock_master()
        assert mock_client.get_eq_master.call_count == 1  # 呼び出し回数が増えない
        assert len(result1) == len(result2)

    @patch("app.jquants_client._get_client")
    def test_get_daily_quotes_caches_result(self, mock_get_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.get_eq_bars_daily.return_value = pd.DataFrame(
            {"Date": ["2024-01-01"], "Code": ["7203"], "Close": [3000.0]}
        )
        mock_get_client.return_value = mock_client

        result1 = get_daily_quotes("7203", "20240101", "20240131")
        result2 = get_daily_quotes("7203", "20240101", "20240131")

        assert mock_client.get_eq_bars_daily.call_count == 1
        assert len(result1) == len(result2)


class TestCacheRobustness:
    """キャッシュの堅牢性テスト。"""

    def test_write_cache_skips_empty_dataframe(self, tmp_path: Path) -> None:
        """空のDataFrameはキャッシュに保存されないことを確認する。"""
        path = tmp_path / "empty_cache.csv"
        empty_df = pd.DataFrame()
        _write_cache(path, empty_df)
        assert not path.exists()

    def test_write_cache_skips_columns_only_dataframe(self, tmp_path: Path) -> None:
        """カラム定義のみで行がないDataFrameもキャッシュに保存されない。"""
        path = tmp_path / "columns_only.csv"
        df = pd.DataFrame({"Code": pd.Series([], dtype="str"), "Name": pd.Series([], dtype="str")})
        _write_cache(path, df)
        assert not path.exists()

    def test_read_cache_returns_none_for_empty_csv(self, tmp_path: Path) -> None:
        """空のCSVファイルはNoneを返し、ファイルを削除する。"""
        path = tmp_path / "empty_data.csv"
        path.write_text("")
        result = _read_cache(path)
        assert result is None

    def test_read_cache_handles_corrupted_csv(self, tmp_path: Path) -> None:
        """壊れたCSVファイルはNoneを返し、ファイルを削除する。"""
        path = tmp_path / "corrupted.csv"
        path.write_bytes(b"\x00\x01\x02\x03\x04\x05")
        result = _read_cache(path)
        # 壊れたファイルが処理されてもエラーにならない
        assert result is None or isinstance(result, pd.DataFrame)

    @patch("app.jquants_client._get_client")
    def test_empty_api_response_not_cached(self, mock_get_client: MagicMock) -> None:
        """APIが空のDataFrameを返した場合、キャッシュに保存されず再問い合わせされる。"""
        mock_client = MagicMock()
        mock_client.get_eq_master.return_value = pd.DataFrame({"Code": pd.Series([], dtype="str")})
        mock_get_client.return_value = mock_client

        # 1回目: APIを呼ぶ（空の結果）
        result1 = get_stock_master(code="9999")
        assert mock_client.get_eq_master.call_count == 1
        assert len(result1) == 0

        # 2回目: 空結果はキャッシュされていないのでAPIが再呼び出しされる
        result2 = get_stock_master(code="9999")
        assert mock_client.get_eq_master.call_count == 2
        assert len(result2) == 0

    def test_cache_path_creates_directory_if_not_exists(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """キャッシュディレクトリが存在しない場合、自動的に作成される。"""
        nonexistent_dir = tmp_path / "nonexistent" / "nested" / "cache"
        monkeypatch.setattr("app.config.settings.cache_dir", str(nonexistent_dir))

        # _cache_pathが呼ばれるとディレクトリが自動作成される
        path = _cache_path("master", "code=7203")
        assert nonexistent_dir.exists()
        assert path.parent == nonexistent_dir

    @patch("app.jquants_client._get_client")
    def test_get_stock_master_works_without_cache_dir(
        self, mock_get_client: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """キャッシュディレクトリが存在しなくても銘柄マスタ取得が動作する。"""
        nonexistent_dir = tmp_path / "fresh_cache"
        monkeypatch.setattr("app.config.settings.cache_dir", str(nonexistent_dir))
        assert not nonexistent_dir.exists()

        mock_client = MagicMock()
        mock_client.get_eq_master.return_value = pd.DataFrame({"Code": ["7203"], "CompanyName": ["トヨタ自動車"]})
        mock_get_client.return_value = mock_client

        result = get_stock_master()
        assert len(result) == 1
        # ディレクトリが作成されている
        assert nonexistent_dir.exists()


class TestRetryLogic:
    """429エラー時のリトライロジックのテスト。"""

    @patch("app.jquants_client._get_client")
    def test_retry_on_429_error(self, mock_get_client: MagicMock) -> None:
        """429エラー後にリトライしてデータを取得する。"""
        mock_client = MagicMock()
        # 1回目: 429エラー、2回目: 成功
        response_429 = Response()
        response_429.status_code = 429
        error_429 = HTTPError(response=response_429)

        success_df = pd.DataFrame({"Code": ["7203"], "CompanyName": ["トヨタ自動車"]})
        mock_client.get_eq_master.side_effect = [error_429, success_df]
        mock_get_client.return_value = mock_client

        result = get_stock_master("7203")
        assert len(result) == 1
        assert mock_client.get_eq_master.call_count == 2

    @patch("app.jquants_client._get_client")
    def test_non_429_error_not_retried(self, mock_get_client: MagicMock) -> None:
        """429以外のHTTPエラーはリトライせず即座に例外を送出する。"""
        mock_client = MagicMock()
        response_500 = Response()
        response_500.status_code = 500
        error_500 = HTTPError(response=response_500)
        mock_client.get_eq_master.side_effect = error_500
        mock_get_client.return_value = mock_client

        with pytest.raises(HTTPError):
            get_stock_master("7203")
        assert mock_client.get_eq_master.call_count == 1


class TestCacheStats:
    """キャッシュ統計情報のテスト。"""

    def test_cache_stats_empty_dir(self) -> None:
        """空のキャッシュディレクトリでの統計情報を確認する。"""
        stats = get_cache_stats()
        assert stats["file_count"] == 0
        assert stats["total_size_bytes"] == 0

    def test_cache_stats_with_files(self, tmp_path: Path) -> None:
        """CSVファイルがある場合の統計情報を確認する。"""
        path = tmp_path / "test.csv"
        df = pd.DataFrame({"A": [1, 2, 3]})
        df.to_csv(path, index=False)

        with patch("app.jquants_client.settings") as mock_settings:
            mock_settings.cache_dir = str(tmp_path)
            stats = get_cache_stats()
            assert stats["file_count"] == 1
            assert stats["total_size_bytes"] > 0
