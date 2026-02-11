import { useNavigate } from "react-router-dom";
import type { StockInfo } from "../types";

interface StockListProps {
  stocks: StockInfo[];
}

export default function StockList({ stocks }: StockListProps) {
  const navigate = useNavigate();

  if (stocks.length === 0) {
    return (
      <p className="text-gray-500 text-center py-8">
        該当する銘柄が見つかりませんでした。
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse bg-white rounded-lg shadow-sm">
        <thead>
          <tr className="bg-gray-100 text-left text-sm text-gray-600">
            <th className="px-4 py-3 font-medium">コード</th>
            <th className="px-4 py-3 font-medium">銘柄名</th>
            <th className="px-4 py-3 font-medium">セクター</th>
            <th className="px-4 py-3 font-medium">市場</th>
          </tr>
        </thead>
        <tbody>
          {stocks.map((stock) => (
            <tr
              key={stock.code}
              onClick={() => navigate(`/stocks/${stock.code}`)}
              className="border-t border-gray-100 hover:bg-blue-50 cursor-pointer transition-colors"
            >
              <td className="px-4 py-3 font-mono text-blue-600">
                {stock.code}
              </td>
              <td className="px-4 py-3">{stock.company_name}</td>
              <td className="px-4 py-3 text-sm text-gray-600">
                {stock.sector_33_code_name}
              </td>
              <td className="px-4 py-3 text-sm text-gray-600">
                {stock.market_code_name}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
