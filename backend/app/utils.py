"""共通ユーティリティ関数。"""

import math
from typing import Any


def normalize_date(value: object) -> str:
    """日付文字列を "YYYY-MM-DD" 形式に統一する。

    "2024-01-04T00:00:00" のようなISO形式や "2024-01-04" をすべて "YYYY-MM-DD" に変換する。
    """
    s = str(value)
    if "T" in s:
        return s.split("T")[0]
    return s


def nan_to_none(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """レコード内のNaN値をNoneに変換する。JSONレスポンスでnullとして返すため。"""
    for row in records:
        for key, val in row.items():
            if isinstance(val, float) and math.isnan(val):
                row[key] = None
    return records
