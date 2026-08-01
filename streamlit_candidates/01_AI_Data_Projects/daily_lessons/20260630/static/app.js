// Global translations dictionary
const i18n = {
  zh: {
    title: "CineBot - 電影搜尋與 AI 助理",
    searchPlaceholder: "搜尋電影名稱、上映地區或關鍵字...",
    allGenres: "所有類型",
    tabDrama: "劇情 (Drama)",
    tabRomance: "愛情 (Romance)",
    tabComedy: "喜劇 (Comedy)",
    tabAction: "動作 (Action)",
    tabCrime: "犯罪 (Crime)",
    tabSciFi: "科幻 (Sci-Fi)",
    tabAnimation: "動畫 (Animation)",
    tabAdventure: "冒險 (Adventure)",
    showingMovies: (count, total) => `顯示 ${count} 部電影（共 ${total} 部）`,
    loadingMovies: "<i class=\"fa-solid fa-circle-notch fa-spin\"></i> 載入電影中...",
    noResults: "<i class=\"fa-solid fa-face-frown\"></i> 沒有符合搜尋條件的電影。",
    errorLoading: (msg) => `載入電影失敗: ${msg}`,
    genresLabel: "類型：",
    regionLabel: "地區：",
    catalogIndexLabel: "目錄索引：",
    of: "分之",
    askCinebot: "向 CineBot 詢問這部電影",
    chatTitle: "CineBot AI 助理",
    chatStatus: "在線 (含 100 部電影資料庫)",
    llmConfig: "LLM 模型設定",
    llmProvider: "LLM 供應商",
    geminiKey: "Gemini API 金鑰",
    apiKeyHelp: "您的金鑰儲存在瀏覽器本地，直接傳送給 API 伺服器。",
    modelConfig: "模型名稱",
    saveSettings: "儲存設定",
    clearSettings: "清除設定",
    statusConfigured: "已配置 LLM 連線",
    statusOffline: "使用本地離線搜尋引擎",
    welcomeMsg: "歡迎來到 CineBot！您可以詢問關於前 100 部熱門電影的任何問題（例如評分、片長、上映日期或類型）。",
    introMsg: "您好！我是 CineBot。我可以協助您在爬取的電影清單中進行搜尋、篩選和推薦。<br><br><em>提示：點擊聊天面板上方的齒輪圖標可設定 Gemini API 金鑰或本地 LLM，以獲得更強大的 AI 對話回覆。否則，我將使用本地關鍵字搜尋引擎。</em>",
    inputPlaceholder: "詢問關於電影的問題...",
    settingsSavedGemini: "LLM 設定已儲存。CineBot 現已連線至 Google Gemini！",
    settingsSavedOllama: "LLM 設定已儲存。CineBot 現已連線至本地 Ollama！",
    settingsSavedOpenAI: "LLM 設定已儲存。CineBot 現已連線至 OpenAI 相容端點！",
    settingsCleared: "設定已清除。CineBot 已切換回本地離線搜尋模式。",
    errorSending: "抱歉，傳送訊息時遇到問題。請檢查後端連線。",
    askAboutTemplate: (title) => `請幫我介紹一下電影《${title}》`
  },
  en: {
    title: "CineBot - Scraped Movie Search & AI Assistant",
    searchPlaceholder: "Search by title, region or keywords...",
    allGenres: "All Genres",
    tabDrama: "Drama",
    tabRomance: "Romance",
    tabComedy: "Comedy",
    tabAction: "Action",
    tabCrime: "Crime",
    tabSciFi: "Sci-Fi",
    tabAnimation: "Animation",
    tabAdventure: "Adventure",
    showingMovies: (count, total) => `Showing ${count} of ${total} movies`,
    loadingMovies: "<i class=\"fa-solid fa-circle-notch fa-spin\"></i> Loading Movies...",
    noResults: "<i class=\"fa-solid fa-face-frown\"></i> No movies match your search criteria.",
    errorLoading: (msg) => `Error loading movies: ${msg}`,
    genresLabel: "Genres:",
    regionLabel: "Region:",
    catalogIndexLabel: "Catalog Index:",
    of: "of",
    askCinebot: "Ask CineBot about this movie",
    chatTitle: "CineBot Assistant",
    chatStatus: "Online (100 Movies Context)",
    llmConfig: "LLM Configuration",
    llmProvider: "LLM Provider",
    geminiKey: "Gemini API Key",
    apiKeyHelp: "Your key is stored locally in your browser and sent directly to the server.",
    modelConfig: "Model Name",
    saveSettings: "Save Settings",
    clearSettings: "Remove Key",
    statusConfigured: "LLM Connected",
    statusOffline: "Using Offline Local Engine",
    welcomeMsg: "Welcome to CineBot! Ask me anything about the top 100 movies in our database (e.g. ratings, durations, release dates, or genres).",
    introMsg: "Hello! I'm CineBot. I can help you search, filter, and recommend movies from our scraped list.<br><br><em>Tip: Click the gear icon at the top of the chat panel to add your Gemini API Key or configure a Local LLM for smart conversational answers. Otherwise, I will use a local keyword search engine.</em>",
    inputPlaceholder: "Ask about movies...",
    settingsSavedGemini: "LLM settings saved. CineBot is now connected to Google Gemini!",
    settingsSavedOllama: "LLM settings saved. CineBot is now connected to Ollama!",
    settingsSavedOpenAI: "LLM settings saved. CineBot is now connected to OpenAI-compatible server!",
    settingsCleared: "API Key/Settings removed. CineBot is now in offline search mode.",
    errorSending: "Sorry, I encountered an issue sending your message. Please check the backend connection.",
    askAboutTemplate: (title) => `Tell me about the movie "${title}"`
  }
};

// Global application state
let allMovies = [];
let currentFilterGenre = "";
let currentSearchQuery = "";
let currentLang = localStorage.getItem("app_language") || "zh";

// Chat & LLM state
let llmProvider = localStorage.getItem("llm_provider") || "local_search";
let apiKey = localStorage.getItem("gemini_api_key") || "";
let apiBase = localStorage.getItem("llm_api_base") || "";
let modelName = localStorage.getItem("llm_model_name") || "";

// DOM Elements
const movieGrid = document.getElementById("movieGrid");
const moviesCount = document.getElementById("moviesCount");
const movieSearch = document.getElementById("movieSearch");
const clearSearchBtn = document.getElementById("clearSearchBtn");
const filterTabs = document.querySelectorAll(".filter-tab");

// Modal Elements
const detailModal = document.getElementById("detailModal");
const closeModalBtn = document.getElementById("closeModalBtn");
const modalBody = document.getElementById("modalBody");

// Chat Elements
const chatToggleBtn = document.getElementById("chatToggleBtn");
const chatWidget = document.getElementById("chatWidget");
const closeChatBtn = document.getElementById("closeChatBtn");
const chatMessages = document.getElementById("chatMessages");
const chatInput = document.getElementById("chatInput");
const sendChatBtn = document.getElementById("sendChatBtn");

// Settings Elements
const chatSettingsBtn = document.getElementById("chatSettingsBtn");
const settingsDrawer = document.getElementById("settingsDrawer");
const closeSettingsBtn = document.getElementById("closeSettingsBtn");
const providerSelect = document.getElementById("providerSelect");
const apiKeyGroup = document.getElementById("apiKeyGroup");
const apiKeyLabel = document.getElementById("apiKeyLabel");
const apiKeyInput = document.getElementById("apiKeyInput");
const apiKeyHelpText = document.getElementById("apiKeyHelpText");
const toggleApiKeyVisibility = document.getElementById("toggleApiKeyVisibility");
const apiBaseGroup = document.getElementById("apiBaseGroup");
const apiBaseLabel = document.getElementById("apiBaseLabel");
const apiBaseInput = document.getElementById("apiBaseInput");
const modelGroup = document.getElementById("modelGroup");
const modelLabel = document.getElementById("modelLabel");
const modelInput = document.getElementById("modelInput");
const saveSettingsBtn = document.getElementById("saveSettingsBtn");
const clearKeyBtn = document.getElementById("clearKeyBtn");
const keyStatusBanner = document.getElementById("keyStatusBanner");
const noKeyBanner = document.getElementById("noKeyBanner");

// Text headers & status ids for translation
const langToggleBtn = document.getElementById("langToggleBtn");
const langBtnText = document.getElementById("langBtnText");
const drawerHeaderTitle = document.getElementById("drawerHeaderTitle");
const providerSelectLabel = document.getElementById("providerSelectLabel");
const statusConfiguredText = document.getElementById("statusConfiguredText");
const statusOfflineText = document.getElementById("statusOfflineText");

/* --- PHASE 1: Fetch and Render Movies --- */

async function fetchMovies() {
  try {
    const response = await fetch("/api/movies");
    if (!response.ok) throw new Error("Failed to fetch movies database.");
    allMovies = await response.json();
    renderMovies();
  } catch (error) {
    console.error(error);
    const t = i18n[currentLang];
    movieGrid.innerHTML = `
      <div class="no-results">
        <i class="fa-solid fa-triangle-exclamation"></i>
        <p>${t.errorLoading(error.message)}</p>
      </div>
    `;
  }
}

function renderMovies() {
  let filtered = allMovies;

  if (currentFilterGenre) {
    filtered = filtered.filter(m => m.categories.includes(currentFilterGenre));
  }

  if (currentSearchQuery) {
    const query = currentSearchQuery.toLowerCase();
    filtered = filtered.filter(m => 
      m.title_zh.toLowerCase().includes(query) || 
      m.title_en.toLowerCase().includes(query) || 
      m.region.toLowerCase().includes(query) ||
      m.categories.toLowerCase().includes(query)
    );
  }

  // Update movie count stats
  const t = i18n[currentLang];
  moviesCount.textContent = t.showingMovies(filtered.length, allMovies.length);

  if (filtered.length === 0) {
    movieGrid.innerHTML = `
      <div class="no-results">
        ${t.noResults}
      </div>
    `;
    return;
  }

  movieGrid.innerHTML = filtered.map(movie => {
    // Generate genre tag HTML
    const genres = movie.categories.split('/');
    const tagsHtml = genres.slice(0, 3).map(g => `<span class="tag">${g}</span>`).join('');
    
    // Poster image source (fallback to URL if local path fails)
    const imgPath = movie.local_path ? `/${movie.local_path}` : movie.cover_url;

    return `
      <div class="movie-card" onclick="openMovieDetail(${movie.index})">
        <span class="index-badge">#${movie.index}</span>
        <span class="score-badge"><i class="fa-solid fa-star"></i> ${movie.score}</span>
        <div class="card-poster-wrapper">
          <img src="${imgPath}" alt="${movie.title_zh}" loading="lazy" onerror="this.src='${movie.cover_url}'">
        </div>
        <div class="card-details">
          <h3>${movie.title_zh}</h3>
          <h4>${movie.title_en}</h4>
          <div class="tag-list">${tagsHtml}</div>
          <div class="card-meta">
            <span class="region">${movie.region.split('、')[0]}</span>
            <span class="duration">${movie.duration}</span>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

/* --- PHASE 2: Search and Category Filtering Events --- */

movieSearch.addEventListener("input", (e) => {
  currentSearchQuery = e.target.value.trim();
  clearSearchBtn.style.display = currentSearchQuery ? "block" : "none";
  renderMovies();
});

clearSearchBtn.addEventListener("click", () => {
  movieSearch.value = "";
  currentSearchQuery = "";
  clearSearchBtn.style.display = "none";
  renderMovies();
  movieSearch.focus();
});

filterTabs.forEach(tab => {
  tab.addEventListener("click", () => {
    filterTabs.forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    currentFilterGenre = tab.dataset.genre;
    renderMovies();
  });
});

/* --- PHASE 3: Detail Modal Views --- */

function openMovieDetail(index) {
  const movie = allMovies.find(m => m.index === index);
  if (!movie) return;

  const t = i18n[currentLang];
  const imgPath = movie.local_path ? `/${movie.local_path}` : movie.cover_url;
  
  modalBody.innerHTML = `
    <div class="modal-poster">
      <img src="${imgPath}" alt="${movie.title_zh}" onerror="this.src='${movie.cover_url}'">
    </div>
    <div class="modal-info">
      <h2>${movie.title_zh}</h2>
      <h3>${movie.title_en}</h3>
      
      <div class="modal-meta-row">
        <span class="modal-score"><i class="fa-solid fa-star"></i> ${movie.score}</span>
        <span class="modal-divider"></span>
        <span class="modal-duration"><i class="fa-regular fa-clock"></i> ${movie.duration}</span>
        <span class="modal-divider"></span>
        <span class="modal-release"><i class="fa-regular fa-calendar"></i> ${movie.release_date || 'N/A'}</span>
      </div>

      <div class="modal-details-grid">
        <dt>${t.genresLabel}</dt>
        <dd>${movie.categories.split('/').join(' / ')}</dd>
        
        <dt>${t.regionLabel}</dt>
        <dd>${movie.region}</dd>
        
        <dt>${t.catalogIndexLabel}</dt>
        <dd>#${movie.index} ${t.of} 100</dd>
      </div>
      
      <button class="btn btn-save" style="margin-top: 15px; width: fit-content;" onclick="askAboutThisMovie('${movie.title_zh}')">
        <i class="fa-solid fa-message"></i> ${t.askCinebot}
      </button>
    </div>
  `;

  detailModal.style.display = "flex";
}

function askAboutThisMovie(title) {
  detailModal.style.display = "none";
  if (chatWidget.style.display === "none") {
    toggleChatWidget();
  }
  const t = i18n[currentLang];
  chatInput.value = t.askAboutTemplate(title);
  chatInput.focus();
  adjustTextareaHeight();
}

// Modal closing helpers
closeModalBtn.addEventListener("click", () => detailModal.style.display = "none");
detailModal.addEventListener("click", (e) => {
  if (e.target === detailModal) detailModal.style.display = "none";
});

/* --- PHASE 4: Chatbot Window & RAG Messaging --- */

function toggleChatWidget() {
  const isHidden = chatWidget.style.display === "none";
  chatWidget.style.display = isHidden ? "flex" : "none";
  
  if (isHidden) {
    chatInput.focus();
    scrollToLatestMessage();
  }
}

chatToggleBtn.addEventListener("click", toggleChatWidget);
closeChatBtn.addEventListener("click", () => chatWidget.style.display = "none");

// Adjust text area height dynamically
function adjustTextareaHeight() {
  chatInput.style.height = "auto";
  chatInput.style.height = Math.min(chatInput.scrollHeight, 80) + "px";
}

chatInput.addEventListener("input", adjustTextareaHeight);

async function sendChatMessage() {
  const message = chatInput.value.trim();
  if (!message) return;

  const t = i18n[currentLang];

  // Render User Message
  appendMessage(message, "user-msg");
  chatInput.value = "";
  adjustTextareaHeight();

  // Render Typing Indicator
  const typingIndicator = appendTypingIndicator();
  scrollToLatestMessage();

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        message: message,
        llmProvider: llmProvider,
        apiKey: apiKey,
        apiBase: apiBase,
        modelName: modelName,
        lang: currentLang
      })
    });

    if (!response.ok) throw new Error("Server returned an error");
    const data = await response.json();

    // Remove Typing Indicator
    typingIndicator.remove();

    // Render Bot Response
    appendBotMessage(data.response, data.retrieved_movies);
    scrollToLatestMessage();

  } catch (error) {
    typingIndicator.remove();
    appendMessage(t.errorSending, "bot-msg");
    scrollToLatestMessage();
  }
}

function appendMessage(text, className) {
  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${className}`;
  msgDiv.textContent = text;
  chatMessages.appendChild(msgDiv);
  return msgDiv;
}

function appendBotMessage(text, retrievedMovies) {
  const msgDiv = document.createElement("div");
  msgDiv.className = "message bot-msg";
  
  // Basic rendering of newlines/markdown-ish bold inside responses
  let formattedText = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
    
  msgDiv.innerHTML = formattedText;

  // If we have retrieved movies from RAG, embed a tiny horizontal carousel!
  if (retrievedMovies && retrievedMovies.length > 0) {
    const carousel = document.createElement("div");
    carousel.className = "chat-movie-carousel";
    
    carousel.innerHTML = retrievedMovies.map(movie => {
      const imgPath = movie.local_path ? `/${movie.local_path}` : movie.cover_url;
      return `
        <div class="chat-movie-card" onclick="openMovieDetail(${movie.index})">
          <div class="chat-movie-poster">
            <img src="${imgPath}" alt="${movie.title_zh}" onerror="this.src='${movie.cover_url}'">
          </div>
          <div class="chat-movie-title">${movie.title_zh}</div>
        </div>
      `;
    }).join('');
    
    msgDiv.appendChild(carousel);
  }

  chatMessages.appendChild(msgDiv);
}

function appendTypingIndicator() {
  const indicatorDiv = document.createElement("div");
  indicatorDiv.className = "message bot-msg";
  indicatorDiv.innerHTML = `
    <div class="typing-indicator">
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
    </div>
  `;
  chatMessages.appendChild(indicatorDiv);
  return indicatorDiv;
}

function scrollToLatestMessage() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

sendChatBtn.addEventListener("click", sendChatMessage);
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendChatMessage();
  }
});

/* --- PHASE 5: Settings and API Key Management --- */

function initSettings() {
  providerSelect.value = llmProvider;
  apiKeyInput.value = apiKey;
  apiBaseInput.value = apiBase;
  modelInput.value = modelName;
  updateSettingsUI();
  updateKeyStatusDisplay();
}

function updateSettingsUI() {
  const val = providerSelect.value;
  const t = i18n[currentLang];
  
  if (val === "gemini") {
    apiKeyGroup.style.display = "block";
    apiKeyLabel.textContent = t.geminiKey;
    apiKeyInput.placeholder = "AIzaSy...";
    
    apiBaseGroup.style.display = "none";
    
    modelGroup.style.display = "block";
    modelLabel.textContent = t.modelConfig + " (Default: gemini-1.5-flash)";
    modelInput.placeholder = "gemini-1.5-flash";
  } else if (val === "ollama") {
    apiKeyGroup.style.display = "none";
    
    apiBaseGroup.style.display = "block";
    apiBaseLabel.textContent = "Ollama Base URL";
    apiBaseInput.placeholder = "http://localhost:11434";
    
    modelGroup.style.display = "block";
    modelLabel.textContent = t.modelConfig + " (Default: llama3)";
    modelInput.placeholder = "llama3";
  } else if (val === "openai_compatible") {
    apiKeyGroup.style.display = "block";
    apiKeyLabel.textContent = "API Key (Optional)";
    apiKeyInput.placeholder = "sk-xxxxxxxx";
    
    apiBaseGroup.style.display = "block";
    apiBaseLabel.textContent = "API Base URL";
    apiBaseInput.placeholder = "http://localhost:12345/v1";
    
    modelGroup.style.display = "block";
    modelLabel.textContent = t.modelConfig + " (Default: meta-llama-3-8b-instruct)";
    modelInput.placeholder = "meta-llama-3-8b-instruct";
  } else {
    // offline local search
    apiKeyGroup.style.display = "none";
    apiBaseGroup.style.display = "none";
    modelGroup.style.display = "none";
  }
}

function updateKeyStatusDisplay() {
  if (llmProvider !== "local_search") {
    keyStatusBanner.style.display = "flex";
    noKeyBanner.style.display = "none";
  } else {
    keyStatusBanner.style.display = "none";
    noKeyBanner.style.display = "flex";
  }
}

providerSelect.addEventListener("change", updateSettingsUI);

chatSettingsBtn.addEventListener("click", () => {
  settingsDrawer.style.display = "flex";
});

closeSettingsBtn.addEventListener("click", () => {
  settingsDrawer.style.display = "none";
});

toggleApiKeyVisibility.addEventListener("click", () => {
  const isPassword = apiKeyInput.type === "password";
  apiKeyInput.type = isPassword ? "text" : "password";
  toggleApiKeyVisibility.innerHTML = isPassword ? 
    `<i class="fa-solid fa-eye-slash"></i>` : 
    `<i class="fa-solid fa-eye"></i>`;
});

saveSettingsBtn.addEventListener("click", () => {
  llmProvider = providerSelect.value;
  apiKey = apiKeyInput.value.trim();
  apiBase = apiBaseInput.value.trim();
  modelName = modelInput.value.trim();
  
  localStorage.setItem("llm_provider", llmProvider);
  localStorage.setItem("gemini_api_key", apiKey);
  localStorage.setItem("llm_api_base", apiBase);
  localStorage.setItem("llm_model_name", modelName);
  
  updateKeyStatusDisplay();
  settingsDrawer.style.display = "none";
  
  const t = i18n[currentLang];
  let statusMsg = "";
  if (llmProvider === "gemini") {
    statusMsg = t.settingsSavedGemini;
  } else if (llmProvider === "ollama") {
    statusMsg = t.settingsSavedOllama;
  } else if (llmProvider === "openai_compatible") {
    statusMsg = t.settingsSavedOpenAI;
  } else {
    statusMsg = t.settingsCleared;
  }
  
  appendMessage(statusMsg, "system-msg");
  scrollToLatestMessage();
});

clearKeyBtn.addEventListener("click", () => {
  apiKeyInput.value = "";
  apiBaseInput.value = "";
  modelInput.value = "";
  providerSelect.value = "local_search";
  
  llmProvider = "local_search";
  apiKey = "";
  apiBase = "";
  modelName = "";
  
  localStorage.removeItem("llm_provider");
  localStorage.removeItem("gemini_api_key");
  localStorage.removeItem("llm_api_base");
  localStorage.removeItem("llm_model_name");
  
  updateKeyStatusDisplay();
  updateSettingsUI();
  settingsDrawer.style.display = "none";
  
  const t = i18n[currentLang];
  appendMessage(t.settingsCleared, "system-msg");
  scrollToLatestMessage();
});

/* --- PHASE 6: Multilingual Switcher --- */

function applyLocalization() {
  const lang = currentLang;
  const t = i18n[lang];
  
  // Title
  document.title = t.title;
  
  // Search bar
  movieSearch.placeholder = t.searchPlaceholder;
  
  // Lang Toggle Button
  langBtnText.textContent = lang === "zh" ? "EN" : "繁";
  
  // Filter tabs
  document.getElementById("tabAll").textContent = t.allGenres;
  document.getElementById("tabDrama").textContent = t.tabDrama;
  document.getElementById("tabRomance").textContent = t.tabRomance;
  document.getElementById("tabComedy").textContent = t.tabComedy;
  document.getElementById("tabAction").textContent = t.tabAction;
  document.getElementById("tabCrime").textContent = t.tabCrime;
  document.getElementById("tabSciFi").textContent = t.tabSciFi;
  document.getElementById("tabAnimation").textContent = t.tabAnimation;
  document.getElementById("tabAdventure").textContent = t.tabAdventure;
  
  // Update Header Movie Count text and Card text
  renderMovies();
  
  // Chat title & status
  document.querySelector(".chat-title h3").textContent = t.chatTitle;
  document.querySelector(".chat-title span").textContent = t.chatStatus;
  
  // Settings labels
  drawerHeaderTitle.innerHTML = `<i class="fa-solid fa-sliders"></i> ` + t.llmConfig;
  providerSelectLabel.textContent = t.llmProvider;
  apiKeyHelpText.textContent = t.apiKeyHelp;
  saveSettingsBtn.textContent = t.saveSettings;
  clearKeyBtn.textContent = t.clearSettings;
  statusConfiguredText.textContent = t.statusConfigured;
  statusOfflineText.textContent = t.statusOffline;
  
  // Input placeholders update
  chatInput.placeholder = t.inputPlaceholder;
  
  updateSettingsUI();
  renderWelcomeMessages();
}

function renderWelcomeMessages() {
  // Only render welcome messages if there are no user messages yet
  const userMsgs = chatMessages.querySelectorAll(".user-msg");
  if (userMsgs.length === 0) {
    const t = i18n[currentLang];
    chatMessages.innerHTML = `
      <div class="message system-msg">${t.welcomeMsg}</div>
      <div class="message bot-msg">${t.introMsg}</div>
    `;
  }
}

langToggleBtn.addEventListener("click", () => {
  currentLang = currentLang === "zh" ? "en" : "zh";
  localStorage.setItem("app_language", currentLang);
  applyLocalization();
});

/* --- PHASE 7: Initialization --- */

document.addEventListener("DOMContentLoaded", () => {
  fetchMovies();
  initSettings();
  applyLocalization();
});
