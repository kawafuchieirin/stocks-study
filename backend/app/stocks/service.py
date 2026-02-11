from typing import Any, cast

from app.jquants_client import get_daily_quotes, get_financial_statements, get_stock_master
from app.utils import nan_to_none, normalize_date


def search_stocks(query: str = "") -> list[dict[str, Any]]:
    """銘柄マスタを検索する。コードまたは名称で部分一致検索。"""
    df = get_stock_master()
    if query:
        mask = df["Code"].astype(str).str.contains(query, case=False, na=False) | df["CoName"].str.contains(
            query, case=False, na=False
        )
        df = df[mask]
    # v2 APIカラム名マッピング
    columns = {
        "Code": "code",
        "CoName": "company_name",
        "CoNameEn": "company_name_english",
        "S17": "sector_17_code",
        "S17Nm": "sector_17_code_name",
        "S33": "sector_33_code",
        "S33Nm": "sector_33_code_name",
        "Mkt": "market_code",
        "MktNm": "market_code_name",
    }
    available_cols = {k: v for k, v in columns.items() if k in df.columns}
    df = df[list(available_cols.keys())].rename(columns=available_cols)
    # 銘柄マスタは文字列フィールドのみなのでfillna("")で統一
    return cast(list[dict[str, Any]], df.fillna("").to_dict(orient="records"))


def get_stock_daily(code: str, from_date: str = "", to_date: str = "") -> list[dict[str, Any]]:
    """株価日足データを取得する。"""
    df = get_daily_quotes(code, from_date, to_date)
    # v2 APIカラム名マッピング
    columns = {
        "Date": "date",
        "Code": "code",
        "O": "open",
        "H": "high",
        "L": "low",
        "C": "close",
        "Vo": "volume",
        "Va": "turnover_value",
        "AdjFactor": "adjustment_factor",
        "AdjO": "adjustment_open",
        "AdjH": "adjustment_high",
        "AdjL": "adjustment_low",
        "AdjC": "adjustment_close",
        "AdjVo": "adjustment_volume",
    }
    available_cols = {k: v for k, v in columns.items() if k in df.columns}
    df = df[list(available_cols.keys())].rename(columns=available_cols)
    # 日付形式を "YYYY-MM-DD" に統一する
    if "date" in df.columns:
        df["date"] = df["date"].map(normalize_date)
    # NaN→None変換（JSONではnullとして返す）
    records = cast(list[dict[str, Any]], df.to_dict(orient="records"))
    return nan_to_none(records)


def get_stock_financials(code: str) -> list[dict[str, Any]]:
    """決算サマリーを取得する。"""
    df = get_financial_statements(code)
    # NaN→None変換（JSONではnullとして返す）
    records = cast(list[dict[str, Any]], df.to_dict(orient="records"))
    return nan_to_none(records)
