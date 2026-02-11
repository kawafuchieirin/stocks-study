# stocks-study

## 概要

J-Quants API v2を使用した日本株データ分析プロジェクト。

1. **Webアプリ** — 銘柄検索、ローソク足チャート、テクニカル指標（SMA, RSI, MACD, ボリンジャーバンド）の可視化
2. **AWSデータプラットフォーム** — S3データレイク上で株価データを自動収集・変換・分析するパイプライン

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│  Webアプリ（ローカル開発）                                  │
│  FastAPI (8080) ←→ React (5173)                         │
│  └─ J-Quants API → CSVキャッシュ → テクニカル分析           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  AWSデータプラットフォーム                                  │
│                                                         │
│  EventBridge Scheduler (毎週日曜 03:00 JST)              │
│      ↓                                                  │
│  Step Functions パイプライン                               │
│      ↓                                                  │
│  1. Lambda Ingest  → S3 raw/       (JSON)               │
│  2. Glue Transform → S3 processed/ (Parquet)            │
│  3. Glue Enrich    → S3 analytics/ (Parquet)            │
│  4. Glue Crawler   → Data Catalog                       │
│      ↓                                                  │
│  Athena (SQLクエリ・分析)                                  │
└─────────────────────────────────────────────────────────┘
```

## 使用技術

| レイヤー | 技術 |
|---------|------|
| Backend | Python 3.12+, FastAPI, jquants-api-client, pandas, ta |
| Frontend | React 19, TypeScript, Vite, Recharts, TailwindCSS |
| Data Platform | AWS Lambda, Glue Python Shell, Step Functions, S3, Athena |
| Infrastructure | Terraform (~> 5.0) |
| パッケージ管理 | Poetry (Python), npm (JS) |
| コード品質 | Ruff, mypy |

## セットアップ

### 前提条件

- Python 3.12+
- Node.js 20+
- Poetry
- [J-Quants](https://jpx-jquants.com/) アカウント（リフレッシュトークン取得用）
- Terraform 1.7+（データプラットフォーム利用時）
- Docker（Lambda Layerビルド時）

### 1. 依存関係のインストール

```bash
make install            # Webアプリ（backend + frontend）
make install-platform   # データプラットフォーム
```

### 2. 環境変数の設定

```bash
# Webアプリ用
cp .env.example backend/.env
# backend/.env を編集して QUANTS_API_V2_API_KEY にリフレッシュトークンを設定
```

```bash
# データプラットフォーム用
cat > terraform/terraform.tfvars << 'EOF'
jquants_api_key = "your_refresh_token_here"
EOF
```

### 3. 開発サーバーの起動

```bash
make dev
```

- バックエンド: http://localhost:8080
- フロントエンド: http://localhost:5173

## 開発コマンド

### Webアプリ

```bash
make install           # 全依存関係インストール
make dev               # バックエンド+フロントエンド同時起動
make dev-backend       # バックエンドのみ
make dev-frontend      # フロントエンドのみ
make test              # バックエンドテスト
make lint              # リンター実行
make format            # コードフォーマット
```

### データプラットフォーム

```bash
make install-platform  # 依存関係インストール
make test-platform     # テスト実行
make lint-platform     # リンター実行
make package-lambda    # Lambda Layer + 関数ZIPビルド（Docker必要）
```

### Terraform

```bash
make tf-init           # Terraform初期化
make tf-plan           # 変更プレビュー
make tf-apply          # AWSデプロイ
make tf-destroy        # AWS全リソース削除
make run-pipeline      # Step Functionsパイプライン手動実行
```

## ディレクトリ構成

```
stocks-study/
├── backend/                     # FastAPI バックエンド
│   ├── app/
│   │   ├── main.py              #   エントリーポイント
│   │   ├── config.py            #   環境変数管理
│   │   ├── jquants_client.py    #   J-Quants APIクライアント + CSVキャッシュ
│   │   ├── stocks/              #   銘柄マスタ・株価データAPI
│   │   └── analysis/            #   テクニカル分析API
│   └── tests/
├── frontend/                    # React フロントエンド
│   └── src/
│       ├── pages/               #   ダッシュボード、銘柄詳細
│       └── components/          #   チャートコンポーネント
├── data-platform/               # AWSデータプラットフォーム
│   ├── lambda/ingest/           #   Lambda Ingest関数
│   ├── glue/
│   │   ├── transform.py         #   JSON→Parquet変換
│   │   └── enrich.py            #   テクニカル指標算出
│   ├── stepfunctions/
│   │   └── pipeline.asl.json    #   Step Functions定義
│   └── tests/
├── terraform/                   # インフラストラクチャ
│   ├── main.tf                  #   Provider, locals
│   ├── s3.tf                    #   S3データレイク
│   ├── lambda.tf                #   Lambda関数
│   ├── glue.tf                  #   Glue Jobs + Crawler
│   ├── stepfunctions.tf         #   Step Functionsステートマシン
│   ├── eventbridge.tf           #   EventBridge Scheduler
│   ├── athena.tf                #   Athenaワークグループ
│   ├── iam.tf                   #   IAMロール・ポリシー
│   └── cloudwatch.tf            #   CloudWatchロググループ
└── Makefile
```

## S3データレイク構造

全レイヤーで Hive スタイルの `year/month/day` パーティションを使用。

```
s3://stocks-study-dev-datalake-{account_id}/
├── raw/                                          # Lambda出力（JSON、90日で自動削除）
│   ├── master/year=YYYY/month=MM/day=DD/
│   ├── daily/year=YYYY/month=MM/day=DD/
│   └── financials/year=YYYY/month=MM/day=DD/
├── processed/                                    # Glue Transform出力（Parquet）
│   ├── master/year=YYYY/month=MM/day=DD/
│   ├── daily/year=YYYY/month=MM/day=DD/
│   └── financials/year=YYYY/month=MM/day=DD/
├── analytics/                                    # Glue Enrich出力（Parquet）
│   └── technical/year=YYYY/month=MM/day=DD/
└── athena-results/                               # Athenaクエリ結果（7日で自動削除）
```

## APIエンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/stocks/master?q=` | 銘柄検索 |
| GET | `/api/stocks/{code}/daily?from=&to=` | 株価日足 |
| GET | `/api/stocks/{code}/financials` | 決算サマリー |
| GET | `/api/analysis/{code}/technical?from=&to=` | テクニカル指標 |
| GET | `/api/health` | ヘルスチェック |

## コスト見積もり（データプラットフォーム、月額）

| サービス | 概算 |
|---------|------|
| S3 (~100MB) | ~$0.01 |
| Lambda (週1回x3) | 無料枠内 |
| Glue Python Shell (週2回, 0.0625DPU) | ~$0.35 |
| Step Functions (週1回x6ステート) | 無料枠内 |
| Athena (月数回, <100MBスキャン) | ~$0.00 |
| **合計** | **~$0.40/月** |

## テスト

```bash
# Webアプリ
make test              # 18 passed

# データプラットフォーム
make test-platform     # 18 passed
```

## 注意事項

- 本プロジェクトは学習目的です
- 投資判断は自己責任で行う必要があります
- 分析結果は将来の成果を保証するものではありません
- J-Quants Freeプランにはレート制限（5回/分）があります
