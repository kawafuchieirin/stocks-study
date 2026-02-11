import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import CandlestickChart from "../components/CandlestickChart";
import VolumeChart from "../components/VolumeChart";
import TechnicalChart from "../components/TechnicalChart";
import {
  getTechnicalIndicators,
  getStockInfo,
  classifyError,
} from "../services/api";
import type { TechnicalData, StockInfo } from "../types";

function getDefaultFromDate(): string {
  // Freeプランは2024年以降のデータのみ取得可能
  return "20240101";
}

export default function StockDetailPage() {
  const { code } = useParams<{ code: string }>();
  const [data, setData] = useState<TechnicalData[]>([]);
  const [stockInfo, setStockInfo] = useState<StockInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!code) return;

    setIsLoading(true);
    setError(null);
    try {
      const from = getDefaultFromDate();
      // 銘柄情報とテクニカルデータを並行取得
      const [info, result] = await Promise.all([
        getStockInfo(code),
        getTechnicalIndicators(code, from),
      ]);
      setStockInfo(info);
      setData(result);
      if (result.length === 0) {
        setError(
          "この期間のデータが取得できませんでした。Freeプランではデータ取得可能な期間が限定されています。"
        );
      }
    } catch (err) {
      setError(classifyError(err));
    } finally {
      setIsLoading(false);
    }
  }, [code]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (!code) {
    return <p>銘柄コードが指定されていません。</p>;
  }

  // 銘柄名の表示テキストを組み立てる
  const stockTitle = stockInfo
    ? `${stockInfo.company_name} (${code}) - ${stockInfo.market_code_name} / ${stockInfo.sector_33_code_name}`
    : `銘柄: ${code}`;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link
          to="/"
          className="text-blue-600 hover:text-blue-800 transition-colors"
        >
          &larr; 検索に戻る
        </Link>
        <h1 className="text-2xl font-bold text-gray-800">{stockTitle}</h1>
      </div>

      {/* エラー表示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-4 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg
              className="h-5 w-5 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <span>{error}</span>
          </div>
          <button
            onClick={fetchData}
            className="ml-4 px-4 py-1.5 bg-red-100 hover:bg-red-200 text-red-800 rounded-md text-sm font-medium transition-colors flex-shrink-0"
          >
            再読み込み
          </button>
        </div>
      )}

      {/* ローディング状態 */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-16 space-y-4">
          <div className="animate-spin h-10 w-10 border-4 border-blue-500 border-t-transparent rounded-full" />
          <div className="text-center space-y-1">
            <p className="text-gray-700 font-medium">
              銘柄データを取得中...
            </p>
            <p className="text-gray-500 text-sm">
              J-Quants API
              Freeプランのため少々お時間をいただく場合があります
            </p>
          </div>
        </div>
      ) : (
        data.length > 0 && (
          <>
            <CandlestickChart data={data} />
            <VolumeChart data={data} />
            <TechnicalChart data={data} />
          </>
        )
      )}
    </div>
  );
}
