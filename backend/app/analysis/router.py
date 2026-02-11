import logging
from typing import Any, cast

from fastapi import APIRouter, Query

from app.analysis.technical import compute_technical_indicators
from app.jquants_client import get_daily_quotes
from app.utils import nan_to_none, normalize_date

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/{code}/technical")
def technical_indicators(
    code: str,
    from_date: str = Query("", alias="from", description="開始日 (YYYYMMDD)"),
    to_date: str = Query("", alias="to", description="終了日 (YYYYMMDD)"),
) -> list[dict[str, Any]]:
    """テクニカル指標を算出して返す。"""
    try:
        df = get_daily_quotes(code, from_date, to_date)
    except Exception:
        logger.exception("J-Quants API error for code=%s", code)
        return []

    # v2 APIカラム名を内部名にマッピング（調整後の値を優先）
    col_map: dict[str, str] = {
        "Date": "date",
        "AdjC": "close",
        "AdjO": "open",
        "AdjH": "high",
        "AdjL": "low",
        "AdjVo": "volume",
    }
    # v2カラムがない場合のフォールバック
    if "AdjC" not in df.columns and "C" in df.columns:
        col_map["C"] = "close"

    df = df.rename(columns=col_map)

    if "close" not in df.columns or df.empty:
        return []

    # 日付形式を "YYYY-MM-DD" に統一する
    if "date" in df.columns:
        df["date"] = df["date"].map(normalize_date)

    df = compute_technical_indicators(df)

    result_columns = [
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "sma_5",
        "sma_25",
        "sma_75",
        "rsi_14",
        "macd",
        "macd_signal",
        "macd_histogram",
        "bb_upper",
        "bb_middle",
        "bb_lower",
    ]
    available = [c for c in result_columns if c in df.columns]
    df = df[available]
    records: list[dict[str, Any]] = cast(list[dict[str, Any]], df.to_dict(orient="records"))
    # NaN→Noneに変換（JSONではnullとして返す）
    return nan_to_none(records)
