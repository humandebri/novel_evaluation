from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, desc, func
from src.db.models import Novel, Episode, Evaluation
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

def save_novel_data(
    session: Session,
    novel_id: str,
    title: str,
    author: str,
    ranking_position: int,
    novel_url: str,
    genre: Optional[str] = None,
    episodes: Optional[List[Dict[str, Any]]] = None
) -> bool:
    """小説データとエピソードデータを保存"""
    try:
        # 小説データの更新または作成
        novel = session.query(Novel).get(novel_id)
        if novel:
            novel.title = title
            novel.author = author
            novel.ranking_position = ranking_position
            novel.novel_url = novel_url
            if genre:
                novel.genre = genre
            novel.updated_at = datetime.utcnow()
        else:
            novel = Novel(
                id=novel_id,
                title=title,
                author=author,
                ranking_position=ranking_position,
                novel_url=novel_url,
                genre=genre
            )
            session.add(novel)

        # エピソードデータの更新または作成
        if episodes:
            for ep in episodes:
                episode = session.query(Episode).get(ep['id'])
                if episode:
                    episode.title = ep['title']
                    episode.content = ep['content']
                    episode.posted_at = ep['posted_at']
                else:
                    episode = Episode(
                        id=ep['id'],
                        novel_id=novel_id,
                        title=ep['title'],
                        content=ep['content'],
                        posted_at=ep['posted_at']
                    )
                    session.add(episode)

        session.commit()
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database error occurred: {e}")
        session.rollback()
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        session.rollback()
        return False

def save_evaluation(
    session: Session,
    novel_id: str,
    episode_id: Optional[str],
    scores: Dict[str, float],
    feedback: str
) -> bool:
    """評価データを保存 - 同じ小説の既存の評価は削除"""
    try:
        # 同じ小説の既存の評価を削除
        existing_evaluations = session.query(Evaluation).filter(
            Evaluation.novel_id == novel_id
        ).all()
        
        for eval in existing_evaluations:
            session.delete(eval)
        
        # 新しい評価を保存
        evaluation = Evaluation(
            novel_id=novel_id,
            episode_id=episode_id,
            overall_score=scores['overall'],
            story_score=scores.get('story'),
            writing_score=scores.get('writing'),
            character_score=scores.get('character'),
            llm_feedback=feedback
        )
        session.add(evaluation)
        session.commit()
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database error occurred: {e}")
        session.rollback()
        return False

def get_novels_for_evaluation(session: Session, limit: int = 100) -> List[Novel]:
    """評価対象の小説を取得"""
    try:
        return session.query(Novel).order_by(Novel.ranking_position).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving novels: {e}")
        return []

def get_novel_episodes(session: Session, novel_id: str, limit: int = 3) -> List[Episode]:
    """小説のエピソードを取得"""
    try:
        return session.query(Episode).filter(Episode.novel_id == novel_id).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving episodes: {e}")
        return []

def get_evaluation_results(session: Session, limit: int = 100) -> List[Dict[str, Any]]:
    """評価結果を取得 - 重複なし、総合評価スコア順に並べ替え"""
    try:
        results = []
        
        # 最新の評価だけを取得し、総合評価スコアの降順で並べ替え
        # PostgreSQLのDISTINCT ON構文に合わせて修正
        evaluations = session.query(Evaluation, Novel).\
            join(Novel, Evaluation.novel_id == Novel.id).\
            order_by(Evaluation.novel_id, desc(Evaluation.overall_score)).\
            distinct(Evaluation.novel_id).\
            limit(limit).all()
            
        for eval, novel in evaluations:
            results.append({
                "novel_id": novel.id,
                "title": novel.title,
                "author": novel.author,
                "ranking": novel.ranking_position,
                "overall_score": eval.overall_score,
                "story_score": eval.story_score,
                "writing_score": eval.writing_score,
                "character_score": eval.character_score,
                "feedback": eval.llm_feedback,
                "evaluation_date": eval.evaluation_date
            })
        
        # 総合評価スコアで並べ替え
        results = sorted(results, key=lambda x: x["overall_score"], reverse=True)
        return results
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving evaluation results: {e}")
        return []

def has_existing_evaluation(session: Session, novel_id: str) -> bool:
    """
    指定された小説IDの評価が既に存在するかどうかを確認
    
    Args:
        session: DBセッション
        novel_id: 小説ID
        
    Returns:
        評価が存在する場合はTrue、そうでない場合はFalse
    """
    try:
        count = session.query(Evaluation).filter(Evaluation.novel_id == novel_id).count()
        return count > 0
    except SQLAlchemyError as e:
        logger.error(f"Error checking existing evaluation: {e}")
        # エラーの場合は安全側に倒して存在するとみなす
        return True

def export_evaluation_results_to_csv(session: Session, filepath: str) -> bool:
    """
    評価結果をCSVファイルにエクスポート
    
    Args:
        session: DBセッション
        filepath: 出力ファイルパス
        
    Returns:
        成功した場合はTrue、失敗した場合はFalse
    """
    import csv
    import os
    
    try:
        # フォルダがなければ作成
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 全ての評価結果を取得（制限なし）
        results = get_evaluation_results(session, limit=10000)
        
        if not results:
            logger.warning("No evaluation results to export")
            return False
            
        # CSVファイルに書き出し
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                "novel_id", "title", "author", "ranking", 
                "overall_score", "story_score", "writing_score", "character_score", 
                "feedback", "evaluation_date"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                writer.writerow(result)
                
        logger.info(f"Exported {len(results)} evaluation results to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error exporting evaluation results to CSV: {e}")
        return False