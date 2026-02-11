"""FastAPI統合テスト。

各APIエンドポイントの正常系・異常系をTestClientで検証する。
J-Quants APIへの実際のリクエストは行わず、すべてモックを使用する。
"""

from unittest.mock import MagicMock, patch

import pandas as pd
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """GET /api/health のテスト。"""

    def test_health_returns_ok(self) -> None:
        """ヘルスチェックが正常なレスポンスを返す。"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "api_key_configured" in data
        assert "cache" in data

    def test_health_content_type_is_json(self) -> None:
        """ヘルスチェックのContent-TypeがJSONである。"""
        response = client.get("/api/health")
        assert "application/json" in response.headers["content-type"]


class TestStocksMasterEndpoint:
    """GET /api/stocks/master のテスト。"""

    @patch("app.stocks.service.get_stock_master")
    def test_search_stocks_with_query(self, mock_get_master: MagicMock) -> None:
        """クエリパラメータで銘柄検索ができる。"""
        mock_get_master.return_value = pd.DataFrame(
            {
                "Code": ["7203", "9984"],
                "CoName": ["トヨタ自動車", "ソフトバンクグループ"],
                "CoNameEn": ["TOYOTA MOTOR", "SOFTBANK GROUP"],
                "S17": ["6", "9"],
                "S17Nm": ["自動車・輸送機", "情報通信・サービスその他"],
                "S33": ["3700", "5250"],
                "S33Nm": ["輸送用機器", "情報・通信業"],
                "Mkt": ["0111", "0111"],
                "MktNm": ["プライム", "プライム"],
            }
        )

        # search_stocksはCode/CoNameでフィルタリングするので、マッチするクエリを使用
        response = client.get("/api/stocks/master", params={"q": "トヨタ"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        # カラム名がリネームされている
        assert data[0]["code"] == "7203"
        assert data[0]["company_name"] == "トヨタ自動車"

    @patch("app.stocks.service.get_stock_master")
    def test_search_stocks_empty_query(self, mock_get_master: MagicMock) -> None:
        """空のクエリでも正常にレスポンスが返る。"""
        mock_get_master.return_value = pd.DataFrame(
            {
                "Code": ["7203"],
                "CoName": ["トヨタ自動車"],
                "CoNameEn": ["TOYOTA MOTOR"],
                "S17": ["6"],
                "S17Nm": ["自動車・輸送機"],
                "S33": ["3700"],
                "S33Nm": ["輸送用機器"],
                "Mkt": ["0111"],
                "MktNm": ["プライム"],
            }
        )

        response = client.get("/api/stocks/master")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    @patch("app.stocks.service.get_stock_master")
    def test_search_stocks_no_results(self, mock_get_master: MagicMock) -> None:
        """検索結果が0件の場合、空配列を返す。"""
        mock_get_master.return_value = pd.DataFrame(
            {
                "Code": pd.Series([], dtype="str"),
                "CoName": pd.Series([], dtype="str"),
                "CoNameEn": pd.Series([], dtype="str"),
                "S17": pd.Series([], dtype="str"),
                "S17Nm": pd.Series([], dtype="str"),
                "S33": pd.Series([], dtype="str"),
                "S33Nm": pd.Series([], dtype="str"),
                "Mkt": pd.Series([], dtype="str"),
                "MktNm": pd.Series([], dtype="str"),
            }
        )

        response = client.get("/api/stocks/master", params={"q": "存在しない銘柄"})
        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestTechnicalEndpoint:
    """GET /api/analysis/{code}/technical のテスト。"""

    @patch("app.analysis.router.get_daily_quotes")
    def test_technical_returns_empty_on_api_error(self, mock_get_daily: MagicMock) -> None:
        """J-Quants APIがエラーの場合、空配列が返る。"""
        mock_get_daily.side_effect = Exception("J-Quants API接続エラー")

        response = client.get("/api/analysis/7203/technical")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    @patch("app.analysis.router.get_daily_quotes")
    def test_technical_returns_empty_on_timeout(self, mock_get_daily: MagicMock) -> None:
        """タイムアウトエラーでも空配列が返る。"""
        mock_get_daily.side_effect = TimeoutError("Request timed out")

        response = client.get("/api/analysis/7203/technical")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    @patch("app.analysis.router.get_daily_quotes")
    def test_technical_with_valid_data(self, mock_get_daily: MagicMock) -> None:
        """正常系: テクニカル指標が正しく計算されて返る。"""
        import numpy as np

        np.random.seed(42)
        n = 100
        dates = pd.date_range("2024-01-01", periods=n, freq="B")
        base_price = 1000.0
        returns = np.random.normal(0.001, 0.02, n)
        close = base_price * np.cumprod(1 + returns)

        mock_get_daily.return_value = pd.DataFrame(
            {
                "Date": dates.strftime("%Y-%m-%d"),
                "Code": ["7203"] * n,
                "AdjC": close,
                "AdjO": close * 0.99,
                "AdjH": close * 1.01,
                "AdjL": close * 0.98,
                "AdjVo": [1000000] * n,
            }
        )

        response = client.get(
            "/api/analysis/7203/technical",
            params={"from": "20240101", "to": "20240601"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == n

        # 各レコードに期待するフィールドが含まれる
        last_record = data[-1]
        assert "date" in last_record
        assert "close" in last_record
        assert "sma_5" in last_record
        assert "sma_25" in last_record
        assert "sma_75" in last_record
        assert "rsi_14" in last_record
        assert "macd" in last_record
        assert "macd_signal" in last_record
        assert "macd_histogram" in last_record
        assert "bb_upper" in last_record
        assert "bb_middle" in last_record
        assert "bb_lower" in last_record

        # 最後のレコードではテクニカル指標が計算済み（Noneではない）
        assert last_record["sma_5"] is not None
        assert last_record["sma_75"] is not None
        assert last_record["rsi_14"] is not None
        assert last_record["macd"] is not None

    @patch("app.analysis.router.get_daily_quotes")
    def test_technical_with_empty_dataframe(self, mock_get_daily: MagicMock) -> None:
        """空のDataFrameが返された場合、空配列を返す。"""
        mock_get_daily.return_value = pd.DataFrame()

        response = client.get("/api/analysis/7203/technical")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    @patch("app.analysis.router.get_daily_quotes")
    def test_technical_with_no_close_column(self, mock_get_daily: MagicMock) -> None:
        """closeカラムがないDataFrameの場合、空配列を返す。"""
        mock_get_daily.return_value = pd.DataFrame(
            {
                "Date": ["2024-01-01"],
                "Code": ["7203"],
                "Volume": [1000000],
            }
        )

        response = client.get("/api/analysis/7203/technical")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    @patch("app.analysis.router.get_daily_quotes")
    def test_technical_nan_converted_to_none(self, mock_get_daily: MagicMock) -> None:
        """NaN値がJSON上でnull (None)に変換される。"""
        # データが少ないとSMA_75はNaN
        dates = pd.date_range("2024-01-01", periods=10, freq="B")
        mock_get_daily.return_value = pd.DataFrame(
            {
                "Date": dates.strftime("%Y-%m-%d"),
                "Code": ["7203"] * 10,
                "AdjC": [1000.0 + i for i in range(10)],
                "AdjO": [999.0 + i for i in range(10)],
                "AdjH": [1001.0 + i for i in range(10)],
                "AdjL": [998.0 + i for i in range(10)],
                "AdjVo": [1000000] * 10,
            }
        )

        response = client.get("/api/analysis/7203/technical")
        assert response.status_code == 200
        data = response.json()
        # SMA_75は75日分のデータが必要なので、10行しかない場合はすべてNone
        for row in data:
            assert row["sma_75"] is None

    @patch("app.analysis.router.get_daily_quotes")
    def test_technical_fallback_to_c_column(self, mock_get_daily: MagicMock) -> None:
        """AdjCカラムがなくCカラムがある場合にフォールバックする。"""
        dates = pd.date_range("2024-01-01", periods=30, freq="B")
        mock_get_daily.return_value = pd.DataFrame(
            {
                "Date": dates.strftime("%Y-%m-%d"),
                "Code": ["7203"] * 30,
                "C": [1000.0 + i for i in range(30)],
            }
        )

        response = client.get("/api/analysis/7203/technical")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 30
        # closeフィールドが存在し値が入っている
        assert data[-1]["close"] is not None
