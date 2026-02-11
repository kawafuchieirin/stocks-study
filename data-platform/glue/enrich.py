"""Glue Python Shell: テクニカル指標算出ジョブ。

processed/daily/ の Parquet データを読み込み、銘柄ごとに
テクニカル指標（SMA, RSI, MACD, ボリンジャーバンド）を算出し
analytics/technical/ へ Parquet 形式で出力する。

パーティション: year=YYYY/month=MM/day=DD/

テクニカル指標の算出ロジックは backend/app/analysis/technical.py と同一。
"""

import logging
import sys
from datetime import datetime, timezone, timedelta
from io import BytesIO

import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import ta

from awsglue.utils import getResolvedOptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))


def compute_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """株価DataFrameにテクニカル指標を追加する。

    backend/app/analysis/technical.py の compute_technical_indicators と同一ロジック。
    """
    close = df["AdjC"].astype(float)

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


def get_latest_daily_keys(s3_client, bucket: str) -> list[str]:
    """processed/daily/ から最新日のParquetファイルキーを取得する。"""
    prefix = "processed/daily/"
    paginator = s3_client.get_paginator("list_objects_v2")
    keys = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".parquet"):
                keys.append(obj["Key"])

    if not keys:
        return []

    keys.sort(reverse=True)
    latest_date_prefix = "/".join(keys[0].split("/")[:-1])
    return [k for k in keys if k.startswith(latest_date_prefix)]


def read_parquet_from_s3(s3_client, bucket: str, key: str) -> pd.DataFrame:
    """S3からParquetファイルを読み込んでDataFrameに変換する。"""
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    buf = BytesIO(obj["Body"].read())
    return pd.read_parquet(buf)


def write_parquet_to_s3(s3_client, df: pd.DataFrame, bucket: str, key: str) -> None:
    """DataFrameをParquet形式でS3に書き込む。"""
    table = pa.Table.from_pandas(df, preserve_index=False)
    buf = BytesIO()
    pq.write_table(table, buf, compression="snappy")
    buf.seek(0)
    s3_client.put_object(Bucket=bucket, Key=key, Body=buf.getvalue())
    logger.info("Parquet保存: s3://%s/%s (%d件)", bucket, key, len(df))


def main():
    """Glue Python Shell エントリーポイント。"""
    args = getResolvedOptions(sys.argv, ["DATALAKE_BUCKET"])
    bucket = args["DATALAKE_BUCKET"]

    s3_client = boto3.client("s3")

    keys = get_latest_daily_keys(s3_client, bucket)
    if not keys:
        logger.warning("processed/daily/ にデータが見つかりません")
        return

    dfs = []
    for key in keys:
        df = read_parquet_from_s3(s3_client, bucket, key)
        if not df.empty:
            dfs.append(df)

    if not dfs:
        logger.warning("読み込み可能なデータがありません")
        return

    daily = pd.concat(dfs, ignore_index=True)
    logger.info("日足データ読み込み完了: %d件", len(daily))

    if "AdjC" not in daily.columns:
        logger.error("AdjC カラムが見つかりません。テクニカル指標算出をスキップします。")
        return

    # 銘柄ごとにテクニカル指標を算出
    results = []
    for code, group in daily.groupby("Code"):
        group = group.sort_values("Date").copy()
        if len(group) < 2:
            continue
        enriched = compute_technical_indicators(group)
        results.append(enriched)

    if not results:
        logger.warning("テクニカル指標を算出できる銘柄がありません")
        return

    combined = pd.concat(results, ignore_index=True)

    now = datetime.now(JST)
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    output_key = f"analytics/technical/year={year}/month={month}/day={day}/technical.parquet"

    write_parquet_to_s3(s3_client, combined, bucket, output_key)
    logger.info("テクニカル指標算出完了: %d件", len(combined))


if __name__ == "__main__":
    main()
