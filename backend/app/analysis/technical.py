import pandas as pd
import ta


def compute_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """株価DataFrameにテクニカル指標を追加する。

    入力DataFrameには 'close' カラム（調整後終値）が必要。
    """
    close = df["close"].astype(float)

    # 移動平均線 (SMA)
    df["sma_5"] = ta.trend.sma_indicator(close, window=5)
    df["sma_25"] = ta.trend.sma_indicator(close, window=25)
    df["sma_75"] = ta.trend.sma_indicator(close, window=75)

    # RSI (14日)
    df["rsi_14"] = ta.momentum.rsi(close, window=14)

    # MACD (12/26/9)
    macd_indicator = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9)
    df["macd"] = macd_indicator.macd()
    df["macd_signal"] = macd_indicator.macd_signal()
    df["macd_histogram"] = macd_indicator.macd_diff()

    # ボリンジャーバンド (20日, ±2σ)
    bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_middle"] = bb.bollinger_mavg()
    df["bb_lower"] = bb.bollinger_lband()

    return df
