"""J-Quants API v2 データフェッチャー。

Freeプランのレート制限（5回/分）に対応するため、
429エラー時は指数バックオフでリトライする。
"""

import logging

import jquantsapi
import pandas as pd
from requests.exceptions import HTTPError
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


def _is_rate_limit_error(exc: BaseException) -> bool:
    """429 Too Many Requests エラーかどうかを判定する。"""
    if isinstance(exc, HTTPError) and exc.response is not None:
        return exc.response.status_code == 429
    return False


_retry_on_rate_limit = retry(
    retry=retry_if_exception(_is_rate_limit_error),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    reraise=True,
)


def _get_client(api_key: str) -> jquantsapi.ClientV2:
    """J-Quants API v2 クライアントを生成する。"""
    return jquantsapi.ClientV2(api_key=api_key)


@_retry_on_rate_limit
def fetch_master(api_key: str) -> pd.DataFrame:
    """銘柄マスタを取得する。"""
    client = _get_client(api_key)
    df: pd.DataFrame = client.get_eq_master()
    logger.info("銘柄マスタ取得完了: %d件", len(df))
    return df


@_retry_on_rate_limit
def fetch_daily(api_key: str, from_date: str = "", to_date: str = "") -> pd.DataFrame:
    """株価日足データを取得する。"""
    client = _get_client(api_key)
    df: pd.DataFrame = client.get_eq_bars_daily(
        from_yyyymmdd=from_date, to_yyyymmdd=to_date
    )
    logger.info("株価日足取得完了: %d件", len(df))
    return df


@_retry_on_rate_limit
def fetch_financials(api_key: str) -> pd.DataFrame:
    """決算サマリーを取得する。"""
    client = _get_client(api_key)
    df: pd.DataFrame = client.get_fin_summary()
    logger.info("決算サマリー取得完了: %d件", len(df))
    return df
