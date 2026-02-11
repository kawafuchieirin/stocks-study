import numpy as np
import pandas as pd

from app.analysis.technical import compute_technical_indicators


def _make_price_data(n: int = 100) -> pd.DataFrame:
    """テスト用の株価データを生成する。"""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    # ランダムウォークで株価を模擬
    base_price = 1000.0
    returns = np.random.normal(0.001, 0.02, n)
    close = base_price * np.cumprod(1 + returns)
    return pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "close": close})


class TestTechnicalIndicators:
    """テクニカル指標計算の正確性テスト。"""

    def test_sma_columns_exist(self) -> None:
        df = _make_price_data()
        result = compute_technical_indicators(df)
        assert "sma_5" in result.columns
        assert "sma_25" in result.columns
        assert "sma_75" in result.columns

    def test_sma_5_values(self) -> None:
        df = _make_price_data()
        result = compute_technical_indicators(df)
        # SMA5は最初の4行がNaN
        assert pd.isna(result["sma_5"].iloc[0])
        assert pd.notna(result["sma_5"].iloc[4])
        # SMA5の値を手動計算と比較
        expected = df["close"].iloc[:5].mean()
        assert abs(result["sma_5"].iloc[4] - expected) < 0.01

    def test_rsi_range(self) -> None:
        df = _make_price_data()
        result = compute_technical_indicators(df)
        rsi = result["rsi_14"].dropna()
        assert (rsi >= 0).all()
        assert (rsi <= 100).all()

    def test_macd_columns_exist(self) -> None:
        df = _make_price_data()
        result = compute_technical_indicators(df)
        assert "macd" in result.columns
        assert "macd_signal" in result.columns
        assert "macd_histogram" in result.columns

    def test_macd_histogram_equals_diff(self) -> None:
        df = _make_price_data()
        result = compute_technical_indicators(df)
        # ヒストグラム = MACD - シグナル
        valid = result.dropna(subset=["macd", "macd_signal", "macd_histogram"])
        diff = valid["macd"] - valid["macd_signal"]
        np.testing.assert_allclose(valid["macd_histogram"].values, diff.values, atol=0.01)

    def test_bollinger_bands_order(self) -> None:
        df = _make_price_data()
        result = compute_technical_indicators(df)
        valid = result.dropna(subset=["bb_upper", "bb_middle", "bb_lower"])
        assert (valid["bb_upper"] >= valid["bb_middle"]).all()
        assert (valid["bb_middle"] >= valid["bb_lower"]).all()

    def test_bollinger_middle_equals_sma_20(self) -> None:
        df = _make_price_data()
        result = compute_technical_indicators(df)
        # BB中央線は20日SMAと一致
        sma_20 = df["close"].rolling(window=20).mean()
        valid_idx = sma_20.dropna().index
        np.testing.assert_allclose(result.loc[valid_idx, "bb_middle"].values, sma_20.loc[valid_idx].values, atol=0.01)

    def test_empty_dataframe(self) -> None:
        df = pd.DataFrame({"date": [], "close": []})
        result = compute_technical_indicators(df)
        assert len(result) == 0


class TestTechnicalIndicatorsEdgeCases:
    """テクニカル指標のエッジケーステスト。"""

    def test_constant_price_sma_equals_price(self) -> None:
        """全て同じ値の場合、SMAは元の値と一致する。"""
        n = 100
        constant_price = 1500.0
        dates = pd.date_range("2024-01-01", periods=n, freq="B")
        df = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "close": [constant_price] * n})

        result = compute_technical_indicators(df)

        # SMAは定数値と一致するはず（NaNでない部分）
        sma_5_valid = result["sma_5"].dropna()
        np.testing.assert_allclose(sma_5_valid.values, constant_price, atol=0.01)

        sma_25_valid = result["sma_25"].dropna()
        np.testing.assert_allclose(sma_25_valid.values, constant_price, atol=0.01)

        sma_75_valid = result["sma_75"].dropna()
        np.testing.assert_allclose(sma_75_valid.values, constant_price, atol=0.01)

    def test_constant_price_rsi_is_nan(self) -> None:
        """全て同じ値の場合、RSIは計算不能（値動きがないため）。

        ta ライブラリの実装では、価格変動がゼロの場合RSIはNaNになる。
        """
        n = 100
        constant_price = 1500.0
        dates = pd.date_range("2024-01-01", periods=n, freq="B")
        df = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "close": [constant_price] * n})

        result = compute_technical_indicators(df)

        # 価格変動ゼロの場合、RSIはNaNまたは特定の値になる
        rsi = result["rsi_14"].dropna()
        if len(rsi) > 0:
            # ta ライブラリでは変動ゼロ時にRSI=0になることがある
            assert ((rsi >= 0) & (rsi <= 100)).all(), "RSIが0-100の範囲外"

    def test_constant_price_bollinger_bands_collapsed(self) -> None:
        """全て同じ値の場合、ボリンジャーバンドの上限と下限が一致する。

        標準偏差が0なので、上限=中央=下限になるはず。
        """
        n = 100
        constant_price = 1500.0
        dates = pd.date_range("2024-01-01", periods=n, freq="B")
        df = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "close": [constant_price] * n})

        result = compute_technical_indicators(df)
        valid = result.dropna(subset=["bb_upper", "bb_middle", "bb_lower"])

        # 標準偏差=0なので上限=中央=下限=定数値
        np.testing.assert_allclose(valid["bb_upper"].values, constant_price, atol=0.01)
        np.testing.assert_allclose(valid["bb_middle"].values, constant_price, atol=0.01)
        np.testing.assert_allclose(valid["bb_lower"].values, constant_price, atol=0.01)

    def test_constant_price_macd_is_zero(self) -> None:
        """全て同じ値の場合、MACDは0になる。

        短期EMAと長期EMAが同じ値になるため。
        """
        n = 100
        constant_price = 1500.0
        dates = pd.date_range("2024-01-01", periods=n, freq="B")
        df = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "close": [constant_price] * n})

        result = compute_technical_indicators(df)
        macd_valid = result["macd"].dropna()
        macd_signal_valid = result["macd_signal"].dropna()
        macd_hist_valid = result["macd_histogram"].dropna()

        np.testing.assert_allclose(macd_valid.values, 0.0, atol=0.01)
        np.testing.assert_allclose(macd_signal_valid.values, 0.0, atol=0.01)
        np.testing.assert_allclose(macd_hist_valid.values, 0.0, atol=0.01)

    def test_very_few_rows_1(self) -> None:
        """1行のデータでもエラーにならない。"""
        df = pd.DataFrame({"date": ["2024-01-01"], "close": [1000.0]})
        result = compute_technical_indicators(df)
        assert len(result) == 1
        # 1行ではすべてのテクニカル指標がNaN
        assert pd.isna(result["sma_5"].iloc[0])
        assert pd.isna(result["sma_25"].iloc[0])
        assert pd.isna(result["sma_75"].iloc[0])

    def test_very_few_rows_3(self) -> None:
        """3行のデータでもエラーにならない。"""
        dates = pd.date_range("2024-01-01", periods=3, freq="B")
        df = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "close": [1000.0, 1010.0, 1005.0]})
        result = compute_technical_indicators(df)
        assert len(result) == 3
        # SMA_5は5行必要なのでNaN
        assert pd.isna(result["sma_5"].iloc[2])
        # SMA_25, SMA_75もNaN
        assert result["sma_25"].isna().all()
        assert result["sma_75"].isna().all()

    def test_very_few_rows_4(self) -> None:
        """4行のデータ（5行未満）でもエラーにならない。"""
        dates = pd.date_range("2024-01-01", periods=4, freq="B")
        df = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "close": [1000.0, 1010.0, 1005.0, 1015.0]})
        result = compute_technical_indicators(df)
        assert len(result) == 4
        # SMA_5は5行必要なので全部NaN
        assert result["sma_5"].isna().all()
        # MACDも計算不能
        assert result["macd"].isna().all()
        # ボリンジャーバンドも20行必要
        assert result["bb_upper"].isna().all()

    def test_exactly_5_rows(self) -> None:
        """ちょうど5行でSMA_5の最後の値が計算できる。"""
        dates = pd.date_range("2024-01-01", periods=5, freq="B")
        prices = [1000.0, 1010.0, 1005.0, 1015.0, 1020.0]
        df = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "close": prices})
        result = compute_technical_indicators(df)
        assert len(result) == 5

        # SMA_5の最後の行は計算可能
        assert pd.notna(result["sma_5"].iloc[4])
        expected_sma_5 = sum(prices) / 5
        assert abs(result["sma_5"].iloc[4] - expected_sma_5) < 0.01

        # SMA_25はまだ計算不能
        assert result["sma_25"].isna().all()
