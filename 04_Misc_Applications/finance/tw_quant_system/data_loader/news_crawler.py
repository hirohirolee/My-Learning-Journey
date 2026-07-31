import datetime
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
from utils.anti_crawler import AntiCrawlerSession
from utils.logger import get_logger
from config import YAHOO_NEWS_URL

logger = get_logger(__name__)

class NewsCrawler:
    """
    2.4 新聞兩層式爬蟲：
    第一層：抓取新聞列表與網址。
    第二層：進入個別新聞頁面抓取內文與精確日期。
    """
    def __init__(self) -> None:
        self.http = AntiCrawlerSession()

    def fetch_news_list(self, limit: int = 5) -> List[Dict[str, str]]:
        """
        第一層：抓取 Yahoo 財經新聞列表。
        
        :param limit: 最大爬取新聞條數
        :return: 包含新聞標題與 URL 的字典列表
        """
        try:
            logger.info("開始爬取新聞列表...")
            response = self.http.get(YAHOO_NEWS_URL)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_links = []
            # 尋找所有 <a> 標籤並過濾出新聞連結
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                # 確認是否為有效的新聞連結格式
                if 'news/' in href and href.endswith('.html'):
                    title = a_tag.text.strip()
                    # 避免重複標題與空標題
                    if title and href not in [link['url'] for link in news_links]:
                        news_links.append({'title': title, 'url': href})
                        if len(news_links) >= limit:
                            break
                            
            logger.info(f"第一層爬取完畢，成功獲取 {len(news_links)} 筆新聞連結")
            return news_links
            
        except Exception as e:
            logger.error(f"爬取新聞列表失敗: {str(e)}")
            return []
        finally:
            logger.debug("第一層新聞列表爬取程序結束")

    def fetch_news_content(self, url: str) -> Optional[Dict[str, str]]:
        """
        第二層：根據 URL 抓取單篇新聞內文與發布日期。
        
        :param url: 新聞內文頁面網址
        :return: 包含日期與內文的字典，若失敗則為 None
        """
        try:
            logger.info(f"開始爬取新聞內文: {url}")
            response = self.http.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 定位時間標籤
            time_tag = soup.find('time')
            date_str = time_tag['datetime'] if time_tag and time_tag.has_attr('datetime') else str(datetime.datetime.now())
            
            # 定位並組合所有段落內文
            paragraphs = soup.find_all('p')
            content = "\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
            
            return {
                'date': date_str,
                'content': content
            }
            
        except Exception as e:
            logger.error(f"爬取新聞內文失敗 ({url}): {str(e)}")
            return None

    def get_latest_news(self, limit: int = 3) -> List[Dict[str, Any]]:
        """
        組合第一與第二層，完整獲取新聞資訊。
        善用 zip() 與 range() 來進行迭代處理與日誌記錄。
        
        :param limit: 欲獲取的新聞總數
        :return: 包含完整標題、網址、日期與內文的新聞列表
        """
        news_list = self.fetch_news_list(limit=limit)
        results = []
        
        # 使用 zip 與 range 來同時追蹤索引與物件，符合教學要求
        for i, news_item in zip(range(len(news_list)), news_list):
            logger.info(f"正在處理第 {i+1}/{len(news_list)} 則新聞: {news_item['title']}")
            details = self.fetch_news_content(news_item['url'])
            
            if details:
                news_item.update(details)
                results.append(news_item)
                
        logger.info(f"成功完成兩層式爬蟲，共獲取 {len(results)} 則完整新聞資料")
        return results

if __name__ == "__main__":
    crawler = NewsCrawler()
    news = crawler.get_latest_news(limit=2)
    for n in news:
        print(f"Title: {n['title']}\nDate: {n['date']}\nContent Preview: {n['content'][:50]}...\n")
