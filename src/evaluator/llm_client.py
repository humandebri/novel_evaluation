import requests
import json
import logging
from typing import Dict, Any, Optional, List
from src.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.api_key = settings.llm_api_key
        self.endpoint = settings.llm_endpoint
        self.model = settings.llm_model
        
        if not self.api_key:
            logger.warning("LLM API key not set. Evaluation will not work.")
    
    def evaluate_novel(self, title: str, author: str, episodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        小説の内容をLLMで評価し、スコアとフィードバックを返す
        """
        if not self.api_key:
            return {
                "overall_score": 0.0,
                "story_score": 0.0,
                "writing_score": 0.0,
                "character_score": 0.0,
                "feedback": "API key not configured"
            }
        
        # エピソードの内容を取得
        episode_texts = []
        for episode in episodes:
            episode_texts.append(f"タイトル: {episode['title']}\n\n{episode['content']}")
        
        # プロンプトの構築
        prompt = self._build_evaluation_prompt(title, author, episode_texts)
        
        try:
            # LLM APIを呼び出し
            response = self._call_llm_api(prompt)
            
            # レスポンスを解析
            return self._parse_evaluation_response(response)
            
        except Exception as e:
            logger.error(f"Error evaluating novel: {e}")
            return {
                "overall_score": 0.0,
                "story_score": 0.0,
                "writing_score": 0.0,
                "character_score": 0.0,
                "feedback": f"評価中にエラーが発生しました: {str(e)}"
            }
    
    def _build_evaluation_prompt(self, title: str, author: str, episode_texts: List[str]) -> str:
        """
        評価用のプロンプトを構築
        """
        prompt = f"""あなたはプロの文学評論家です。以下の小説を評価してください。

タイトル: {title}
作者: {author}

以下の3つのエピソードを読んで、小説の質を10点満点で評価してください。
評価は絶対的な基準で行い、相対評価ではなく絶対評価としてください。

{'-' * 50}
{'-' * 50}
{'-' * 50}

{episode_texts[0]}

{'-' * 50}

{episode_texts[1] if len(episode_texts) > 1 else "エピソード2は利用できません。"}

{'-' * 50}

{episode_texts[2] if len(episode_texts) > 2 else "エピソード3は利用できません。"}

{'-' * 50}

以下の観点から評価し、各項目のスコアと理由を詳しく説明してください：

1. ストーリー性 (10点満点): 物語の展開、構成、オリジナリティ
2. 文章力 (10点満点): 表現力、読みやすさ、言葉の選択
3. キャラクター (10点満点): 登場人物の魅力、深み、成長
4. 総合評価 (10点満点): 全体的な作品の質

必ず以下のJSON形式で回答してください：
```json
{
  "story_score": 数値,
  "writing_score": 数値,
  "character_score": 数値,
  "overall_score": 数値,
  "feedback": "詳細な評価コメント"
}
```

評価は厳格かつ公平に行い、プロの文学評論家として真摯な評価を提供してください。
"""
        return prompt
    
    def _call_llm_api(self, prompt: str) -> str:
        """
        LLM APIを呼び出し、レスポンスを取得
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a professional literary critic who evaluates novels."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        response = requests.post(
            self.endpoint,
            headers=headers,
            data=json.dumps(payload),
            timeout=60
        )
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code} - {response.text}")
            raise Exception(f"API error: {response.status_code}")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _parse_evaluation_response(self, response: str) -> Dict[str, Any]:
        """
        LLMのレスポンスからJSON部分を抽出して解析
        """
        try:
            # JSONブロックを抽出
            json_str = response.split("```json")[1].split("```")[0].strip()
            evaluation = json.loads(json_str)
            
            # 必要なフィールドが含まれているか確認
            required_fields = ["overall_score", "story_score", "writing_score", "character_score", "feedback"]
            for field in required_fields:
                if field not in evaluation:
                    raise ValueError(f"Missing required field: {field}")
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            logger.debug(f"Raw response: {response}")
            
            # エラー時はデフォルト値を返す
            return {
                "overall_score": 0.0,
                "story_score": 0.0,
                "writing_score": 0.0,
                "character_score": 0.0,
                "feedback": f"評価結果の解析に失敗しました: {str(e)}"
            }
