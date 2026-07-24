import os
import csv
import json
import urllib.request
import sys
import re
import base64
import streamlit as st

# Configuration persistence file
CONFIG_FILE = "streamlit_config.json"

def load_config():
    default_config = {
        "lang": "zh",
        "llm_provider": "local_search",
        "gemini_api_key": "",
        "llm_api_base": "",
        "llm_model_name": ""
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    default_config.update(loaded)
        except:
            pass
            
    # Try loading from environment variables or Streamlit secrets for deployment convenience
    if not default_config["gemini_api_key"]:
        if "GEMINI_API_KEY" in os.environ:
            default_config["gemini_api_key"] = os.environ["GEMINI_API_KEY"]
            default_config["llm_provider"] = "gemini"
        else:
            try:
                if "GEMINI_API_KEY" in st.secrets:
                    default_config["gemini_api_key"] = st.secrets["GEMINI_API_KEY"]
                    default_config["llm_provider"] = "gemini"
            except:
                pass
                
    return default_config

def save_config(config):
    # Do not save to shared disk on Streamlit Cloud to avoid cross-user state leakage
    is_cloud = (
        "STREAMLIT_SHARING_MODE" in os.environ 
        or "STREAMLIT_IS_RUNNING_IN_CLOUD" in os.environ
    )
    if is_cloud:
        return
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except:
        pass

def get_ollama_models(api_base="http://localhost:11434"):
    try:
        url = api_base.strip()
        if not url.endswith("/api/tags") and not url.endswith("/api/tags/"):
            url = url.rstrip("/") + "/api/tags"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
            models = [m["name"] for m in data.get("models", []) if "embed" not in m["name"].lower()]
            return models
    except:
        pass
    return []

# 1. Load configuration
if "config" not in st.session_state:
    st.session_state.config = load_config()
config = st.session_state.config

if "expander_expanded" not in st.session_state:
    st.session_state.expander_expanded = False


# 2. Localized Text Maps
t_zh = {
    "page_title": "CineBot - 電影搜尋與 AI 助理",
    "search_placeholder": "搜尋電影名稱、上映地區或關鍵字...",
    "all_genres": "所有類型",
    "tab_gallery": "電影大廳 (Gallery)",
    "tab_chat": "CineBot 助理 (Chat)",
    "showing_movies": "顯示 {} 部電影（共 {} 部）",
    "no_results": "沒有符合搜尋條件的電影。",
    "genres_label": "類型：",
    "region_label": "地區：",
    "duration_label": "片長：",
    "release_label": "上映時間：",
    "ask_template": "請幫我介紹一下電影《{}》",
    "welcome_msg": "歡迎來到 CineBot！您可以詢問關於前 100 部熱門電影的任何問題（例如評分、片長、上映日期或類型）。",
    "intro_msg": "您好！我是 CineBot。我可以協助您在爬取的電影清單中進行搜尋、篩選和推薦。\n\n提示：在側邊欄可設定 Gemini API 金鑰或本地 LLM，以獲得更強大的 AI 對話回覆。否則，我將使用本地關鍵字搜尋引擎。",
    "input_placeholder": "詢問關於電影的問題...",
    "err_sending": "抱歉，傳送訊息時遇到問題。請檢查連線。",
    "err_no_key": "*(注意：未提供 Gemini API 金鑰，已自動切換至本地搜尋)*\n\n",
    "err_conn_failed": "*(注意：LLM 連線失敗，請確保本地/遠端伺服器運行正常。已自動切換至本地搜尋)*\n\n",
    "offline_search": "本地離線搜尋",
    "save_success": "設定已成功儲存並同步！",
    "clear_success": "已清除設定，回到本地離線搜尋模式。"
}

t_en = {
    "page_title": "CineBot - Scraped Movie Search & AI Assistant",
    "search_placeholder": "Search by title, region or keywords...",
    "all_genres": "All Genres",
    "tab_gallery": "Movie Gallery",
    "tab_chat": "AI Assistant",
    "showing_movies": "Showing {} of {} movies",
    "no_results": "No movies match your search criteria.",
    "genres_label": "Genres:",
    "region_label": "Region:",
    "duration_label": "Duration:",
    "release_label": "Release:",
    "ask_template": 'Tell me about the movie "{}"',
    "welcome_msg": "Welcome to CineBot! Ask me anything about the top 100 movies in our database (e.g. ratings, durations, release dates, or genres).",
    "intro_msg": "Hello! I'm CineBot. I can help you search, filter, and recommend movies from our scraped list.\n\nTip: In the sidebar, configure your Gemini API Key or a Local LLM for smart conversational answers. Otherwise, I will use a local keyword search engine.",
    "input_placeholder": "Ask about movies...",
    "err_sending": "Sorry, I encountered an issue sending your message. Please check connection.",
    "err_no_key": "*(Note: Gemini API Key not provided, falling back to local search)*\n\n",
    "err_conn_failed": "*(Note: LLM connection failed, falling back to local search)*\n\n",
    "offline_search": "Offline Search",
    "save_success": "Settings successfully saved and synced!",
    "clear_success": "Settings cleared. Switched back to offline search."
}

# 3. Streamlit Page Config
st.set_page_config(
    page_title="CineBot - Movie AI Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Style Rules for Dark Theme Glassmorphism
st.markdown("""
<style>
    .stApp {
        background-color: #0b0f19;
        background-image: 
            radial-gradient(at 10% 20%, rgba(99, 102, 241, 0.08) 0px, transparent 50%),
            radial-gradient(at 90% 80%, rgba(34, 211, 238, 0.06) 0px, transparent 50%);
        background-attachment: fixed;
        color: #f3f4f6;
    }
    header, [data-testid="stHeader"] {
        background: transparent !important;
    }
    
    /* Floating Expander Style for Chatbot */
    div[data-testid="stExpander"] {
        position: fixed !important;
        bottom: 25px !important;
        right: 25px !important;
        width: 400px !important;
        z-index: 999999 !important;
        background: rgba(15, 23, 42, 0.95) !important;
        border: 1px solid rgba(99, 102, 241, 0.4) !important;
        border-radius: 16px !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.6) !important;
        backdrop-filter: blur(15px) !important;
        -webkit-backdrop-filter: blur(15px) !important;
    }
    
    div[data-testid="stExpander"] summary {
        background: rgba(30, 41, 59, 0.8) !important;
        color: #22d3ee !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        border-radius: 15px !important;
    }
    
    div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        max-height: 450px !important;
        overflow-y: auto !important;
        background: transparent !important;
        padding: 10px !important;
    }
</style>
""", unsafe_allow_html=True)


# 4. Sidebar Panel for Controls
st.sidebar.markdown("<h2 style='text-align: center; color: #22d3ee;'>🎬 Cine<span>Bot</span> Settings</h2>", unsafe_allow_html=True)

# Language Select
lang_option = st.sidebar.selectbox(
    "語言 / Language",
    options=["繁體中文 (Traditional Chinese)", "English"],
    index=0 if config["lang"] == "zh" else 1
)
lang = "zh" if "繁體中文" in lang_option else "en"
t = t_zh if lang == "zh" else t_en

# LLM Provider Select
provider_map = {
    "本地離線搜尋 (Offline Search)": "local_search",
    "Gemini API": "gemini",
    "Local LLM (Ollama)": "ollama",
    "Local LLM (OpenAI Compatible)": "openai_compatible"
}
provider_options = list(provider_map.keys())
saved_provider_key = [k for k, v in provider_map.items() if v == config["llm_provider"]]
saved_index = provider_options.index(saved_provider_key[0]) if saved_provider_key else 0

llm_provider_display = st.sidebar.selectbox(
    "LLM 供應商 / LLM Provider",
    options=provider_options,
    index=saved_index
)
llm_provider = provider_map[llm_provider_display]

# Dynamic configuration forms based on provider
api_key = config["gemini_api_key"]
api_base = config["llm_api_base"]
model_name = config["llm_model_name"]

if llm_provider == "gemini":
    api_key = st.sidebar.text_input("Gemini API Key", value=config["gemini_api_key"], type="password", placeholder="AIzaSy...")
    model_name = st.sidebar.text_input("Model Name", value=config["llm_model_name"] or "gemini-1.5-flash", placeholder="gemini-1.5-flash")
elif llm_provider == "ollama":
    api_base = st.sidebar.text_input("Ollama Base URL", value=config["llm_api_base"] or "http://localhost:11434", placeholder="http://localhost:11434")
    ollama_models = get_ollama_models(api_base)
    if ollama_models:
        default_model = config["llm_model_name"] if config["llm_model_name"] in ollama_models else (ollama_models[0] if ollama_models else "llama3")
        try:
            model_index = ollama_models.index(default_model)
        except ValueError:
            model_index = 0
        model_name = st.sidebar.selectbox("Model Name", options=ollama_models, index=model_index)
    else:
        model_name = st.sidebar.text_input("Model Name", value=config["llm_model_name"] or "llama3", placeholder="llama3")
elif llm_provider == "openai_compatible":
    api_base = st.sidebar.text_input("API Base URL", value=config["llm_api_base"] or "http://localhost:12345/v1", placeholder="http://localhost:12345/v1")
    api_key = st.sidebar.text_input("API Key (Optional)", value=config["gemini_api_key"], type="password", placeholder="sk-...")
    model_name = st.sidebar.text_input("Model Name", value=config["llm_model_name"] or "meta-llama-3-8b-instruct", placeholder="meta-llama-3-8b-instruct")

col_side1, col_side2 = st.sidebar.columns(2)
with col_side1:
    if st.button("儲存 / Save", use_container_width=True):
        config["lang"] = lang
        config["llm_provider"] = llm_provider
        config["gemini_api_key"] = api_key
        config["llm_api_base"] = api_base
        config["llm_model_name"] = model_name
        save_config(config)
        st.sidebar.success(t["save_success"])
        st.rerun()

with col_side2:
    if st.button("清除 / Reset", use_container_width=True):
        config["llm_provider"] = "local_search"
        config["gemini_api_key"] = ""
        config["llm_api_base"] = ""
        config["llm_model_name"] = ""
        save_config(config)
        st.sidebar.warning(t["clear_success"])
        st.rerun()

# 5. Database loading
@st.cache_data
def load_movies_db():
    # Resolve path relative to this script file so it works on Streamlit Cloud
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "movies.csv")
    if not os.path.exists(csv_path):
        return []
    movies = []
    try:
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader)
            for row in reader:
                if len(row) < 11:
                    continue
                movies.append({
                    "index": int(row[0]),
                    "title_zh": row[2],
                    "title_en": row[3],
                    "score": row[4],
                    "categories": row[5],
                    "region": row[6],
                    "duration": row[7],
                    "release_date": row[8],
                    "cover_url": row[9],
                    "local_path": row[10]
                })
    except Exception as e:
        print(f"Error loading CSV in Streamlit: {e}")
    return movies

movies_db = load_movies_db()

# 6. Core Logic (RAG Search and LLM Callers)
def retrieve_movies_context(message: str) -> list:
    message_lower = message.lower()
    keywords = re.findall(r'\w+', message_lower)
    ignore = {"a", "the", "in", "on", "of", "and", "movie", "movies", "show", "film", "tell", "me", "about", "find", "search", "recommend", "is", "are", "highest", "best", "lowest", "score"}
    keywords = [k for k in keywords if k not in ignore and len(k) > 1]
    
    genres = ["劇情", "愛情", "動作", "犯罪", "喜劇", "科幻", "戰爭", "動畫", "歌舞", "冒險", "災難", "懸疑", "驚悚", "恐怖", "古裝", "歷史"]
    found_genres = [g for g in genres if g in message_lower]
    
    scored_movies = []
    is_best_query = any(w in message_lower for w in ["best", "highest", "top", "score", "評分最高", "最火", "好看", "最好"])
    
    for m in movies_db:
        score = 0
        text_to_search = f"{m['title_zh']} {m['title_en']} {m['categories']} {m['region']} {m['release_date']}".lower()
        for kw in keywords:
            if kw in text_to_search:
                score += 2
        for g in found_genres:
            if g in m['categories']:
                score += 3
        if is_best_query:
            try:
                val = float(m['score'])
                score += (val - 8.0) * 2
            except ValueError:
                pass
        if score > 0 or is_best_query:
            scored_movies.append((score, m))
            
    scored_movies.sort(key=lambda x: x[0], reverse=True)
    retrieved = [item[1] for item in scored_movies[:8]]
    if not retrieved and is_best_query:
        sorted_db = sorted(movies_db, key=lambda m: float(m['score']) if m['score'] else 0, reverse=True)
        retrieved = sorted_db[:8]
    return retrieved

def generate_local_response(message: str, movies: list, lang: str = "zh") -> str:
    if lang == "zh":
        if not movies:
            return "我在資料庫中找不到符合您搜尋關鍵字的電影。推薦您嘗試搜尋「劇情」、「愛情」、「動作」，或者特定的電影名稱如「霸王別姬」或「這個殺手不太冷」。"
        response = "我在我們的資料庫中為您找到了以下符合要求的精彩電影：\n\n"
        for m in movies[:5]:
            response += f"- **{m['title_zh']}** ({m['title_en']}) - ⭐ **{m['score']}**\n  *類型:* {m['categories']} | *地區:* {m['region']} | *片長:* {m['duration']}\n"
            if m['release_date']:
                response += f"  *上映時間:* {m['release_date']}\n"
            response += "\n"
        if len(movies) > 5:
            response += f"還有 {len(movies) - 5} 部符合的電影已經顯示在搜尋面板中了！"
        return response
    else:
        if not movies:
            return "I couldn't find any movies in my database matching your search keywords. Please try searching for terms like 'Romance', 'Comedy', 'Action', or specific titles like 'Farewell My Concubine' or 'Léon'."
        response = "I found some great movies matching your request in our database:\n\n"
        for m in movies[:5]:
            response += f"- **{m['title_zh']}** ({m['title_en']}) - ⭐ **{m['score']}**\n  *Genre:* {m['categories']} | *Region:* {m['region']} | *Duration:* {m['duration']}\n"
            if m['release_date']:
                response += f"  *Release:* {m['release_date']}\n"
            response += "\n"
        if len(movies) > 5:
            response += f"And {len(movies) - 5} more matching movies are visible in the search panel!"
        return response

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

def call_llm_api(provider: str, message: str, context_str: str, api_key: str, api_base: str, model_name: str, lang: str):
    system_prompt = (
        "You are an assistant for CineBot Scraped Movie website. You help users find and recommend movies from a database of 100 movies. "
        "Here are your rules:\n"
        "1. Prioritize answering using the provided movie database context. "
        "2. If you find matching movies, list them clearly, mentioning their scores, categories, and duration if helpful. "
        "3. Keep your answers friendly, engaging, and professional.\n"
    )
    if lang == "zh":
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

    if provider == "gemini":
        model = model_name if model_name else "gemini-1.5-flash"
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": system_prompt}]
            }]
        }
        res_body = make_post_request(gemini_url, payload, {"Content-Type": "application/json"})
        res_json = json.loads(res_body)
        return res_json["candidates"][0]["content"]["parts"][0]["text"]

    elif provider == "ollama":
        base_url = api_base.strip() if api_base else "http://localhost:11434"
        if not base_url.endswith("/api/chat") and not base_url.endswith("/api/chat/"):
            base_url = base_url.rstrip("/") + "/api/chat"
        model = model_name if model_name else "llama3"
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": system_prompt}
            ],
            "stream": False
        }
        res_body = make_post_request(base_url, payload, {"Content-Type": "application/json"})
        res_json = json.loads(res_body)
        return res_json["message"]["content"]

    elif provider == "openai_compatible":
        base_url = api_base.strip() if api_base else "http://localhost:12345/v1"
        if not base_url.endswith("/chat/completions") and not base_url.endswith("/chat/completions/"):
            base_url = base_url.rstrip("/") + "/chat/completions"
        model = model_name if model_name else "meta-llama-3-8b-instruct"
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": system_prompt}
            ],
            "stream": False
        }
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        res_body = make_post_request(base_url, payload, headers)
        res_json = json.loads(res_body)
        return res_json["choices"][0]["message"]["content"]

def get_movie_poster(movie):
    """Encodes local poster to base64, otherwise falls back to cover_url."""
    if movie["local_path"] and os.path.exists(movie["local_path"]):
        try:
            with open(movie["local_path"], "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
            return f"data:image/jpeg;base64,{encoded_string}"
        except:
            pass
    return movie["cover_url"]

# 7. Main Application UI Layout
st.markdown(f"<h1 style='text-align: center; font-weight: 800; color: #f3f4f6;'>Cine<span style='color: #22d3ee;'>Bot</span></h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #9ca3af; margin-bottom: 30px;'>Top 100 Scraped Movies & AI Chat Assistant</p>", unsafe_allow_html=True)

with st.container():

    # Search and Filter Form Controls
    col_search, col_genre = st.columns([2, 1])
    with col_search:
        search_query = st.text_input("搜尋關鍵字 / Search", placeholder=t["search_placeholder"], label_visibility="collapsed")
    with col_genre:
        genres_list = [
            t["all_genres"], "劇情", "愛情", "喜劇", "動作", "犯罪", "科幻", "動畫", "冒險"
        ] if lang == "zh" else [
            t["all_genres"], "Drama", "Romance", "Comedy", "Action", "Crime", "Sci-Fi", "Animation", "Adventure"
        ]
        
        # English to Traditional Chinese category mapping
        genre_display_map = {
            "All Genres": t["all_genres"],
            "Drama": "劇情",
            "Romance": "愛情",
            "Comedy": "喜劇",
            "Action": "動作",
            "Crime": "犯罪",
            "Sci-Fi": "科幻",
            "Animation": "動畫",
            "Adventure": "冒險"
        }
        
        selected_genre_display = st.selectbox("分類篩選 / Genre", options=genres_list, label_visibility="collapsed")
        
        # Normalize to database tags
        if lang == "en":
            selected_genre = genre_display_map.get(selected_genre_display, "")
        else:
            selected_genre = "" if selected_genre_display == t["all_genres"] else selected_genre_display

    # Filter movies list
    filtered_movies = movies_db
    if selected_genre:
        filtered_movies = [m for m in filtered_movies if selected_genre in m["categories"]]
    if search_query:
        sq = search_query.strip().lower()
        filtered_movies = [
            m for m in filtered_movies 
            if sq in m["title_zh"].lower() or sq in m["title_en"].lower() or sq in m["region"].lower() or sq in m["categories"].lower()
        ]

    st.markdown(f"<p style='color:#9ca3af; font-size:14px; margin-top:-10px; margin-bottom:15px;'>{t['showing_movies'].format(len(filtered_movies), len(movies_db))}</p>", unsafe_allow_html=True)

    if not filtered_movies:
        st.warning(t["no_results"])
    else:
        # Render responsive columns grid
        grid_cols = 4
        rows = (len(filtered_movies) + grid_cols - 1) // grid_cols
        
        for r in range(rows):
            cols = st.columns(grid_cols)
            for c in range(grid_cols):
                index = r * grid_cols + c
                if index < len(filtered_movies):
                    movie = filtered_movies[index]
                    poster_src = get_movie_poster(movie)
                    
                    with cols[c]:
                        card_html = f"""
                        <div style="
                            background: rgba(31, 41, 55, 0.45);
                            border: 1px solid rgba(255, 255, 255, 0.08);
                            border-radius: 16px;
                            overflow: hidden;
                            display: flex;
                            flex-direction: column;
                            position: relative;
                            backdrop-filter: blur(5px);
                            margin-bottom: 25px;
                            height: 380px;
                        ">
                          <span style="
                              position: absolute;
                              top: 10px;
                              left: 10px;
                              background: rgba(11, 15, 25, 0.85);
                              border: 1px solid rgba(255, 255, 255, 0.08);
                              color: #f3f4f6;
                              padding: 3px 7px;
                              border-radius: 6px;
                              font-size: 10px;
                              font-weight: 600;
                              z-index: 2;
                          ">#{movie['index']}</span>
                          <span style="
                              position: absolute;
                              top: 10px;
                              right: 10px;
                              background: rgba(11, 15, 25, 0.85);
                              border: 1px solid rgba(251, 191, 36, 0.3);
                              color: #fbbf24;
                              padding: 3px 7px;
                              border-radius: 6px;
                              font-size: 11px;
                              font-weight: 700;
                              display: flex;
                              align-items: center;
                              gap: 3px;
                              z-index: 2;
                          ">⭐ {movie['score']}</span>
                          <div style="height: 230px; background: #181d28; overflow: hidden; display: flex; align-items: center; justify-content: center;">
                            <img src="{poster_src}" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.src='{movie['cover_url']}';" />
                          </div>
                          <div style="padding: 12px; display: flex; flex-direction: column; flex: 1; gap: 4px;">
                            <h3 style="margin: 0; font-size: 14px; font-weight: 600; color: #f3f4f6; text-overflow: ellipsis; white-space: nowrap; overflow: hidden;" title="{movie['title_zh']}">{movie['title_zh']}</h3>
                            <h4 style="margin: 0; font-size: 11px; font-weight: 400; color: #9ca3af; text-overflow: ellipsis; white-space: nowrap; overflow: hidden;" title="{movie['title_en']}">{movie['title_en']}</h4>
                            <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px;">
                              {" ".join([f'<span style="background: rgba(99, 102, 241, 0.12); color: #a5b4fc; font-size: 9px; font-weight: 600; padding: 2px 6px; border-radius: 4px;">{g}</span>' for g in movie['categories'].split('/')[:2]])}
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 10px; color: #9ca3af; margin-top: auto; border-top: 1px solid rgba(255, 255, 255, 0.05); padding-top: 8px;">
                              <span>{movie['region'].split('、')[0]}</span>
                              <span>{movie['duration']}</span>
                            </div>
                          </div>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        # Add a tiny button to ask chatbot about this movie
                        if st.button(f"Ask CineBot 💬", key=f"ask_{movie['index']}", use_container_width=True):
                            st.session_state.chat_input_val = t["ask_template"].format(movie["title_zh"])
                            st.session_state.expander_expanded = True
                            st.toast(f"Prompt set: '{st.session_state.chat_input_val}'")
                            st.rerun()

# ----------------- CineBot 浮動對話視窗 -----------------
with st.expander("💬 CineBot 助理 (Chat)", expanded=st.session_state.expander_expanded):
    # 重設展開狀態，讓使用者可點擊收合
    st.session_state.expander_expanded = False

    # Initialize Chat Messages
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # Render Welcome Messages if empty
    if not st.session_state.messages:
        st.markdown(f"<div style='background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius:8px; padding:10px 15px; margin-bottom:15px; font-size:12px; color:#9ca3af; text-align:center;'>{t['welcome_msg']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.04); border-radius:8px; padding:12px 16px; margin-bottom:20px; font-size:13.5px; border-left: 4px solid #6366f1;'>{t['intro_msg'].replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)

    # Render Historical messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # If bot message has retrieved movies, render them in columns below the text
            if "retrieved_movies" in msg and msg["retrieved_movies"]:
                rm_list = msg["retrieved_movies"]
                cols_ret = st.columns(min(len(rm_list), 4))
                for idx, movie_ret in enumerate(rm_list[:4]):
                    with cols_ret[idx]:
                        r_poster = get_movie_poster(movie_ret)
                        st.image(r_poster, caption=f"{movie_ret['title_zh']} (⭐{movie_ret['score']})", use_container_width=True)

    # Input area for chat
    chat_prompt = st.chat_input(t["input_placeholder"])
    
    # Check if a template prompt was set from the gallery tab
    if "chat_input_val" in st.session_state and st.session_state.chat_input_val:
        chat_prompt = st.session_state.chat_input_val
        st.session_state.chat_input_val = None # clear value
        
    if chat_prompt:
        # 1. Render user message
        with st.chat_message("user"):
            st.markdown(chat_prompt)
        st.session_state.messages.append({"role": "user", "content": chat_prompt})
        
        # 2. Match RAG movies context
        matched = retrieve_movies_context(chat_prompt)
        
        context_str = ""
        if matched:
            context_str = "Relevant Movie Dataset Context:\n"
            for m in matched:
                context_str += (
                    f"- Index: {m['index']}, Title: {m['title_zh']} ({m['title_en']}), "
                    f"Score: {m['score']}, Categories: {m['categories']}, "
                    f"Region: {m['region']}, Duration: {m['duration']}, "
                    f"Release: {m['release_date'] if m['release_date'] else 'Unknown'}\n"
                )
                
        # 3. Call LLM or Local fallback
        with st.chat_message("assistant"):
            with st.spinner("AI thinking..."):
                if llm_provider == "local_search":
                    ans = generate_local_response(chat_prompt, matched, lang)
                else:
                    try:
                        ans = call_llm_api(llm_provider, chat_prompt, context_str, api_key, api_base, model_name, lang)
                    except Exception as e:
                        print(f"Error calling LLM in Streamlit chat: {e}", file=sys.stderr)
                        ans = "error_api"
                        
                # 4. Handle API error fallbacks
                if ans == "error_no_key":
                    local_ans = generate_local_response(chat_prompt, matched, lang)
                    ans = f"{t['err_no_key']}{local_ans}"
                elif ans == "error_api":
                    local_ans = generate_local_response(chat_prompt, matched, lang)
                    ans = f"{t['err_conn_failed']}{local_ans}"
                
                st.markdown(ans)
                
                # Render movies carousel if matched
                if matched:
                    cols_ret = st.columns(min(len(matched), 4))
                    for idx, movie_ret in enumerate(matched[:4]):
                        with cols_ret[idx]:
                            r_poster = get_movie_poster(movie_ret)
                            st.image(r_poster, caption=f"{movie_ret['title_zh']} (⭐{movie_ret['score']})", use_container_width=True)
                            
            # Save assistant response to memory
            st.session_state.messages.append({
                "role": "assistant",
                "content": ans,
                "retrieved_movies": matched[:4]
            })
            
            # Rerun page to keep layout in sync
            st.rerun()
