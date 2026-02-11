"""Lambda Ingest ハンドラーのテスト。"""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import boto3
import pandas as pd
import pytest
from moto import mock_aws

# Lambda関数のソースをインポートパスに追加
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "lambda", "ingest")
)


@pytest.fixture
def mock_env(s3_bucket):
    """Lambda環境変数をモックする。"""
    with patch.dict(
        os.environ,
        {
            "DATALAKE_BUCKET": s3_bucket,
            "JQUANTS_API_KEY": "test-api-key",
        },
    ):
        yield s3_bucket


@pytest.fixture(autouse=True)
def _reload_handler():
    """テストごとにhandlerモジュールを再読み込みする。"""
    for mod_name in list(sys.modules.keys()):
        if mod_name in ("handler", "jquants_fetcher"):
            del sys.modules[mod_name]


class TestIngestHandler:
    """handler.handler のテスト。"""

    @mock_aws
    def test_ingest_master(self, aws_credentials):
        """銘柄マスタの取得とS3保存が正常に動作する。"""
        bucket = "test-datalake"
        s3 = boto3.client("s3", region_name="ap-northeast-1")
        s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={"LocationConstraint": "ap-northeast-1"},
        )

        with patch.dict(
            os.environ,
            {"DATALAKE_BUCKET": bucket, "JQUANTS_API_KEY": "test-key"},
        ):
            master_df = pd.DataFrame(
                {
                    "Code": ["86970", "13010"],
                    "CoName": ["日本取引所グループ", "極洋"],
                }
            )

            with patch(
                "jquants_fetcher.fetch_master", return_value=master_df
            ):
                import handler

                result = handler.handler({"data_type": "master"}, None)

        assert result["status"] == "success"
        assert result["data_type"] == "master"
        assert result["record_count"] == 2
        assert result["s3_key"].startswith("raw/master/year=")
        assert result["s3_key"].endswith(".json")

        # S3にJSONが保存されたことを確認
        obj = s3.get_object(Bucket=bucket, Key=result["s3_key"])
        data = json.loads(obj["Body"].read().decode("utf-8"))
        assert len(data) == 2
        assert data[0]["Code"] == "86970"

    @mock_aws
    def test_ingest_daily(self, aws_credentials):
        """株価日足データの取得とS3保存が正常に動作する。"""
        bucket = "test-datalake"
        s3 = boto3.client("s3", region_name="ap-northeast-1")
        s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={"LocationConstraint": "ap-northeast-1"},
        )

        with patch.dict(
            os.environ,
            {"DATALAKE_BUCKET": bucket, "JQUANTS_API_KEY": "test-key"},
        ):
            daily_df = pd.DataFrame(
                {
                    "Date": ["2025-02-07", "2025-02-08"],
                    "Code": ["86970", "86970"],
                    "AdjC": [4500.0, 4520.0],
                }
            )

            with patch("jquants_fetcher.fetch_daily", return_value=daily_df):
                import handler

                result = handler.handler(
                    {
                        "data_type": "daily",
                        "from_date": "20250201",
                        "to_date": "20250209",
                    },
                    None,
                )

        assert result["status"] == "success"
        assert result["data_type"] == "daily"
        assert result["record_count"] == 2

    @mock_aws
    def test_ingest_financials(self, aws_credentials):
        """決算サマリーの取得とS3保存が正常に動作する。"""
        bucket = "test-datalake"
        s3 = boto3.client("s3", region_name="ap-northeast-1")
        s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={"LocationConstraint": "ap-northeast-1"},
        )

        with patch.dict(
            os.environ,
            {"DATALAKE_BUCKET": bucket, "JQUANTS_API_KEY": "test-key"},
        ):
            fin_df = pd.DataFrame(
                {
                    "Code": ["86970"],
                    "NetSales": [100000000],
                }
            )

            with patch(
                "jquants_fetcher.fetch_financials", return_value=fin_df
            ):
                import handler

                result = handler.handler({"data_type": "financials"}, None)

        assert result["status"] == "success"
        assert result["data_type"] == "financials"
        assert result["record_count"] == 1

    @mock_aws
    def test_ingest_empty_data(self, aws_credentials):
        """空データの場合はemptyステータスを返す。"""
        bucket = "test-datalake"
        s3 = boto3.client("s3", region_name="ap-northeast-1")
        s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={"LocationConstraint": "ap-northeast-1"},
        )

        with patch.dict(
            os.environ,
            {"DATALAKE_BUCKET": bucket, "JQUANTS_API_KEY": "test-key"},
        ):
            with patch(
                "jquants_fetcher.fetch_master",
                return_value=pd.DataFrame(),
            ):
                import handler

                result = handler.handler({"data_type": "master"}, None)

        assert result["status"] == "empty"
        assert result["record_count"] == 0

    def test_ingest_invalid_data_type(self, aws_credentials):
        """未対応のdata_typeでValueErrorが発生する。"""
        with patch.dict(
            os.environ,
            {
                "DATALAKE_BUCKET": "test-datalake",
                "JQUANTS_API_KEY": "test-key",
            },
        ):
            import handler

            with pytest.raises(ValueError, match="未対応の data_type"):
                handler.handler({"data_type": "unknown"}, None)
