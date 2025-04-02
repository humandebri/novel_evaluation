# カクヨム小説評価システム

カクヨムの日刊ランキング上位100タイトルから各3話を取得し、LLM APIを使用して小説の面白さを10点満点で評価するシステムです。

## 機能

- カクヨムの日刊ランキングから上位100タイトルを自動取得
- 各小説の最初の3話を取得
- LLM APIを使用して小説を評価（10点満点）
  - ストーリー性
  - 文章力
  - キャラクター
  - 総合評価
- 評価結果をPostgreSQLデータベースに保存
- 評価結果の表示

## システム構成

- **データベース**: PostgreSQL
- **言語**: Python
- **主要ライブラリ**:
  - SQLAlchemy (ORM)
  - BeautifulSoup4 (スクレイピング)
  - Requests (HTTP通信)
  - FastAPI (APIサーバー、オプション)

## セットアップ

### 前提条件

- Python 3.9以上
- Docker & Docker Compose
- LLM API キー (DeepSeek API)

### インストール手順

1. リポジトリをクローン
```bash
git clone <repository-url>
cd novel_evaluation_system
```

2. 仮想環境を作成してアクティベート
```bash
python3.12 -m venv venv_py312
source venv_py312/bin/activate
```

3. 依存パッケージをインストール
```bash
pip install -r requirements.txt
```

4. 環境変数を設定
```bash
# .envファイルを編集してLLM APIキーなどを設定
nano .env
```

5. PostgreSQLデータベースを起動
```bash
docker-compose up -d
```

6. データベースの初期化
```bash
python -m src.scripts.init_db
```

## 使用方法

### 基本的な使い方

```bash
# 全ての処理を実行（スクレイピング、評価、結果表示）
python -m src.main

# スクレイピングのみ実行
python -m src.main --scrape

# 評価のみ実行
python -m src.main --evaluate

# 結果表示のみ実行
python -m src.main --results

# 処理する小説数を制限
python -m src.main --limit 10
```

### PGAdminへのアクセス

データベースの内容を確認するには、ブラウザで以下のURLにアクセスします：
```
http://localhost:5050
```

ログイン情報：
- Email: admin@example.com
- Password: admin

## プロジェクト構造

```
novel_evaluation_system/
│
├── src/
│   ├── __init__.py
│   ├── config.py                  # 設定ファイル
│   ├── main.py                    # メインエントリーポイント
│   │
│   ├── db/                        # データベース関連
│   │   ├── __init__.py
│   │   ├── models.py              # SQLAlchemyモデル定義
│   │   ├── database.py            # DB接続管理
│   │   └── repository.py          # DBアクセス関数
│   │
│   ├── scraper/                   # スクレイピング関連
│   │   ├── __init__.py
│   │   ├── kakuyomu.py            # カクヨムランキング・作品情報取得
│   │   └── utils.py               # スクレイピング用ユーティリティ
│   │
│   ├── evaluator/                 # 評価エンジン
│   │   ├── __init__.py
│   │   ├── llm_client.py          # LLM API接続
│   │   ├── prompt_manager.py      # プロンプト管理
│   │   └── evaluator.py           # 評価ロジック
│   │
│   └── api/                       # APIサーバー（オプション）
│       ├── __init__.py
│       ├── server.py              # FastAPI定義
│       └── endpoints/             # APIエンドポイント
│
├── scripts/                       # 運用スクリプト
│   ├── init_db.py                 # DB初期化
│   ├── backup.py                  # バックアップ
│   └── run_evaluation.py          # 評価実行
│
├── tests/                         # テスト
│   ├── __init__.py
│   ├── test_scraper.py
│   ├── test_evaluator.py
│   └── test_db.py
│
├── logs/                          # ログファイル
│
├── alembic/                       # マイグレーション
│   ├── versions/
│   └── alembic.ini
│
├── requirements.txt               # 依存パッケージ
├── README.md                      # プロジェクト説明
├── docker-compose.yml             # Docker Compose設定
└── .env                           # 環境変数（gitignore対象）
```

## 注意事項

- カクヨムのウェブサイト利用規約を遵守してください
- スクレイピングの間隔を適切に設定し、サーバーに負荷をかけないようにしてください
- LLM APIの利用料金に注意してください
