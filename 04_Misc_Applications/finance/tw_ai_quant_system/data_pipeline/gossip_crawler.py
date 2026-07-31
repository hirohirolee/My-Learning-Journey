import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict
import datetime
import logging

logger = logging.getLogger(__name__)

class GossipCrawler:
    """
    爬取真實市場八卦 (Google News RSS)
    """
    def fetch_news(self, keyword: str, days: int = 15) -> List[Dict]:
        """
        根據關鍵字抓取過去幾天的新聞標題做為八卦來源
        """
        encoded_kw = urllib.parse.quote(keyword)
        url = f"https://news.google.com/rss/search?q={encoded_kw}+when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        news_list = []
        
        try:
            logger.info(f"開始爬取 {keyword} 的真實市場新聞 (來源: Google News RSS)...")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                
                for item in root.findall('.//item')[:20]: # 取最近20篇
                    title = item.find('title').text
                    pubDate = item.find('pubDate').text
                    # 轉換 pubDate (例如: Tue, 24 Oct 2023 08:00:00 GMT)
                    dt = datetime.datetime.strptime(pubDate, "%a, %d %b %Y %H:%M:%S %Z")
                    
                    news_list.append({
                        'date': dt.strftime('%Y-%m-%d'),
                        'content': title
                    })
            logger.info(f"成功爬取 {len(news_list)} 篇關於 {keyword} 的新聞。")
        except Exception as e:
            logger.error(f"爬取新聞失敗: {e}")
            
        return news_list

if __name__ == "__main__":
    crawler = GossipCrawler()
    news = crawler.fetch_news("廣達")
    for n in news[:3]:
        print(n)
