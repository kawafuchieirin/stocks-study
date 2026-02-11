export interface StockInfo {
  code: string;
  company_name: string;
  company_name_english: string;
  sector_17_code: string;
  sector_17_code_name: string;
  sector_33_code: string;
  sector_33_code_name: string;
  market_code: string;
  market_code_name: string;
}

export interface DailyQuote {
  date: string;
  code: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
  turnover_value: number | null;
  adjustment_factor: number | null;
  adjustment_open: number | null;
  adjustment_high: number | null;
  adjustment_low: number | null;
  adjustment_close: number | null;
  adjustment_volume: number | null;
}

export interface TechnicalData {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
  sma_5: number | null;
  sma_25: number | null;
  sma_75: number | null;
  rsi_14: number | null;
  macd: number | null;
  macd_signal: number | null;
  macd_histogram: number | null;
  bb_upper: number | null;
  bb_middle: number | null;
  bb_lower: number | null;
}
