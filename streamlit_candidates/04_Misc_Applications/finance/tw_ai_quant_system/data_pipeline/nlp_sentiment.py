import streamlit as st

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from typing import List, Dict
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
from config import OPENAI_API_KEY, LLM_MODEL, USE_OLLAMA, OLLAMA_BASE_URL, OLLAMA_MODEL
from utils.logger import get_logger

logger = get_logger(__name__)

class NLPSentimentAnalyzer:
    """
    鞈?蝞∠?嚗???LLM (憒?OpenAI GPT) ?脰??啗????? (NLP)??    撠?蝯????鞈?頧???-1 (璆萄漲?脰?/?拍征) ??1 (璆萄漲璅?/?拙?) ????蝺??詻?    """
    def __init__(self):
        if OpenAI is None:
            self.client = None
            self.model_name = "RuleBasedFallback"
            logger.warning("OpenAI 模組未安裝，啟用規則情緒分析備援模式。")
        elif USE_OLLAMA:
            # 使用 Ollama 的 OpenAI 相容 API 介面
            self.client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
            self.model_name = OLLAMA_MODEL
            logger.info(f"啟動 NLPSentimentAnalyzer，使用本機 Ollama 模型: {self.model_name}")
        else:
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            self.model_name = LLM_MODEL
            logger.info(f"啟動 NLPSentimentAnalyzer，使用 OpenAI 模型: {self.model_name}")
        
    def analyze_text(self, text: str) -> float:
        """
        ?澆 LLM ???格挾???嚗??瘚桅??詨??詻?        
        :param text: ?啗?璅????        :return: ??? (-1.0 ~ 1.0)
        """
        prompt = f"""
        雿銝雿?璆剔??啗????撣怒???隞乩????啗??嚗蒂蝯血?????        ?蝭?敺?-1.0 (璆萄漲?脰?/?拍征) ??1.0 (璆萄漲璅?/?拙?)?葉蝡 0.0??        ?芷??銝?筑暺嚗?閬??思遙雿隞?摮?        
        ?啗??批捆:
        {text}
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a quantitative financial sentiment analyzer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            score_str = response.choices[0].message.content.strip()
            return float(score_str)
        except ValueError:
            logger.error(f"LLM ?鈭瘜圾??詨??摰? {score_str}")
            return 0.0
        except Exception as e:
            logger.error(f"LLM ????隢?憭望?: {str(e)}")
            return 0.0

    def process_news_list(self, news_list: List[Dict]) -> pd.DataFrame:
        """
        ?寞活???啗?皜嚗?蝞???????嚗蒂???蝯像??        
        :param news_list: ? 'date' ??'content' ???詨?銵?(靘???挾???
        :return: ? 'Date' ??'Sentiment_Score' ??DataFrame嚗?湔???DataFrame ?脰? Merge
        """
        logger.info(f"???脰? NLP ?寞活???? (??{len(news_list)} 蝑?")
        results = []
        
        for i, news in enumerate(news_list):
            # ?? 1000 摮誑?踹?頞? token ?銝???API ?
            content_snippet = news.get('content', '')[:1000] 
            if not content_snippet:
                continue
                
            score = self.analyze_text(content_snippet)
            results.append({
                'Date': pd.to_datetime(news['date']).date(),
                'Sentiment_Score': score
            })
            logger.debug(f"撌脰???{i+1}/{len(news_list)} 蝑? ???: {score}")
            
        df = pd.DataFrame(results)
        if not df.empty:
            # 敶蜇??憭拍??啗????撟喳???(?亦憭拇?憭??啗?)
            daily_df = df.groupby('Date')['Sentiment_Score'].mean().reset_index()
            daily_df['Date'] = pd.to_datetime(daily_df['Date'])
            logger.info("NLP ??????摰?")
            return daily_df
            
        return pd.DataFrame()

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    analyzer = NLPSentimentAnalyzer()
    
    sample_news = [
        {"date": "2023-10-25", "content": "Sample positive news"},
        {"date": "2023-10-26", "content": "Sample negative news"}
    ]
    
    st.write("Testing NLP Sentiment Analyzer...")
    df = analyzer.process_news_list(sample_news)
    st.write("\nResulting DataFrame:")
    st.write(df)
    import logging
    logging.basicConfig(level=logging.INFO)
    
    analyzer = NLPSentimentAnalyzer()
    
    sample_news = [
        {"date": "2023-10-25", "content": "Sample positive news"},
        {"date": "2023-10-26", "content": "Sample negative news"}
    ]
    
    st.write("Testing NLP Sentiment Analyzer...")
    df = analyzer.process_news_list(sample_news)
    st.write("\nResulting DataFrame:")
    st.write(df)
    import logging
    logging.basicConfig(level=logging.INFO)
    
    analyzer = NLPSentimentAnalyzer()
    
    sample_news = [
        {"date": "2023-10-25", "content": "Sample positive news"},
        {"date": "2023-10-26", "content": "Sample negative news"}
    ]
    
    st.write("Testing NLP Sentiment Analyzer...")
    df = analyzer.process_news_list(sample_news)
    st.write("\nResulting DataFrame:")
    st.write(df)
