"""data-platform テスト共通フィクスチャ。"""

import os
import sys
import types

import boto3
import pytest
from moto import mock_aws

# awsglue モジュールのモック（Glue実行環境でのみ利用可能）
_awsglue = types.ModuleType("awsglue")
_awsglue_utils = types.ModuleType("awsglue.utils")


def _mock_get_resolved_options(args, options):
    """getResolvedOptions のモック実装。"""
    result = {}
    for opt in options:
        key = f"--{opt}"
        if key in args:
            idx = args.index(key)
            result[opt] = args[idx + 1] if idx + 1 < len(args) else ""
    return result


_awsglue_utils.getResolvedOptions = _mock_get_resolved_options  # type: ignore[attr-defined]
_awsglue.utils = _awsglue_utils  # type: ignore[attr-defined]
sys.modules["awsglue"] = _awsglue
sys.modules["awsglue.utils"] = _awsglue_utils


@pytest.fixture
def aws_credentials():
    """モック用のAWS認証情報をセットする。"""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "ap-northeast-1"


@pytest.fixture
def s3_bucket(aws_credentials):
    """テスト用のS3バケットを作成する。"""
    bucket_name = "test-datalake"
    with mock_aws():
        s3 = boto3.client("s3", region_name="ap-northeast-1")
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": "ap-northeast-1"},
        )
        yield bucket_name
