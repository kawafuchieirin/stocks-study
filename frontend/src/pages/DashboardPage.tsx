import { useState, useRef } from "react";
import SearchBar from "../components/SearchBar";
import StockList from "../components/StockList";
import { searchStocks, classifyError } from "../services/api";
import type { StockInfo } from "../types";

export default function DashboardPage() {
  const [stocks, setStocks] = useState<StockInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  // 最後に検索したクエリを保持し、再検索に利用
  const lastQueryRef = useRef<string>("");

  const handleSearch = async (query: string) => {
    lastQueryRef.current = query;
    setIsLoading(true);
    setError(null);
    try {
      const results = await searchStocks(query);
      setStocks(results);
      setHasSearched(true);
    } catch (err) {
      setError(classifyError(err));
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    if (lastQueryRef.current) {
      void handleSearch(lastQueryRef.current);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800 mb-2">銘柄検索</h1>
        <p className="text-gray-600">
          銘柄コードまたは名称で検索して、詳細な株価チャートやテクニカル指標を確認できます。
        </p>
      </div>

      <SearchBar onSearch={handleSearch} isLoading={isLoading} />

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
            onClick={handleRetry}
            className="ml-4 px-4 py-1.5 bg-red-100 hover:bg-red-200 text-red-800 rounded-md text-sm font-medium transition-colors flex-shrink-0"
          >
            再読み込み
          </button>
        </div>
      )}

      {hasSearched && <StockList stocks={stocks} />}
    </div>
  );
}
