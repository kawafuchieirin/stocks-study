from pydantic import BaseModel


class StockInfo(BaseModel):
    code: str
    company_name: str
    company_name_english: str
    sector_17_code: str
    sector_17_code_name: str
    sector_33_code: str
    sector_33_code_name: str
    market_code: str
    market_code_name: str


class DailyQuote(BaseModel):
    date: str
    code: str
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: float | None = None
    turnover_value: float | None = None
    adjustment_factor: float | None = None
    adjustment_open: float | None = None
    adjustment_high: float | None = None
    adjustment_low: float | None = None
    adjustment_close: float | None = None
    adjustment_volume: float | None = None
