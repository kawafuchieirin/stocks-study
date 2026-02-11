"""Glue Transform ジョブのテスト。

awsglue モジュールはGlue環境のみで利用可能なため、
変換ロジック関数を直接テストする。
"""

import json
import os
import sys
from io import BytesIO

import boto3
import pandas as pd
import pyarrow.parquet as pq
import pytest
from moto import mock_aws

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "glue")
)


class TestNormalization:
    """型正規化関数のテスト。"""

    def test_normalize_master(self):
        """銘柄マスタの文字列型正規化。"""
        # awsglue を使わない関数のみインポート
        from transform import normalize_master

        df = pd.DataFrame({
            "Code": [86970, 13010],
            "CoName": ["日本取引所グループ", "極洋"],
            "S17": [1, 2],
        })
        result = normalize_master(df)
        assert result["Code"].dtype == object  # str型
        assert result["Code"].iloc[0] == "86970"

    def test_normalize_daily(self):
        """株価日足データの型正規化。"""
        from transform import normalize_daily

        df = pd.DataFrame({
            "Date": ["2025-02-07T00:00:00", "2025-02-08T00:00:00"],
            "Code": [86970, 86970],
            "AdjC": ["4500", "4520.5"],
            "Vo": ["100000", "invalid"],
        })
        result = normalize_daily(df)
        assert result["Date"].iloc[0] == "2025-02-07"
        assert result["Code"].dtype == object
        assert result["AdjC"].dtype == float
        assert pd.isna(result["Vo"].iloc[1])  # "invalid" → NaN

    def test_normalize_financials(self):
        """決算サマリーの型正規化。"""
        from transform import normalize_financials

        df = pd.DataFrame({
            "Code": [86970],
            "NetSales": [100000000],
        })
        result = normalize_financials(df)
        assert result["Code"].dtype == object

    def test_normalize_empty_df(self):
        """空のDataFrameでもエラーにならない。"""
        from transform import normalize_master, normalize_daily, normalize_financials

        for normalizer in [normalize_master, normalize_daily, normalize_financials]:
            result = normalizer(pd.DataFrame())
            assert result.empty


class TestTransformIO:
    """S3 I/O 関連のテスト。"""

    @mock_aws
    def test_read_json_from_s3(self):
        """S3からJSONを読み込めること。"""
        from transform import read_json_from_s3

        s3 = boto3.client("s3", region_name="ap-northeast-1")
        bucket = "test-bucket"
        s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={"LocationConstraint": "ap-northeast-1"},
        )
        data = [{"Code": "86970", "CoName": "テスト"}]
        s3.put_object(
            Bucket=bucket,
            Key="raw/master/test.json",
            Body=json.dumps(data),
        )

        df = read_json_from_s3(s3, bucket, "raw/master/test.json")
        assert len(df) == 1
        assert df["Code"].iloc[0] == "86970"

    @mock_aws
    def test_write_parquet_to_s3(self):
        """S3にParquetを書き込めること。"""
        from transform import write_parquet_to_s3

        s3 = boto3.client("s3", region_name="ap-northeast-1")
        bucket = "test-bucket"
        s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={"LocationConstraint": "ap-northeast-1"},
        )

        df = pd.DataFrame({"Code": ["86970"], "CoName": ["テスト"]})
        write_parquet_to_s3(s3, df, bucket, "processed/master/test.parquet")

        obj = s3.get_object(Bucket=bucket, Key="processed/master/test.parquet")
        result = pq.read_table(BytesIO(obj["Body"].read())).to_pandas()
        assert len(result) == 1
        assert result["Code"].iloc[0] == "86970"

    @mock_aws
    def test_get_latest_raw_keys(self):
        """最新日のJSONキーのみ取得できること。"""
        from transform import get_latest_raw_keys

        s3 = boto3.client("s3", region_name="ap-northeast-1")
        bucket = "test-bucket"
        s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={"LocationConstraint": "ap-northeast-1"},
        )

        # 異なる日付のファイルを配置
        s3.put_object(Bucket=bucket, Key="raw/master/year=2025/month=02/day=07/master.json", Body=b"[]")
        s3.put_object(Bucket=bucket, Key="raw/master/year=2025/month=02/day=09/master.json", Body=b"[]")

        keys = get_latest_raw_keys(s3, bucket, "master")
        assert len(keys) == 1
        assert "day=09" in keys[0]
