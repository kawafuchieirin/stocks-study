import axios, { AxiosError } from "axios";
import type { StockInfo, TechnicalData } from "../types";

const client = axios.create({ baseURL: "/api" });

/**
 * APIエラーを分類し、ユーザー向けのメッセージを返す
 */
export function classifyError(err: unknown): string {
  if (err instanceof AxiosError) {
    if (!err.response) {
      // ネットワーク接続の問題（タイムアウト、DNS解決失敗など）
      return "ネットワークエラー: サーバーに接続できませんでした。インターネット接続を確認してください。";
    }
    const status = err.response.status;
    if (status === 404) {
      return "指定された銘柄が見つかりませんでした。銘柄コードを確認してください。";
    }
    if (status === 429) {
      return "APIのリクエスト制限に達しました。しばらく待ってから再度お試しください。";
    }
    if (status >= 500) {
      return "サーバーエラーが発生しました。しばらく待ってから再度お試しください。";
    }
    return `APIエラーが発生しました（ステータス: ${status}）。`;
  }
  if (err instanceof Error) {
    return err.message;
  }
  return "予期しないエラーが発生しました。";
}

export async function searchStocks(query: string): Promise<StockInfo[]> {
  const { data } = await client.get<StockInfo[]>("/stocks/master", {
    params: { q: query },
  });
  return data;
}

/**
 * 銘柄コードから銘柄情報を取得する。
 * マスタAPIで検索し、完全一致する銘柄を返す。
 */
export async function getStockInfo(code: string): Promise<StockInfo | null> {
  const { data } = await client.get<StockInfo[]>("/stocks/master", {
    params: { q: code },
  });
  // 銘柄コードが完全一致するものを返す
  return data.find((s) => s.code === code) ?? null;
}

export async function getDailyQuotes(
  code: string,
  from?: string,
  to?: string
) {
  const { data } = await client.get(`/stocks/${code}/daily`, {
    params: { from, to },
  });
  return data;
}

export async function getTechnicalIndicators(
  code: string,
  from?: string,
  to?: string
): Promise<TechnicalData[]> {
  const { data } = await client.get<TechnicalData[]>(
    `/analysis/${code}/technical`,
    { params: { from, to } }
  );
  return data;
}

export async function getFinancials(code: string) {
  const { data } = await client.get(`/stocks/${code}/financials`);
  return data;
}
