import logging
from typing import Any

from fastapi import APIRouter, Query

from app.stocks.service import get_stock_daily, get_stock_financials, search_stocks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/master")
def list_stocks(q: str = Query("", description="銘柄コードまたは名称で検索")) -> list[dict[str, Any]]:
    """銘柄マスタを検索する。"""
    return search_stocks(q)


@router.get("/{code}/daily")
def daily_quotes(
    code: str,
    from_date: str = Query("", alias="from", description="開始日 (YYYYMMDD)"),
    to_date: str = Query("", alias="to", description="終了日 (YYYYMMDD)"),
) -> list[dict[str, Any]]:
    """株価日足データを取得する。"""
    try:
        return get_stock_daily(code, from_date, to_date)
    except Exception:
        logger.exception("J-Quants API error for code=%s", code)
        return []


@router.get("/{code}/financials")
def financials(code: str) -> list[dict[str, Any]]:
    """決算サマリーを取得する。"""
    try:
        return get_stock_financials(code)
    except Exception:
        logger.exception("J-Quants API error for code=%s", code)
        return []
