# stocks-study

## 概要

J-Quants API v2を使用した日本株データ分析Webアプリケーション。

銘柄検索、ローソク足チャート表示、テクニカル指標（SMA, RSI, MACD, ボリンジャーバンド）の可視化機能を提供する。

## 使用技術

- **Backend**: Python + FastAPI + jquants-api-client + pandas + ta
- **Frontend**: React + TypeScript + Vite + Recharts + TailwindCSS
- **パッケージ管理**: Poetry (Python), npm (JS)

## セットアップ

### 1. 依存関係のインストール

```bash
make install
```

### 2. 環境変数の設定

```bash
cp .env.example backend/.env
# backend/.env を編集して QUANTS_API_V2_API_KEY にリフレッシュトークンを設定
```

J-Quants API v2のリフレッシュトークンは [J-Quants](https://jpx-jquants.com/) でアカウント作成後に取得できます。

### 3. 開発サーバーの起動

```bash
make dev
```

- バックエンド: http://localhost:8000
- フロントエンド: http://localhost:5173

## 開発コマンド

```bash
make install           # 全依存関係インストール
make dev               # バックエンド+フロントエンド同時起動
make dev-backend       # バックエンドのみ
make dev-frontend      # フロントエンドのみ
make test              # バックエンドテスト
make lint              # リンター実行
make format            # コードフォーマット
```

## 主な機能

- 銘柄コード/名称による検索
- ローソク足チャート（移動平均線、ボリンジャーバンド付き）
- RSI / MACD テクニカル指標チャート
- 決算サマリー取得
- CSVキャッシュによるAPI呼び出し最適化

## 注意事項

- 本プロジェクトは学習目的です
- 投資判断は自己責任で行う必要があります
- 分析結果は将来の成果を保証するものではありません
