from typing import List, Dict, Any

class PromptManager:
    """
    評価用プロンプトの管理クラス
    """
    
    @staticmethod
    def get_evaluation_prompt(title: str, author: str, episodes: List[Dict[str, Any]]) -> str:
        """
        小説評価用のプロンプトを生成
        
        Args:
            title: 小説のタイトル
            author: 作者名
            episodes: エピソードのリスト（最大3つ）
            
        Returns:
            評価用プロンプト
        """
        # エピソードテキストの準備
        episode_texts = []
        for ep in episodes[:3]:  # 最大3つまで
            episode_texts.append(f"## エピソード: {ep['title']}\n\n{ep['content']}")
        
        # エピソードが3つない場合の対応
        while len(episode_texts) < 3:
            episode_texts.append("(このエピソードは利用できません)")
        
        prompt = f"""# 小説評価タスク

あなたはプロの文学評論家です。以下の小説を評価してください。

## 基本情報
- タイトル: {title}
- 作者: {author}

## 評価指示
以下の3つのエピソードを読んで、小説の質を10点満点で評価してください。
評価は絶対的な基準で行い、相対評価ではなく絶対評価としてください。

{'-' * 80}

{episode_texts[0]}

{'-' * 80}

{episode_texts[1]}

{'-' * 80}

{episode_texts[2]}

{'-' * 80}

## 評価基準
以下の観点から評価し、各項目のスコアと理由を詳しく説明してください：

1. ストーリー性 (10点満点): 物語の展開、構成、オリジナリティ
2. 文章力 (10点満点): 表現力、読みやすさ、言葉の選択
3. キャラクター (10点満点): 登場人物の魅力、深み、成長
4. 総合評価 (10点満点): 全体的な作品の質

## 回答形式
必ず以下のJSON形式で回答してください：
```json
{{
  "story_score": 数値,
  "writing_score": 数値,
  "character_score": 数値,
  "overall_score": 数値,
  "feedback": "詳細な評価コメント"
}}
```

評価は厳格かつ公平に行い、プロの文学評論家として真摯な評価を提供してください。
"""
        return prompt
