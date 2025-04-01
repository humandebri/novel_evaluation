import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def scrape_kakuyomu_rankings(url="https://kakuyomu.jp/rankings/all/daily"):
    """
    KakuyomuのランキングページからタイトルとURLを取得する
    
    Parameters:
    url (str): スクレイピング対象のURL。デフォルトは日間総合ランキング
    
    Returns:
    pd.DataFrame: タイトルとURLを含むDataFrame
    """
    # リクエストヘッダー（ブラウザとして認識されるため）
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # ページの取得
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # エラーがあれば例外を発生
        
        # BeautifulSoupでHTMLを解析
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 結果を格納するリスト
        titles = []
        urls = []
        ranks = []
        
        # 修正したセレクタで要素を取得
        title_elements = soup.select(".widget-workCard-titleLabel.bookWalker-work-title")
        
        for i, title_element in enumerate(title_elements, 1):
            if title_element:
                # タイトルテキストを取得
                title = title_element.get_text(strip=True)
                
                # URLを取得し、相対パスの場合は絶対URLに変換
                href = title_element.get('href')
                full_url = f"https://kakuyomu.jp{href}" if href.startswith('/') else href
                
                # リストに追加
                ranks.append(i)
                titles.append(title)
                urls.append(full_url)
        
        # DataFrameに変換
        df = pd.DataFrame({
            'ランク': ranks,
            'タイトル': titles,
            'URL': urls
        })
        
        return df
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return None

def simple_scrape_kakuyomu(url="https://kakuyomu.jp/rankings/all/daily"):
    """
    シンプルな方法でKakuyomuのランキングページからタイトルとURLを取得し、直接表示する
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 修正したセレクタでタイトル要素を取得
    titles = soup.select(".widget-workCard-titleLabel.bookWalker-work-title")
    
    for title in titles:
        print(title.text.strip(), "-", "https://kakuyomu.jp" + title["href"])

if __name__ == "__main__":
    print("方法1: DataFrameとして取得")
    # ランキングを取得
    results = scrape_kakuyomu_rankings()
    
    if results is not None:
        # 結果を表示
        print(f"合計 {len(results)} 作品を取得しました")
        print(results)
        
        # CSVとして保存（オプション）
        results.to_csv('kakuyomu_rankings.csv', index=False, encoding='utf-8-sig')
        print("結果をkakuyomu_rankings.csvに保存しました")
    
    print("\n方法2: シンプルな表示")
    simple_scrape_kakuyomu()