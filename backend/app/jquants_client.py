import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import jquantsapi
import pandas as pd
from requests.exceptions import HTTPError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)


def _is_rate_limit_error(exc: BaseException) -> bool:
    """429 Too Many Requests（レート制限）エラーかどうかを判定する。"""
    if isinstance(exc, HTTPError) and exc.response is not None:
        return exc.response.status_code == 429  # type: ignore[no-any-return]
    return False


# レート制限（429）時のリトライデコレータ: 最大3回、指数バックオフ（2秒→4秒→8秒）
_retry_on_rate_limit = retry(
    retry=retry_if_exception(_is_rate_limit_error),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    reraise=True,
)


def _cache_path(endpoint: str, params: str) -> Path:
    """キャッシュファイルのパスを生成する。"""
    cache_dir = Path(settings.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    params_hash = hashlib.md5(params.encode()).hexdigest()[:8]  # noqa: S324
    today = datetime.now().strftime("%Y%m%d")
    return cache_dir / f"{endpoint}_{params_hash}_{today}.csv"


def _read_cache(path: Path) -> pd.DataFrame | None:
    """キャッシュファイルが存在すれば読み込む。壊れたCSVはスキップして削除する。"""
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path)
    except Exception:
        logger.warning("壊れたキャッシュファイルを検出・削除しました: %s", path)
        path.unlink(missing_ok=True)
        return None
    # 空のDataFrameはキャッシュとして無効
    if df.empty:
        logger.info("空のキャッシュファイルを検出・削除しました: %s", path)
        path.unlink(missing_ok=True)
        return None
    return df


def _write_cache(path: Path, df: pd.DataFrame) -> None:
    """DataFrameをCSVキャッシュとして保存する。空DataFrameは保存しない。"""
    if df.empty:
        logger.info("空のDataFrameはキャッシュに保存しません: %s", path)
        return
    df.to_csv(path, index=False)


def _get_client() -> jquantsapi.ClientV2:
    """J-Quants API v2クライアントを生成する。"""
    return jquantsapi.ClientV2(api_key=settings.quants_api_v2_api_key)


def get_cache_stats() -> dict[str, Any]:
    """キャッシュディレクトリの統計情報を返す。"""
    cache_dir = Path(settings.cache_dir)
    if not cache_dir.exists():
        return {"cache_dir": str(cache_dir), "file_count": 0, "total_size_bytes": 0}
    csv_files = list(cache_dir.glob("*.csv"))
    total_size = sum(f.stat().st_size for f in csv_files)
    return {
        "cache_dir": str(cache_dir),
        "file_count": len(csv_files),
        "total_size_bytes": total_size,
    }


@_retry_on_rate_limit
def get_stock_master(code: str = "") -> pd.DataFrame:
    """銘柄マスタを取得する。CSVキャッシュ対応。429エラー時はリトライする。"""
    cache_key = f"code={code}"
    path = _cache_path("master", cache_key)
    cached = _read_cache(path)
    if cached is not None:
        return cached

    client = _get_client()
    df: pd.DataFrame = client.get_eq_master(code=code)
    _write_cache(path, df)
    return df


@_retry_on_rate_limit
def get_daily_quotes(code: str, from_date: str = "", to_date: str = "") -> pd.DataFrame:
    """株価日足データを取得する。CSVキャッシュ対応。429エラー時はリトライする。"""
    cache_key = f"code={code}&from={from_date}&to={to_date}"
    path = _cache_path("daily", cache_key)
    cached = _read_cache(path)
    if cached is not None:
        return cached

    client = _get_client()
    df: pd.DataFrame = client.get_eq_bars_daily(code=code, from_yyyymmdd=from_date, to_yyyymmdd=to_date)
    _write_cache(path, df)
    return df


@_retry_on_rate_limit
def get_financial_statements(code: str) -> pd.DataFrame:
    """決算サマリーを取得する。CSVキャッシュ対応。429エラー時はリトライする。"""
    cache_key = f"code={code}"
    path = _cache_path("financials", cache_key)
    cached = _read_cache(path)
    if cached is not None:
        return cached

    client = _get_client()
    df: pd.DataFrame = client.get_fin_summary(code=code)
    _write_cache(path, df)
    return df
