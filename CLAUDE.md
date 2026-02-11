# CLAUDE.md - stocks-study

## 概要

J-Quants API v2を使用した日本株データ分析Webアプリ。テクニカル分析（SMA, RSI, MACD, ボリンジャーバンド）をチャートで可視化する。

## 技術スタック

- **Backend**: Python 3.12+, FastAPI, jquants-api-client, pandas, ta
- **Frontend**: React 19, TypeScript, Vite, Recharts, TailwindCSS
- **パッケージ管理**: Poetry (Python), npm (JS)
- **コード品質**: Ruff, mypy

## 開発コマンド

```bash
make install           # 全依存関係インストール
make dev               # バックエンド(8000)+フロントエンド(5173)同時起動
make dev-backend       # バックエンドのみ
make dev-frontend      # フロントエンドのみ
make test              # バックエンドテスト
make lint              # Ruff + mypy
make format            # コードフォーマット
```

## 環境変数

`.env`ファイルを`backend/`配下に作成:

```
QUANTS_API_V2_API_KEY=your_refresh_token_here
```

J-Quants API v2のリフレッシュトークンを設定する。[J-Quants](https://jpx-jquants.com/)でアカウント作成後に取得可能。

## アーキテクチャ

### バックエンド (`backend/`)

- `app/main.py`: FastAPIエントリーポイント（CORS設定、ルーター登録）
- `app/config.py`: 環境変数管理（pydantic-settings）
- `app/jquants_client.py`: J-Quants APIクライアント + CSVキャッシュ
- `app/stocks/`: 銘柄マスタ・株価データのAPI
- `app/analysis/`: テクニカル分析のAPI

### フロントエンド (`frontend/`)

- `src/pages/DashboardPage.tsx`: 銘柄検索ページ
- `src/pages/StockDetailPage.tsx`: チャート表示ページ
- `src/components/CandlestickChart.tsx`: ローソク足+移動平均+BB
- `src/components/TechnicalChart.tsx`: RSI, MACDサブチャート

### APIエンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/stocks/master?q=` | 銘柄検索 |
| GET | `/api/stocks/{code}/daily?from=&to=` | 株価日足 |
| GET | `/api/stocks/{code}/financials` | 決算サマリー |
| GET | `/api/analysis/{code}/technical?from=&to=` | テクニカル指標 |
| GET | `/api/health` | ヘルスチェック |

### CSVキャッシュ

`backend/data/`配下にCSVキャッシュを保存し、Freeプランのレート制限（5回/分）に対応。同日の同一リクエストはキャッシュから返す。

## テスト

```bash
cd backend && poetry run pytest tests/ -v
```

- `test_jquants_client.py`: CSVキャッシュの読み書き、API呼び出しのモック
- `test_technical.py`: SMA, RSI, MACD, BBの計算精度
