"""Glue Python Shell: JSON → Parquet 変換ジョブ。

S3 raw/ レイヤーの JSON データを読み込み、型正規化・クレンジング後に
processed/ レイヤーへ Parquet 形式で出力する。

パーティション: year=YYYY/month=MM/day=DD/
"""

import json
import logging
import sys
from datetime import datetime, timezone, timedelta
from io import BytesIO

import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Glue Python Shell のジョブパラメータ取得
from awsglue.utils import getResolvedOptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))


def get_latest_raw_keys(s3_client, bucket: str, data_type: str) -> list[str]:
    """raw/ レイヤーから最新日のJSONファイルキーを取得する。"""
    prefix = f"raw/{data_type}/"
    paginator = s3_client.get_paginator("list_objects_v2")
    keys = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".json"):
                keys.append(obj["Key"])

    if not keys:
        return []

    # 最新日のキーのみ取得（パーティションパスの日付でソート）
    keys.sort(reverse=True)
    latest_date_prefix = "/".join(keys[0].split("/")[:-1])
    return [k for k in keys if k.startswith(latest_date_prefix)]


def read_json_from_s3(s3_client, bucket: str, key: str) -> pd.DataFrame:
    """S3からJSONファイルを読み込んでDataFrameに変換する。"""
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    data = json.loads(obj["Body"].read().decode("utf-8"))
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def normalize_master(df: pd.DataFrame) -> pd.DataFrame:
    """銘柄マスタの型正規化。"""
    if df.empty:
        return df
    str_cols = ["Code", "CoName", "CoNameEn", "S17", "S17Nm", "S33", "S33Nm", "Mkt", "MktNm"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).fillna("")
    return df


def normalize_daily(df: pd.DataFrame) -> pd.DataFrame:
    """株価日足データの型正規化。"""
    if df.empty:
        return df
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
    if "Code" in df.columns:
        df["Code"] = df["Code"].astype(str)
    float_cols = ["O", "H", "L", "C", "Vo", "Va", "AdjFactor", "AdjO", "AdjH", "AdjL", "AdjC", "AdjVo"]
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def normalize_financials(df: pd.DataFrame) -> pd.DataFrame:
    """決算サマリーの型正規化。"""
    if df.empty:
        return df
    if "Code" in df.columns:
        df["Code"] = df["Code"].astype(str)
    return df


def write_parquet_to_s3(s3_client, df: pd.DataFrame, bucket: str, key: str) -> None:
    """DataFrameをParquet形式でS3に書き込む。"""
    table = pa.Table.from_pandas(df, preserve_index=False)
    buf = BytesIO()
    pq.write_table(table, buf, compression="snappy")
    buf.seek(0)
    s3_client.put_object(Bucket=bucket, Key=key, Body=buf.getvalue())
    logger.info("Parquet保存: s3://%s/%s (%d件)", bucket, key, len(df))


def transform_data_type(s3_client, bucket: str, data_type: str) -> int:
    """指定されたdata_typeのデータを変換する。"""
    keys = get_latest_raw_keys(s3_client, bucket, data_type)
    if not keys:
        logger.warning("raw/%s にデータが見つかりません", data_type)
        return 0

    dfs = []
    for key in keys:
        df = read_json_from_s3(s3_client, bucket, key)
        if not df.empty:
            dfs.append(df)

    if not dfs:
        return 0

    combined = pd.concat(dfs, ignore_index=True)

    normalizers = {
        "master": normalize_master,
        "daily": normalize_daily,
        "financials": normalize_financials,
    }
    normalizer = normalizers.get(data_type)
    if normalizer:
        combined = normalizer(combined)

    now = datetime.now(JST)
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    output_key = f"processed/{data_type}/year={year}/month={month}/day={day}/{data_type}.parquet"

    write_parquet_to_s3(s3_client, combined, bucket, output_key)
    return len(combined)


def main():
    """Glue Python Shell エントリーポイント。"""
    args = getResolvedOptions(sys.argv, ["DATALAKE_BUCKET"])
    bucket = args["DATALAKE_BUCKET"]

    s3_client = boto3.client("s3")

    total_records = 0
    for data_type in ["master", "daily", "financials"]:
        count = transform_data_type(s3_client, bucket, data_type)
        total_records += count
        logger.info("%s: %d件変換完了", data_type, count)

    logger.info("全変換完了: 合計%d件", total_records)


if __name__ == "__main__":
    main()
