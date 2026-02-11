"""Glue Enrich ジョブのテスト。

テクニカル指標算出ロジックのテストおよび
backend/app/analysis/technical.py との出力一致検証。
"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "glue")
)

# backendのtechnical.pyも比較用にインポート可能にする
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "backend")
)


def _make_daily_df(n: int = 100) -> pd.DataFrame:
    """テスト用の日足DataFrameを生成する。"""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    prices = 1000 + np.cumsum(np.random.randn(n) * 10)
    return pd.DataFrame({
        "Date": dates.strftime("%Y-%m-%d"),
        "Code": "86970",
        "AdjC": prices,
        "AdjO": prices - np.random.rand(n) * 5,
        "AdjH": prices + np.random.rand(n) * 10,
        "AdjL": prices - np.random.rand(n) * 10,
        "AdjVo": np.random.randint(10000, 100000, n).astype(float),
    })


class TestComputeTechnicalIndicators:
    """テクニカル指標算出のテスト。"""

    def test_all_indicators_present(self):
        """全テクニカル指標カラムが生成されること。"""
        from enrich import compute_technical_indicators

        df = _make_daily_df()
        result = compute_technical_indicators(df)

        expected_cols = [
            "sma_5", "sma_25", "sma_75",
            "rsi_14",
            "macd", "macd_signal", "macd_histogram",
            "bb_upper", "bb_middle", "bb_lower",
        ]
        for col in expected_cols:
            assert col in result.columns, f"{col} が結果に含まれていません"

    def test_sma_values(self):
        """SMA値が正しく算出されること。"""
        from enrich import compute_technical_indicators

        df = _make_daily_df()
        result = compute_technical_indicators(df)

        # SMA_5: 最初の4行はNaN、5行目以降は値がある
        assert pd.isna(result["sma_5"].iloc[0])
        assert not pd.isna(result["sma_5"].iloc[4])

        # SMA_5の値を手計算で確認
        expected_sma5 = df["AdjC"].iloc[:5].mean()
        assert abs(result["sma_5"].iloc[4] - expected_sma5) < 0.01

    def test_rsi_range(self):
        """RSI値が0-100の範囲内であること。"""
        from enrich import compute_technical_indicators

        df = _make_daily_df()
        result = compute_technical_indicators(df)

        rsi = result["rsi_14"].dropna()
        assert (rsi >= 0).all()
        assert (rsi <= 100).all()

    def test_bollinger_bands_order(self):
        """ボリンジャーバンドの上限 > 中央 > 下限であること。"""
        from enrich import compute_technical_indicators

        df = _make_daily_df()
        result = compute_technical_indicators(df)

        valid = result.dropna(subset=["bb_upper", "bb_middle", "bb_lower"])
        assert (valid["bb_upper"] >= valid["bb_middle"]).all()
        assert (valid["bb_middle"] >= valid["bb_lower"]).all()

    def test_short_data(self):
        """データが少ない場合でもエラーにならないこと。"""
        from enrich import compute_technical_indicators

        df = _make_daily_df(n=5)
        result = compute_technical_indicators(df)
        assert len(result) == 5


class TestConsistencyWithBackend:
    """backend/app/analysis/technical.py との出力一致検証。"""

    def test_indicators_match_backend(self):
        """Glue版とbackend版のテクニカル指標が一致すること。"""
        from enrich import compute_technical_indicators as glue_compute

        try:
            from app.analysis.technical import compute_technical_indicators as backend_compute
        except ImportError:
            pytest.skip("backend モジュールが利用できません")

        # 同じ入力データを準備
        df = _make_daily_df()

        # Glue版: AdjC カラムを使う
        glue_df = df.copy()
        glue_result = glue_compute(glue_df)

        # backend版: close カラムを使う
        backend_df = df.copy()
        backend_df["close"] = backend_df["AdjC"]
        backend_result = backend_compute(backend_df)

        # 一致検証
        indicator_cols = [
            "sma_5", "sma_25", "sma_75",
            "rsi_14",
            "macd", "macd_signal", "macd_histogram",
            "bb_upper", "bb_middle", "bb_lower",
        ]
        for col in indicator_cols:
            glue_vals = glue_result[col].dropna().values
            backend_vals = backend_result[col].dropna().values
            np.testing.assert_allclose(
                glue_vals, backend_vals, rtol=1e-10,
                err_msg=f"{col} の値がGlue版とbackend版で一致しません",
            )
