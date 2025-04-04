import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from src.db.models import Novel, Episode
from src.db.repository import save_evaluation, get_novel_episodes, has_existing_evaluation
from .llm_client import LLMClient

logger = logging.getLogger(__name__)

class NovelEvaluator:
    """
    小説評価エンジン
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.llm_client = LLMClient()
    
    def evaluate_novel(self, novel_id: str) -> Optional[Dict[str, Any]]:
        """
        指定された小説を評価する
        
        Args:
            novel_id: 評価対象の小説ID
            
        Returns:
            評価結果（スコアとフィードバック）
        """
        try:
            # 小説情報の取得
            novel = self.session.query(Novel).get(novel_id)
            if not novel:
                logger.error(f"Novel with ID {novel_id} not found")
                return None
            
            # 既存の評価があるかをチェック
            if has_existing_evaluation(self.session, novel_id):
                logger.info(f"Novel {novel.title} already has evaluation, skipping...")
                return None
            
            # エピソード情報の取得
            episodes = get_novel_episodes(self.session, novel_id, limit=3)
            if not episodes:
                logger.error(f"No episodes found for novel {novel_id}")
                return None
            
            # エピソードデータの整形
            episode_data = []
            for ep in episodes:
                episode_data.append({
                    'id': ep.id,
                    'title': ep.title,
                    'content': ep.content
                })
            
            # LLMによる評価
            evaluation = self.llm_client.evaluate_novel(
                title=novel.title,
                author=novel.author,
                episodes=episode_data
            )
            
            # 評価結果の保存 - 最初のエピソードに対してのみ保存
            save_evaluation(
                session=self.session,
                novel_id=novel_id,
                episode_id=episodes[0].id if episodes else None,
                scores={
                    'overall': evaluation['overall_score'],
                    'story': evaluation['story_score'],
                    'writing': evaluation['writing_score'],
                    'character': evaluation['character_score']
                },
                feedback=evaluation['feedback']
            )
            
            logger.info(f"Novel {novel.title} evaluated with score {evaluation['overall_score']}")
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating novel {novel_id}: {e}")
            return None
    
    def evaluate_novels_batch(self, novel_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        複数の小説をバッチで評価する
        
        Args:
            novel_ids: 評価対象の小説IDリスト
            
        Returns:
            小説IDをキー、評価結果を値とする辞書
        """
        results = {}
        
        for novel_id in novel_ids:
            result = self.evaluate_novel(novel_id)
            if result:
                results[novel_id] = result
        
        return results