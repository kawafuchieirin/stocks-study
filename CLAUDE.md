# CLAUDE.md - stocks-study

## 概要

J-Quants API v2を使用した日本株データ分析Webアプリ。テクニカル分析（SMA, RSI, MACD, ボリンジャーバンド）をチャートで可視化する。

## 技術スタック

- **Backend**: Python 3.12+, FastAPI, jquants-api-client, pandas, ta
- **Frontend**: React 19, TypeScript, Vite, Recharts, TailwindCSS
- **Data Platform**: AWS Lambda, Glue Python Shell, Step Functions, S3, Athena
- **Infrastructure**: Terraform (~> 5.0)
- **パッケージ管理**: Poetry (Python), npm (JS)
- **コード品質**: Ruff, mypy

## 開発コマンド

```bash
# Webアプリ
make install           # 全依存関係インストール
make dev               # バックエンド(8000)+フロントエンド(5173)同時起動
make dev-backend       # バックエンドのみ
make dev-frontend      # フロントエンドのみ
make test              # バックエンドテスト
make lint              # Ruff + mypy
make format            # コードフォーマット

# データプラットフォーム
make install-platform  # data-platform依存関係インストール
make test-platform     # data-platformテスト
make lint-platform     # data-platformリント
make package-lambda    # Lambda Layer + 関数ZIPビルド（Docker必要）
make tf-init           # Terraform初期化
make tf-plan           # Terraformプラン
make tf-apply          # Terraformデプロイ
make tf-destroy        # Terraform削除
make run-pipeline      # Step Functionsパイプライン手動実行
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

## データプラットフォーム (`data-platform/` + `terraform/`)

### アーキテクチャ

```
EventBridge Scheduler (毎週日曜 03:00 JST)
    ↓
Step Functions パイプライン
    ↓
1. Lambda Ingest (master/daily/financials) → S3 raw/ (JSON)
2. Glue Python Shell Transform              → S3 processed/ (Parquet)
3. Glue Python Shell Enrich (テクニカル指標) → S3 analytics/ (Parquet)
4. Glue Crawler                             → Data Catalog 更新
    ↓
Athena (SQLクエリ・分析)
```

### S3レイヤー構造（Hive パーティション: year/month/day）

```
s3://stocks-study-dev-datalake-{account_id}/
├── raw/{data_type}/year=YYYY/month=MM/day=DD/     # JSON, 90日で自動削除
├── processed/{data_type}/year=YYYY/month=MM/day=DD/ # Parquet
├── analytics/technical/year=YYYY/month=MM/day=DD/   # Parquet
└── athena-results/                                   # 7日で自動削除
```

### ディレクトリ構造

- `data-platform/lambda/ingest/`: Lambda Ingest関数（J-Quants API → S3 raw/）
- `data-platform/glue/transform.py`: JSON → Parquet変換
- `data-platform/glue/enrich.py`: テクニカル指標算出（backendのtechnical.pyと同一ロジック）
- `data-platform/stepfunctions/pipeline.asl.json`: Step Functions ASL定義
- `data-platform/tests/`: ユニットテスト（motoでS3モック）
- `terraform/`: 全AWSリソースのIaC

### Terraform環境変数

```bash
# terraform.tfvars（.gitignore済）
jquants_api_key = "your_refresh_token_here"
```

### テスト

```bash
cd data-platform && poetry run pytest tests/ -v
```

- `test_ingest_handler.py`: Lambda handler（moto S3 + mock J-Quants API）
- `test_transform.py`: JSON→Parquet変換、型正規化
- `test_enrich.py`: テクニカル指標算出 + backend実装との一致検証
