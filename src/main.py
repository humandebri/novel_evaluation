import logging
import argparse
import sys
from sqlalchemy.orm import Session
import os
import logging


from src.db.database import SessionLocal
from src.scraper.kakuyomu import KakuyomuScraper
from src.evaluator.evaluator import NovelEvaluator
from src.db.repository import get_novels_for_evaluation, save_novel_data, get_evaluation_results, export_evaluation_results_to_csv

# ロギング設定
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
# 結果ディレクトリも作成
results_dir = "results"
os.makedirs(results_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir + "/novel_evaluation.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def scrape_novels(session: Session, limit: int = 100):
    """
    カクヨムからランキング上位の小説を取得してDBに保存
    """
    logger.info(f"Starting to scrape top {limit} novels from Kakuyomu")
    
    scraper = KakuyomuScraper()
    novels = scraper.get_daily_ranking(limit=limit)
    
    for novel in novels:
        logger.info(f"Processing novel: {novel['title']} by {novel['author']}")
        
        # 小説の最初の1話を取得
        episode = scraper.get_first_episode(novel['id'])
        
        # DBに保存
        save_novel_data(
            session=session,
            novel_id=novel['id'],
            title=novel['title'],
            author=novel['author'],
            ranking_position=novel['ranking_position'],
            novel_url=novel['novel_url'],
            episodes=[episode] if episode else None
        )
    
    logger.info(f"Completed scraping {len(novels)} novels")

def evaluate_novels(session: Session, limit: int = 100):
    """
    DBに保存された小説を評価
    """
    logger.info(f"Starting to evaluate novels")
    
    # 評価対象の小説を取得
    novels = get_novels_for_evaluation(session, limit=limit)
    
    if not novels:
        logger.warning("No novels found for evaluation")
        return
    
    evaluator = NovelEvaluator(session)
    
    for novel in novels:
        logger.info(f"Evaluating novel: {novel.title} by {novel.author}")
        result = evaluator.evaluate_novel(novel.id)
        
        if result:
            logger.info(f"Evaluation complete: Overall score {result['overall_score']}")
        else:
            logger.error(f"Failed to evaluate novel {novel.title}")
    
    logger.info(f"Completed evaluating {len(novels)} novels")

def display_results(session: Session, limit: int = 10):
    """
    評価結果を表示（総合評価スコア順）
    """
    results = get_evaluation_results(session, limit=limit)
    
    if not results:
        print("No evaluation results found")
        return
    
    print("\n===== 小説評価結果（総合評価スコア順） =====\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']} by {result['author']}")
        print(f"   ランキング: {result['ranking']}位")
        print(f"   総合評価: {result['overall_score']:.1f}/10")
        print(f"   ストーリー: {result['story_score']:.1f}/10")
        print(f"   文章力: {result['writing_score']:.1f}/10")
        print(f"   キャラクター: {result['character_score']:.1f}/10")
        print(f"   評価日: {result['evaluation_date'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   評価コメント: {result['feedback'][:100]}...")
        print()
    
    # 評価結果をCSVに書き出し
    from src.db.repository import export_evaluation_results_to_csv
    export_filepath = "results/evaluation_results.csv"
    if export_evaluation_results_to_csv(session, export_filepath):
        print(f"\n評価結果を {export_filepath} にエクスポートしました。")
    else:
        print("\n評価結果のエクスポートに失敗しました。")

def main():
    parser = argparse.ArgumentParser(description="カクヨム小説評価システム")
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
            scrape_novels(session, limit=args.limit)
        
        if args.evaluate:
            evaluate_novels(session, limit=args.limit)
        
        if args.results:
            display_results(session, limit=args.limit)
            
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()