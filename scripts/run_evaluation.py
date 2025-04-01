#!/usr/bin/env python
"""
カクヨム小説評価実行スクリプト

このスクリプトは、カクヨムの日刊ランキングから小説を取得し、
LLM APIを使用して評価するプロセスを実行します。
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.db.database import SessionLocal
from src.main import scrape_novels, evaluate_novels, display_results

# ログディレクトリの作成
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "evaluation.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="カクヨム小説評価実行スクリプト")
    parser.add_argument("--scrape", action="store_true", help="小説データを取得")
    parser.add_argument("--evaluate", action="store_true", help="小説を評価")
    parser.add_argument("--results", action="store_true", help="評価結果を表示")
    parser.add_argument("--limit", type=int, default=100, help="処理する小説数")
    
    args = parser.parse_args()
    
    # デフォルトの動作（引数なし）
    if not (args.scrape or args.evaluate or args.results):
        args.scrape = True
        args.evaluate = True
        args.results = True
    
    # DBセッション作成
    session = SessionLocal()
    
    try:
        if args.scrape:
            logger.info("スクレイピング処理を開始します")
            scrape_novels(session, limit=args.limit)
        
        if args.evaluate:
            logger.info("評価処理を開始します")
            evaluate_novels(session, limit=args.limit)
        
        if args.results:
            logger.info("評価結果を表示します")
            display_results(session, limit=args.limit)
            
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
