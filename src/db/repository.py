from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, desc
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
    """評価データを保存"""
    try:
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
    """評価結果を取得"""
    try:
        results = []
        evaluations = session.query(Evaluation, Novel).\
            join(Novel, Evaluation.novel_id == Novel.id).\
            order_by(desc(Evaluation.evaluation_date)).\
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
        
        return results
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving evaluation results: {e}")
        return []
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from src.db.models import Novel, Episode
import logging

logger = logging.getLogger(__name__)

def save_novel(session: Session, novel: Novel, episodes: list[Episode]) -> bool:
    """小説データとエピソードデータを保存"""
    try:
        # 既存データのチェック
        existing_novel = session.query(Novel).get(novel.id)
        if existing_novel:
            logger.info(f"Novel {novel.id} already exists, updating data")
            # 既存データの更新
            for key, value in vars(novel).items():
                if key != '_sa_instance_state' and key != 'id':
                    setattr(existing_novel, key, value)
        else:
            session.add(novel)

        # エピソードの保存
        for episode in episodes:
            existing_episode = session.query(Episode).get(episode.id)
            if existing_episode:
                logger.info(f"Episode {episode.id} already exists, updating data")
                for key, value in vars(episode).items():
                    if key != '_sa_instance_state' and key != 'id':
                        setattr(existing_episode, key, value)
            else:
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
