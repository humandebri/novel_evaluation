import requests
import time
import random
import logging
from typing import Optional
from src.config import settings

logger = logging.getLogger(__name__)

def fetch_with_retry(url: str, max_retries: int = None) -> Optional[requests.Response]:
    """
    指定されたURLからデータを取得し、失敗した場合はリトライする
    """
    if max_retries is None:
        max_retries = settings.max_retries
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                # 指数バックオフでリトライ間隔を増やす
                wait_time = (2 ** attempt) + random.random()
                logger.info(f"Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                raise
    
    return None

def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
    """
    サーバー負荷軽減のためのランダム待機
    """
    delay = min_seconds + random.random() * (max_seconds - min_seconds)
    time.sleep(delay)
