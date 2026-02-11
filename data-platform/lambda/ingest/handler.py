"""Lambda Ingest ハンドラー。

Step Functions から呼び出され、J-Quants API v2 からデータを取得し
S3 raw/ レイヤーに JSON 形式で保存する。

Event 例:
    {"data_type": "master"}
    {"data_type": "daily", "from_date": "20250101", "to_date": "20250209"}
    {"data_type": "financials"}
"""

import json
import logging
import os
from datetime import datetime, timezone, timedelta

import boto3
import pandas as pd

from jquants_fetcher import fetch_daily, fetch_financials, fetch_master

logger = logging.getLogger()
logger.setLevel(logging.INFO)

JST = timezone(timedelta(hours=9))

s3_client = boto3.client("s3")


def handler(event: dict, context: object) -> dict:
    """Lambda エントリーポイント。"""
    data_type = event["data_type"]
    bucket = os.environ["DATALAKE_BUCKET"]
    api_key = os.environ["JQUANTS_API_KEY"]

    logger.info("Ingest開始: data_type=%s, bucket=%s", data_type, bucket)

    now = datetime.now(JST)
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    timestamp = now.strftime("%Y%m%d_%H%M%S")

    df = _fetch_data(data_type, api_key, event)

    if df.empty:
        logger.warning("取得データが空です: data_type=%s", data_type)
        return {
            "status": "empty",
            "data_type": data_type,
            "record_count": 0,
        }

    s3_key = f"raw/{data_type}/year={year}/month={month}/day={day}/{data_type}_{timestamp}.json"
    json_data = df.to_json(orient="records", force_ascii=False, date_format="iso")

    s3_client.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=json_data,
        ContentType="application/json",
    )

    record_count = len(df)
    logger.info("S3保存完了: s3://%s/%s (%d件)", bucket, s3_key, record_count)

    return {
        "status": "success",
        "data_type": data_type,
        "s3_key": s3_key,
        "record_count": record_count,
    }


def _fetch_data(data_type: str, api_key: str, event: dict) -> pd.DataFrame:
    """data_type に応じてデータを取得する。"""
    if data_type == "master":
        return fetch_master(api_key)
    elif data_type == "daily":
        from_date = event.get("from_date", "")
        to_date = event.get("to_date", "")
        return fetch_daily(api_key, from_date, to_date)
    elif data_type == "financials":
        return fetch_financials(api_key)
    else:
        raise ValueError(f"未対応の data_type: {data_type}")
