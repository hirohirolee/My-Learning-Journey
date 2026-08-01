import streamlit as st
st.title('app.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import os
import csv
import json
import urllib.request
import urllib.error
import sys
import re
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Scraped Movies Search & Chatbot API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Movie model
class Movie:
    def __init__(self, index, cover_formula, title_zh, title_en, score, categories, region, duration, release_date, cover_url, local_path):
        self.index = index
        self.title_zh = title_zh
        self.title_en = title_en
        self.score = score
        self.categories = categories
        self.region = region
        self.duration = duration
        self.release_date = release_date
        self.cover_url = cover_url
        self.local_path = local_path

    def to_dict(self):
        return {
            "index": self.index,
            "title_zh": self.title_zh,
            "title_en": self.title_en,
            "score": self.score,
            "categories": self.categories,
            "region": self.region,
            "duration": self.duration,
            "release_date": self.release_date,
            "cover_url": self.cover_url,
            "local_path": self.local_path
        }

# Global list of loaded movies
movies_db: List[Movie] = []

def load_movies_from_csv():
    global movies_db
    csv_path = "movies.csv"
    if not os.path.exists(csv_path):
        st.write(f"WARNING: '{csv_path}' not found on startup! Please run crawl_all.py to generate it.")
        return
        
    try:
        # Load CSV using UTF-8-BOM
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader)
            movies_db = []
            for row in reader:
                if len(row) < 11:
                    continue
                # Row format matches: Index, Poster (Excel Formula), Chinese Title, English Title, Score, Categories, Region, Duration, Release Date, Poster URL, Local Poster Path
                movie = Movie(
                    index=int(row[0]),
                    cover_formula=row[1],
                    title_zh=row[2],
                    title_en=row[3],
                    score=row[4],
                    categories=row[5],
                    region=row[6],
                    duration=row[7],
                    release_date=row[8],
                    cover_url=row[9],
                    local_path=row[10]
                )
                movies_db.append(movie)
        st.write(f"Successfully loaded {len(movies_db)} movies from CSV.")
    except Exception as e:
        st.write(f"ERROR: Failed to load movies from CSV: {e}")

@app.on_event("startup")
def startup_event():
    load_movies_from_csv()

# Request and Response schemas
class ChatRequest(BaseModel):
    message: str
    llmProvider: str = "local_search"
    apiKey: Optional[str] = None
    apiBase: Optional[str] = None
    modelName: Optional[str] = None
    lang: str = "zh"

class ChatResponse(BaseModel):
    response: str
    retrieved_movies: List[dict]

@app.get("/api/movies")
def get_movies(search: Optional[str] = None, genre: Optional[str] = None):
    results = movies_db
    if search:
        search_lower = search.lower()
        results = [
            m for m in results 
            if search_lower in m.title_zh.lower() or 
               search_lower in m.title_en.lower() or 
               search_lower in m.region.lower()
        ]
    if genre:
        genre_lower = genre.lower()
        results = [
            m for m in results 
            if genre_lower in m.categories.lower()
        ]
    return [m.to_dict() for m in results]

def retrieve_movies_context(message: str) -> List[Movie]:
    """Simple RAG search: retrieves top 8 most matching movies based on user query keywords."""
    message_lower = message.lower()
    
    # Simple keyword extraction
    keywords = re.findall(r'\w+', message_lower)
    # Stop words or short terms to ignore
    ignore = {"a", "the", "in", "on", "of", "and", "movie", "movies", "show", "film", "tell", "me", "about", "find", "search", "recommend", "is", "are", "highest", "best", "lowest", "score"}
    keywords = [k for k in keywords if k not in ignore and len(k) > 1]
    
    # Also look for explicit Chinese genres
    genres = ["剧情", "爱情", "动作", "犯罪", "喜剧", "科幻", "战争", "动画", "歌舞", "冒险", "灾难", "悬疑", "惊悚", "恐怖", "古装", "历史"]
    found_genres = [g for g in genres if g in message_lower]
    
    scored_movies = []
    
    # Check for queries about "highest score" or "best"
    is_best_query = any(w in message_lower for w in ["best", "highest", "top", "score", "评分最高", "最火", "好看", "最好"])
    
    for m in movies_db:
        score = 0
        
        # Match keywords in text
        text_to_search = f"{m.title_zh} {m.title_en} {m.categories} {m.region} {m.release_date}".lower()
        for kw in keywords:
            if kw in text_to_search:
                score += 2
                
        # Genre matches
        for g in found_genres:
            if g in m.categories:
                score += 3
                
        # Score priority if asking for best/highest
        if is_best_query:
            try:
                # Add rating score weight
                val = float(m.score)
                score += (val - 8.0) * 2  # Higher rated movies get extra weight
            except ValueError:
                pass
                
        if score > 0 or is_best_query:
            scored_movies.append((score, m))
            
    # Sort by score descending
    scored_movies.sort(key=lambda x: x[0], reverse=True)
    
    # Return top 8 matches (or top 8 sorted by score if it's a general query)
    retrieved = [item[1] for item in scored_movies[:8]]
    if not retrieved and is_best_query:
        # Fallback: just return top 8 highest rated movies
        sorted_db = sorted(movies_db, key=lambda m: float(m.score) if m.score else 0, reverse=True)
        retrieved = sorted_db[:8]
    return retrieved

def make_post_request(url: str, payload: dict, headers: dict) -> str:
    req_data = json.dumps(payload).encode("utf-8")
    api_req = urllib.request.Request(
        url,
        data=req_data,
        headers=headers,
        method="POST"
    )
    with urllib.request.urlopen(api_req, timeout=20) as response:
        return response.read().decode("utf-8")

def generate_local_response(message: str, movies: List[Movie], lang: str = "zh") -> str:
    """Generates a conversational response based on matched movies without external API."""
    if lang == "zh":
        if not movies:
            return (
                "我在資料庫中找不到符合您搜尋關鍵字的電影。推薦您嘗試搜尋「劇情」、「愛情」、「動作」，或者特定的電影名稱如「霸王別姬」或「這個殺手不太冷」。"
            )
        
        response = "我在我們的資料庫中為您找到了以下符合要求的精彩電影：\n\n"
        for m in movies[:5]:
            response += (
                f"- **{m.title_zh}** ({m.title_en}) - ⭐ **{m.score}**\n"
                f"  *類型:* {m.categories} | *地區:* {m.region} | *片長:* {m.duration}\n"
            )
            if m.release_date:
                response += f"  *上映時間:* {m.release_date}\n"
            response += "\n"
            
        if len(movies) > 5:
            response += f"還有 {len(movies) - 5} 部符合的電影已經顯示在搜尋面板中了！"
        return response
    else:
        if not movies:
            return (
                "I couldn't find any movies in my database matching your search keywords. "
                "Please try searching for terms like 'Romance', 'Comedy', 'Action', or specific titles like 'Farewell My Concubine' or 'Léon'."
            )
            
        response = "I found some great movies matching your request in our database:\n\n"
        for m in movies[:5]:
            response += (
                f"- **{m.title_zh}** ({m.title_en}) - ⭐ **{m.score}**\n"
                f"  *Genre:* {m.categories} | *Region:* {m.region} | *Duration:* {m.duration}\n"
            )
            if m.release_date:
                response += f"  *Release:* {m.release_date}\n"
            response += "\n"
            
        if len(movies) > 5:
            response += f"And {len(movies) - 5} more matching movies are visible in the search panel!"
        return response

@app.post("/api/chat", response_model=ChatResponse)
def chat_bot(req: ChatRequest):
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Retrieve relevant movies
    matched_movies = retrieve_movies_context(message)
    
    # Construct context context string
    context_str = ""
    if matched_movies:
        context_str = "Relevant Movie Dataset Context:\n"
        for m in matched_movies:
            context_str += (
                f"- Index: {m.index}, Title: {m.title_zh} ({m.title_en}), "
                f"Score: {m.score}, Categories: {m.categories}, "
                f"Region: {m.region}, Duration: {m.duration}, "
                f"Release: {m.release_date if m.release_date else 'Unknown'}\n"
            )
            
    # System instructions
    system_prompt = (
        "You are an assistant for CineBot Scraped Movie website. You help users find and recommend movies from a database of 100 movies. "
        "Here are your rules:\n"
        "1. Prioritize answering using the provided movie database context. "
        "2. If you find matching movies, list them clearly, mentioning their scores, categories, and duration if helpful. "
        "3. Keep your answers friendly, engaging, and professional.\n"
    )
    
    if req.lang == "zh":
        system_prompt += (
            "4. IMPORTANT: You MUST respond in Traditional Chinese (繁體中文) ONLY. Do NOT use Simplified Chinese. "
            "Translate any terminology to standard Taiwanese/Hong Kong expressions (e.g. use '電影', '劇情', '動作片', '地區', '上映日期').\n"
        )
    else:
        system_prompt += (
            "4. IMPORTANT: You MUST respond in English ONLY. If the movie titles in the database are in Chinese, "
            "you can mention their English titles or include both.\n"
        )
        
    system_prompt += (
        "5. If the user asks general questions unrelated to movies, you can answer them normally.\n"
        "6. If you do not find relevant movies in the database context, let the user know you don't have them in your curated database, but give a general answer based on your knowledge.\n\n"
        f"{context_str}\n"
        f"User Question: {message}\n"
        "Answer:"
    )

    retrieved_dicts = [m.to_dict() for m in matched_movies]
    provider = req.llmProvider.lower() if req.llmProvider else "local_search"

    if provider == "gemini":
        api_key = req.apiKey
        if not api_key:
            err_note = "*(注意：未提供 Gemini API 金鑰，已自動切換至本地搜尋)*\n\n" if req.lang == "zh" else "*(Note: Gemini API Key not provided, falling back to local search)*\n\n"
            local_answer = generate_local_response(message, matched_movies, req.lang)
            return ChatResponse(response=f"{err_note}{local_answer}", retrieved_movies=retrieved_dicts)
            
        model = req.modelName if req.modelName else "gemini-1.5-flash"
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": system_prompt}]
            }]
        }
        try:
            res_body = make_post_request(gemini_url, payload, {"Content-Type": "application/json"})
            res_json = json.loads(res_body)
            answer = res_json["candidates"][0]["content"]["parts"][0]["text"]
            return ChatResponse(response=answer, retrieved_movies=retrieved_dicts)
        except Exception as e:
            st.write(f"Gemini API Error: {e}", file=sys.stderr)
            err_note = "*(注意：Gemini API 連線失敗或出錯，已自動切換至本地搜尋)*\n\n" if req.lang == "zh" else "*(Note: Gemini API connection failed, falling back to local search)*\n\n"
            local_answer = generate_local_response(message, matched_movies, req.lang)
            return ChatResponse(response=f"{err_note}{local_answer}", retrieved_movies=retrieved_dicts)

    elif provider == "ollama":
        base_url = req.apiBase.strip() if req.apiBase else "http://localhost:11434"
        if not base_url.endswith("/api/chat") and not base_url.endswith("/api/chat/"):
            base_url = base_url.rstrip("/") + "/api/chat"
            
        model = req.modelName if req.modelName else "llama3"
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": system_prompt}
            ],
            "stream": False
        }
        try:
            res_body = make_post_request(base_url, payload, {"Content-Type": "application/json"})
            res_json = json.loads(res_body)
            answer = res_json["message"]["content"]
            return ChatResponse(response=answer, retrieved_movies=retrieved_dicts)
        except Exception as e:
            st.write(f"Ollama API Error: {e}", file=sys.stderr)
            err_note = "*(注意：本地 Ollama 連線失敗，請確認 Ollama 正在運行。已自動切換至本地搜尋)*\n\n" if req.lang == "zh" else "*(Note: Local Ollama connection failed. Please ensure Ollama is running. Falling back to local search)*\n\n"
            local_answer = generate_local_response(message, matched_movies, req.lang)
            return ChatResponse(response=f"{err_note}{local_answer}", retrieved_movies=retrieved_dicts)

    elif provider == "openai_compatible":
        base_url = req.apiBase.strip() if req.apiBase else "http://localhost:12345/v1"
        if not base_url.endswith("/chat/completions") and not base_url.endswith("/chat/completions/"):
            base_url = base_url.rstrip("/") + "/chat/completions"
            
        model = req.modelName if req.modelName else "meta-llama-3-8b-instruct"
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": system_prompt}
            ],
            "stream": False
        }
        headers = {"Content-Type": "application/json"}
        if req.apiKey:
            headers["Authorization"] = f"Bearer {req.apiKey}"
            
        try:
            res_body = make_post_request(base_url, payload, headers)
            res_json = json.loads(res_body)
            answer = res_json["choices"][0]["message"]["content"]
            return ChatResponse(response=answer, retrieved_movies=retrieved_dicts)
        except Exception as e:
            st.write(f"OpenAI-Compatible API Error: {e}", file=sys.stderr)
            err_note = "*(注意：本地/遠端 OpenAI 相容 API 連線失敗，已自動切換至本地搜尋)*\n\n" if req.lang == "zh" else "*(Note: OpenAI-Compatible API connection failed, falling back to local search)*\n\n"
            local_answer = generate_local_response(message, matched_movies, req.lang)
            return ChatResponse(response=f"{err_note}{local_answer}", retrieved_movies=retrieved_dicts)

    else:
        # Local offline search
        local_answer = generate_local_response(message, matched_movies, req.lang)
        return ChatResponse(response=local_answer, retrieved_movies=retrieved_dicts)

# Helper to find file paths


# Serve posters folder static assets
posters_path = os.path.abspath("posters")
if os.path.exists(posters_path):
    app.mount("/posters", StaticFiles(directory=posters_path), name="posters")

# Serve UI HTML folder static assets
static_path = os.path.abspath("static")
os.makedirs(static_path, exist_ok=True)

# Mount the static files for frontend. We will mount it last.
app.mount("/", StaticFiles(directory=static_path, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
