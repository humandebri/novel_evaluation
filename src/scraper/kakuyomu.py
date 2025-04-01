import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
import re
from datetime import datetime
import html
import logging
from src.config import settings

logger = logging.getLogger(__name__)

# 青空文庫形式のタグ（整形用）
AO_RBI = '｜'            # ルビのかかり始め
AO_RBL = '《'            # ルビ始め
AO_RBR = '》'            # ルビ終わり
AO_PB2 = '［＃改ページ］'  # ページ送り
AO_EMB = '［＃丸傍点］'    # 傍点開始
AO_EME = '［＃丸傍点終わり］' # 傍点終わり
AO_PIB = '［＃リンクの図（'  # 画像埋め込み
AO_PIE = '）入る］'        # 画像埋め込み終わり

class KakuyomuScraper:
    def __init__(self):
        self.base_url = settings.kakuyomu_base_url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_daily_ranking(self, limit: int = 10) -> List[Dict]:
        """カクヨムの日刊ランキングから小説情報を取得（上位10作品）"""
        url = f"{self.base_url}/rankings/all/daily"
        novels = []
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            # html5libパーサーを使用
            soup = BeautifulSoup(response.text, 'html5lib')
            
            # 修正したセレクタでタイトル要素を取得
            title_elements = soup.select(".widget-workCard-titleLabel.bookWalker-work-title")
            
            for i, title_element in enumerate(title_elements[:limit], 1):
                try:
                    # タイトルテキストを取得
                    title = title_element.text.strip()
                    
                    # URLを取得
                    href = title_element.get('href')
                    novel_url = f"{self.base_url}{href}"
                    
                    # 作品IDを取得
                    novel_id = href.split('/')[-1]
                    
                    # 著者名を取得（親要素から辿る）
                    work_card = title_element.find_parent('.widget-workCard')
                    author_element = work_card.select_one('.widget-workCard-authorLabel') if work_card else None
                    author = author_element.text.strip() if author_element else "不明"
                    
                    novels.append({
                        'id': novel_id,
                        'title': title,
                        'author': author,
                        'ranking_position': i,
                        'novel_url': novel_url
                    })
                except Exception as e:
                    logger.error(f"Error parsing novel at position {i}: {e}")
                    logger.error(f"Error details: {str(e)}")
                
            logger.info(f"Retrieved {len(novels)} novels from daily ranking")
                
        except Exception as e:
            logger.error(f"Error fetching daily ranking: {e}")
        
        return novels

    def get_first_episode(self, novel_id: str) -> Optional[Dict]:
        """小説の最初の1話を取得"""
        try:
            # 小説の目次ページを取得
            novel_url = f"{self.base_url}/works/{novel_id}"
            response = self.session.get(novel_url)
            response.raise_for_status()
            
            # エピソード1のURLを取得
            body = response.text
            ep_match = re.search(r'"__typename":"Episode","id":".*?","title":".*?",', body)
            
            if not ep_match:
                logger.error(f"No episode found for novel {novel_id}")
                return None
                
            # エピソード1のURLを作成
            tmp = ep_match.group(0)
            episode_id = re.sub('"__typename":"Episode","id":"', '', tmp)
            episode_id = re.sub('","title":".*?",', '', episode_id)
            episode_url = f"{novel_url}/episodes/{episode_id}"
            
            # エピソードタイトルを取得
            title_match = re.search(r'"title":"(.*?)"', tmp)
            title = title_match.group(1) if title_match else "第1話"
            
            # エピソードの内容を取得
            content = self._get_episode_content(episode_url)
            
            if content:
                logger.info(f"Retrieved first episode for novel {novel_id}")
                return {
                    'id': f"{novel_id}-{episode_id}",
                    'title': title,
                    'content': content,
                    'posted_at': datetime.now()
                }
            else:
                logger.error(f"Failed to get content for episode {episode_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching first episode for novel {novel_id}: {e}")
            return None

    def _get_episode_content(self, episode_url: str) -> Optional[str]:
        """エピソードの本文を取得"""
        try:
            response = self.session.get(episode_url)
            response.raise_for_status()
            body = response.text
            
            # 話タイトル
            sect = re.search(r'<p class="widget-episodeTitle.*?">.*?</p>', body)
            if sect:
                title = sect.group(0)
                title = re.sub('<p class="widget-episodeTitle.*?">', '', title)
                title = re.sub('</p>', '', title)
                logger.info(f"Episode title: {title}")
            
            # 本文を取得
            text = ""
            tbody = re.search(r'<p id="p.*?</p>', body)
            while tbody:
                text = text + tbody.group(0) + '\r\n'
                body = body[tbody.end(0):]
                tbody = re.search(r'<p id="p.*?</p>', body)
            
            if text:
                # 本文を整形
                text = self._format_text(text)
                return text
            else:
                logger.error(f"No content found in {episode_url}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching episode content from {episode_url}: {e}")
            return None
    
    def _format_text(self, text: str) -> str:
        """本文テキストを整形"""
        # 改行タグを改行コードに変換
        text = re.sub('<br />', '\r\n', text)
        
        # ルビタグを青空文庫形式に変換
        text = text.replace('<rp>(</rp>', '')
        text = text.replace('<rp>)</rp>', '')
        text = text.replace('<rp>（</rp>', '')
        text = text.replace('<rp>）</rp>', '')
        text = text.replace('<rb>', '')
        text = text.replace('</rb>', '')
        text = text.replace('<ruby>', AO_RBI)
        text = text.replace('<rt>', AO_RBL)
        text = text.replace('</rt></ruby>', AO_RBR)
        
        # 傍点タグを変換
        text = text.replace('<em class="emphasisDots"><span>', AO_EMB)
        text = text.replace('<span>', AO_EMB)
        text = text.replace('</span></em>', AO_EME)
        text = text.replace('</span>', AO_EME)
        
        # 画像リンクを変換
        text = text.replace('<a href="', AO_PIB)
        text = text.replace(' alt="挿絵" name="img">【挿絵表示】</a>', AO_PIE)
        
        # HTMLタグを除去
        text = re.sub('<.*?>', '', text)
        text = re.sub(' ', '', text)
        
        # HTML特殊文字を処理
        text = text.replace('&lt', '<')
        text = text.replace('&gt', '>')
        text = text.replace('&quot', '')
        text = text.replace('&nbsp', ' ')
        text = text.replace('&yen', '\\')
        text = text.replace('&brvbar', '|')
        text = text.replace('&copy', '©')
        text = text.replace('&amp', '&')
        
        # &#????にエンコードされた文字をデコードする
        en = re.search(r'&#.*?;', text)
        while en:
            ch = en.group(0)
            de = html.unescape(ch)
            text = text.replace(ch, de)
            en = re.search(r'&#.*?;', text)
        
        return text

    def process_novels_for_evaluation(self, limit: int = 10):
        """ランキング上位の小説を取得して評価用に処理（上位10作品、各1話）"""
        novels = self.get_daily_ranking(limit)
        results = []
        
        for novel in novels:
            # サーバー負荷軽減のため待機
            time.sleep(settings.scrape_interval)
            
            episode = self.get_first_episode(novel['id'])
            if episode:
                novel['episodes'] = [episode]
                results.append(novel)
        
        return results
