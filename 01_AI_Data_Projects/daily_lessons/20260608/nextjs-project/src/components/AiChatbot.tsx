"use client";

import React, { useState, useEffect, useRef } from "react";
import { MessageSquare, Settings, X, Send, Bot, User, Loader2 } from "lucide-react";

interface Message {
  text: string;
  sender: "user" | "bot";
}

export default function AiChatbot() {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [showSettings, setShowSettings] = useState<boolean>(false);
  const [apiKey, setApiKey] = useState<string>("");
  const [inputVal, setInputVal] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "bot",
      text: `你好！我是你的 AI 機器學習導師。您可以向我詢問關於這十大機器學習主題的任何問題，例如：
      \n💡 「SVM 的最大間距邊界是？」
      \n💡 「決策樹基尼係數如何計算？」
      \n💡 「過擬合 (Overfitting) 是什麼意思？」`
    }
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load API Key from localStorage
    const savedKey = localStorage.getItem("gemini_api_key");
    if (savedKey) {
      setApiKey(savedKey);
    }
  }, []);

  useEffect(() => {
    // Scroll to bottom on new message
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSaveApiKey = (key: string) => {
    const trimmed = key.trim();
    setApiKey(trimmed);
    localStorage.setItem("gemini_api_key", trimmed);
    alert(trimmed ? "Gemini API 金鑰儲存成功！" : "API 金鑰已清除，將使用本機問答引擎。");
    setShowSettings(false);
  };

  const getLocalResponse = (question: string): string => {
    const q = question.toLowerCase();
    
    // Keyword rules matching
    const rules = [
      { keys: ["svm", "向量機", "margin", "邊界", "楚河漢界", "超平面"], tag: "svm" },
      { keys: ["隨機森林", "random forest", "森林", "stump"], tag: "randomForest" },
      { keys: ["決策樹", "gini", "基尼", "不純", "樹"], tag: "tree" },
      { keys: ["貝氏", "bayes", "獨立", "垃圾郵件"], tag: "bayes" },
      { keys: ["過擬合", "overfit", "死背"], tag: "overfitting" },
      { keys: ["線性迴歸", "linear", "最小平方", "趨勢線"], tag: "linear" },
      { keys: ["邏輯迴歸", "logistic", "sigmoid", "二分"], tag: "logistic" },
      { keys: ["knn", "最近鄰", "距離", "鄰居"], tag: "knn" },
      { keys: ["kmeans", "分群", "群心"], tag: "kmeans" },
      { keys: ["pca", "降維", "主成分", "協方差"], tag: "pca" },
      { keys: ["神經網路", "深度學習", "神經元", "人臉", "表情"], tag: "deep" },
      { keys: ["助教", "功能", "你好", "哈囉", "誰"], tag: "tutor" }
    ];

    let matchedTag = "";
    for (const rule of rules) {
      if (rule.keys.some(k => q.includes(k))) {
        matchedTag = rule.tag;
        break;
      }
    }

    const localAnswers: { [key: string]: string } = {
      svm: `### 🛡️ 支援向量機 (SVM) 核心精華\n\n**支援向量機 (Support Vector Machine, SVM)** 的目標是在特徵空間中尋找一個**最大安全邊際 (Margin) 的決策邊界（超平面）**來區分類別。\n\n* **支援向量 (Support Vectors)**：最接近決策邊界的那幾個樣本點，正是這幾個點「支撐」起這條邊界線。如果移除其他點，邊界不會變；但如果移動支援向量，邊界就會改變！\n* **最大間距 (Max Margin)**：邊界到最近的支援向量的距離要最大化。這代表模型擁有最高的穩定度與泛化能力。\n* **核技巧 (Kernel Trick)**：若資料在低維空間裝不下、混雜在一起，SVM 可以使用核函數 (如 RBF、Polynomial) 將資料映射到高維空間，在更高維度實現完美的線性切分！`,
      tree: `### 🌿 決策樹 (Decision Tree) 核心精華\n\n**決策樹**是一種「樹狀結構」的分類與迴歸方法，結構完全透明，是最經典的**「白箱」演算法**。\n\n* **不純度 (Impurities)**：決策樹會依據特徵數值，將資料分成左右兩邊。選擇特徵時，主要基於**基尼係數 (Gini Index)** 或 **訊息熵 (Entropy)** 的降低程度。\n* **Gini 係數計算**：$Gini(D) = 1 - \\sum p_i^2$。當 Gini 越接近 0，代表該節點的資料越純（都是同一類）；當 Gini 等於 0.5 時，代表兩種類別各佔一半，最不純。\n* **剪枝 (Pruning)**：決策樹容易長得太深，完美死記訓練集，導致過擬合 (Overfitting)。實務上需透過限制深度或剪枝來限制樹的生長。`,
      randomForest: `### 🌲 隨機森林 (Random Forest) 核心精華\n\n**隨機森林**是經典的**集成學習 (Ensemble Learning)** 方法，它透過「集體智慧」來解決單棵決策樹容易過擬合的問題。\n\n* **自助抽樣 (Bootstrap Aggregation / Bagging)**：隨機森林會從原始資料中，重複隨機抽取樣本（放回抽樣）來訓練多棵獨立的決策樹。\n* **特徵隨機選擇**：在每次分支時，只隨機挑選一部分特徵進行評估，避免單一強特徵主導了所有樹，增加樹與樹之間的差異性。\n* **多數決投票 (Voting)**：新資料進來時，由森林中所有的決策樹各自預測，最後以**多數決 (Classification)** 或 **平均數 (Regression)** 決定最終答案。`,
      bayes: `### ✉️ 單純貝氏 (Naive Bayes) 核心精華\n\n**單純貝氏**是基於**貝氏定理**的機率分類器，由於其假設特徵之間「單純獨立」，因此計算速度快到不可思議。\n\n* **貝氏定理**：$P(C|X) = \\frac{P(X|C) \\cdot P(C)}{P(X)}$。即在看到特徵 $X$ 後，推測它屬於類別 $C$ 的後驗機率。\n* **單純假設 (Naive Assumption)**：強烈假設各特徵之間「彼此獨立、互不影響」。例如信件中出現「中獎」與「免費」是獨立的。雖然在現實中極少成立，但在垃圾郵件過濾、文本分類上效果卻驚人地好。\n* **高斯貝氏 (Gaussian NB)**：當特徵是連續變數（如網格座標）時，我們假設特徵呈常態分佈，計算均值與變異數來計算機率。`,
      overfitting: `### ⚠️ 什麼是過擬合 (Overfitting)？\n\n**過擬合 (Overfitting)** 是機器學習中最常見的難題，指模型在**訓練集表現極佳，但在未見過的測試集上表現極差**的現象。\n\n* **原因**：模型學得「太努力」了，連訓練資料中的「雜訊 (Noise)」、「死背的特徵」都一起背了下來。\n* **視覺特徵**：在沙盒畫面上，決策邊界如果顯得非常破碎、扭曲，繞過每一個雜點，這通常就是過擬合的徵兆。\n* **解決方案**：\n  1. 增加訓練數據量。\n  2. **正規化 (Regularization)**：懲罰過於複雜的權重（如 SVM 的 C 參數、線性迴歸的 Ridge/Lasso）。\n  3. **限制模型複雜度**：例如限制決策樹的最大深度。\n  4. **集成學習**：例如隨機森林。`,
      linear: `### 📊 線性迴歸 (Linear Regression) 核心精華\n\n**線性迴歸**假設特徵與預測目標之間存在連續的線性映射關係，尋找最佳擬合直線。\n\n* **最小平方法 (OLS)**：透過最小化殘差平方和（預測值與實際值的誤差平方），來決定趨勢線的斜率與截距。\n* **決定係數 $R^2$**：介於 0 到 1 之間。$R^2$ 越接近 1，表示模型解釋資料變異的能力越強。`,
      logistic: `### 🛑 邏輯迴歸 (Logistic Regression) 核心精華\n\n雖然叫迴歸，但**邏輯迴歸**是用於**二元分類**的。它將線性方程式的連續輸出映射至 [0, 1] 的機率範圍。\n\n* **Sigmoid 函數**：$P(Y=1|X) = \\frac{1}{1 + e^{-z}}$，將任何實數壓縮成機率。\n* **交叉熵損失 (Cross-Entropy Loss)**：做為分類的代價函數，透過梯度下降法 (Gradient Descent) 迭代尋找最佳權重。`,
      knn: `### 📍 K-最近鄰 (KNN) 核心精華\n\n**KNN** 是一種基於「物以類聚」的**懶惰學習 (Lazy Learner)** 演算法。\n\n* **運作機制**：新樣本進來時，不需事先訓練，而是直接計算與所有訓練樣本的**歐氏距離**，挑選最近的 $K$ 個鄰居，以多數決決定新樣本的分類。\n* **$K$ 值的影響**：$K$ 太小（如 $K=1$）極易受局部噪點干擾，導致模型過擬合；$K$ 太大則容易使邊界過於平滑，導致欠擬合。`,
      kmeans: `### 🧲 K-Means 分群 核心精華\n\n**K-Means** 是一種**非監督式學習**演算法，用來將無標籤的數據自動凝聚為 $K$ 個群體。\n\n* **運作機制**：\n  1. 隨機指定 $K$ 個群心。\n  2. **分配步驟**：將每個點歸入距離最近的群心。\n  3. **更新步驟**：重新計算每個群體中所有點的平均值做為新群心。\n  4. 重複分配與更新，直到群心不再移動（收斂）。`,
      pca: `### 📉 主成分分析 (PCA) 核心精華\n\n**PCA** 是一種最常用的**線性降維與特徵提取**演算法。\n\n* **運作機制**：藉由正交轉換，將多維相關特徵投影到一組新的「主成分 (PC)」上。\n* **保留變異數**：第一主成分 (PC1) 沿著資料變異數最大（最分散、保留最多原始資訊）的軸向；第二主成分 (PC2) 則與 PC1 正交且變異數次大。`,
      deep: `### 🧠 類神經網路 / 深度學習 核心精華\n\n**類神經網路**模擬生物大腦的突觸結構，是深度學習的骨幹。\n\n* **多層架構**：包含輸入層、多個隱藏層 (Hidden Layers) 與輸出層。每層由多個神經元組成，各自乘上權重並經過非線性激活函數 (如 ReLU, Sigmoid) 轉換。\n* **反向傳播 (Backpropagation)**：計算預測與實際標籤的損失，將誤差從輸出層往回傳遞以修正權重參數。`,
      tutor: `您好！我是您的 AI 學習助教。我有以下功能：\n1. 隨時透過視訊相機監測您的讀書專注度與困惑表情。\n2. 當您露出困惑表情時，我會主動提供生活化的比喻（例如 SVM 的楚河漢界、K-Means 的選組長比喻）。\n3. 當您學得順手時，我會出考題來挑戰您！\n4. 您可以在這裡打字向我發問任何機器學習演算法的問題！`
    };

    return localAnswers[matchedTag] || `我收到您的提問了！目前我沒有在我的本地知識庫中找到與這項提問精確符合的演算法說明。\n\n💡 **您可以嘗試提問包含這些關鍵字的問題：**\n* 決策樹、隨機森林、SVM、單純貝氏、KNN、線性迴歸、邏輯迴歸、KMeans、PCA、神經網路。\n* 或詢問關於 **過擬合 (Overfitting)** 等概念。\n\n*(如果您想要不受限制的任意 AI 聊天，可以點擊右上角 ⚙️ 設定並貼上您的 **Gemini API Key**！)*`;
  };

  const fetchGeminiResponse = async (question: string): Promise<string> => {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`;
    const sysInstruction = "You are a helpful, encouraging, and highly knowledgeable AI Machine Learning Tutor for NCHU AI Training program. Explain machine learning algorithms in a friendly, dynamic way, using Chinese (zh-Hant). Provide short code blocks or clear analogies if asked. Keep responses concise and clean so they fit nicely in a small chat window.";
    
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: [{
          parts: [{ text: `${sysInstruction}\n\nUser Question: ${question}` }]
        }]
      })
    });

    if (!response.ok) {
      throw new Error("API Response Error");
    }

    const data = await response.json();
    return data.candidates[0].content.parts[0].text;
  };

  const handleSend = async (question: string) => {
    if (!question.trim()) return;
    setInputVal("");

    const newMessages = [...messages, { sender: "user", text: question } as Message];
    setMessages(newMessages);
    setIsLoading(true);

    let answer = "";
    if (apiKey) {
      try {
        answer = await fetchGeminiResponse(question);
      } catch (err) {
        console.error(err);
        answer = `❌ **連線錯誤**：無法呼叫 Gemini API。請確認您的 API 金鑰是否有效且網路連線正常。\n\n*系統已自動切換回本機問答模式。*\n\n` + getLocalResponse(question);
      }
    } else {
      answer = getLocalResponse(question);
    }

    setIsLoading(false);
    setMessages((prev) => [...prev, { sender: "bot", text: answer }]);
  };

  const parseMarkdown = (text: string) => {
    let html = text;
    // Code blocks
    html = html.replace(/\`\`\`(.*?)\n([\s\S]*?)\`\`\`/g, '<pre class="bg-slate-950 p-2.5 rounded-lg my-1.5 overflow-x-auto font-mono text-[10px] text-slate-300 border border-slate-800">$2</pre>');
    // Inline code
    html = html.replace(/\`([^`\n]+)\`/g, '<code class="bg-slate-950 px-1 py-0.5 rounded font-mono text-[10px] text-pink-400">$1</code>');
    // Headers
    html = html.replace(/^### (.*$)/gim, '<h4 class="text-white font-bold text-xs mt-2 mb-1">$1</h4>');
    html = html.replace(/^## (.*$)/gim, '<h3 class="text-white font-bold text-sm mt-3 mb-1.5">$1</h3>');
    html = html.replace(/^# (.*$)/gim, '<h2 class="text-white font-bold text-base mt-4 mb-2">$1</h2>');
    // Bold
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong class="text-indigo-400 font-bold">$1</strong>');
    // Bullet points
    html = html.replace(/^\* (.*$)/gim, '<li class="ml-3 list-disc text-slate-300 my-0.5">$1</li>');
    html = html.replace(/^- (.*$)/gim, '<li class="ml-3 list-disc text-slate-300 my-0.5">$1</li>');
    // Newlines
    html = html.replace(/\n/g, "<br>");
    return <div dangerouslySetInnerHTML={{ __html: html }} />;
  };

  return (
    <>
      {/* Floating Chat Button */}
      <div className="fixed top-6 right-6 z-45 no-print">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold p-3.5 rounded-full shadow-2xl flex items-center justify-center transition transform hover:scale-105 active:scale-95 border border-indigo-400/20 relative"
        >
          <MessageSquare size={20} />
          <span className="absolute top-0 right-0 w-2.5 h-2.5 bg-emerald-500 rounded-full border-2 border-slate-950 animate-ping"></span>
        </button>
      </div>

      {/* Floating Chat Window */}
      <div
        className={`fixed top-24 right-6 z-45 max-w-sm w-96 h-[480px] bg-slate-900/95 backdrop-blur-md border border-slate-800 rounded-2xl shadow-2xl flex flex-col transition-all duration-300 transform ${
          isOpen ? "opacity-100 translate-y-0 pointer-events-auto" : "opacity-0 translate-y-4 pointer-events-none"
        } no-print`}
      >
        {/* Chat Header */}
        <div className="p-3 border-b border-slate-800 flex justify-between items-center bg-slate-950/40 rounded-t-2xl">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse"></div>
            <div>
              <h5 className="text-white font-bold text-xs tracking-wide">AI 機器學習導師</h5>
              <span className="text-[9px] text-slate-500 font-semibold block uppercase">NCHU ML Tutor</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="text-slate-400 hover:text-white transition p-1 rounded-lg hover:bg-slate-800"
            >
              <Settings size={16} />
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="text-slate-400 hover:text-white transition p-1 rounded-lg hover:bg-slate-800"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* API Key Settings Panel */}
        {showSettings && (
          <div className="p-3 border-b border-slate-800 bg-slate-950/80 text-xs space-y-1.5">
            <p className="text-slate-300 font-bold">Gemini API Key 設定</p>
            <p className="text-slate-500 text-[10px] leading-relaxed">
              設定後將啟用真實 Gemini AI 聊天。金鑰將僅存在您的瀏覽器中。
            </p>
            <div className="flex gap-2">
              <input
                type="password"
                defaultValue={apiKey}
                id="api-key-input-field"
                placeholder="貼上您的 Gemini API Key..."
                className="flex-1 bg-slate-900 border border-slate-800 text-slate-100 rounded-lg px-2 py-1 text-xs focus:outline-none focus:border-indigo-500"
              />
              <button
                onClick={() => {
                  const el = document.getElementById("api-key-input-field") as HTMLInputElement;
                  handleSaveApiKey(el ? el.value : "");
                }}
                className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-lg transition text-[10px]"
              >
                儲存
              </button>
            </div>
          </div>
        )}

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 text-xs scroll-smooth">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex items-start gap-2.5 ${msg.sender === "user" ? "flex-row-reverse" : ""}`}>
              <div
                className={`p-1.5 rounded-lg shrink-0 ${
                  msg.sender === "user" ? "bg-indigo-600 text-white" : "bg-indigo-600/10 text-indigo-400"
                }`}
              >
                {msg.sender === "user" ? <User size={14} /> : <Bot size={14} />}
              </div>
              <div
                className={`px-3 py-2 rounded-2xl rounded-tl-none max-w-[80%] leading-relaxed ${
                  msg.sender === "user"
                    ? "bg-indigo-600/10 border border-indigo-500/20 text-slate-100"
                    : "bg-slate-850 border border-slate-800/80 text-slate-200"
                }`}
              >
                {msg.sender === "user" ? msg.text : parseMarkdown(msg.text)}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex items-start gap-2.5">
              <div className="bg-indigo-600/10 text-indigo-400 p-1.5 rounded-lg shrink-0">
                <Loader2 size={14} className="animate-spin" />
              </div>
              <div className="bg-slate-850 border border-slate-800/80 text-slate-400 px-3 py-2 rounded-2xl rounded-tl-none font-mono">
                思考中...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Suggestion Chips */}
        <div
          className="px-3 py-1.5 border-t border-slate-850/50 flex gap-1.5 overflow-x-auto whitespace-nowrap text-[10px] no-print"
          style={{ scrollbarWidth: "none" }}
        >
          <button
            onClick={() => handleSend("SVM 的最大邊際是什麼？")}
            className="px-2 py-1 bg-slate-850 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-300 rounded-full transition shrink-0"
          >
            🛡️ SVM 邊際
          </button>
          <button
            onClick={() => handleSend("請解釋決策樹的基尼係數")}
            className="px-2 py-1 bg-slate-850 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-300 rounded-full transition shrink-0"
          >
            🌿 決策樹 Gini
          </button>
          <button
            onClick={() => handleSend("什麼是機器學習的過擬合？")}
            className="px-2 py-1 bg-slate-850 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-300 rounded-full transition shrink-0"
          >
            ⚠️ 什麼是過擬合？
          </button>
          <button
            onClick={() => handleSend("單純貝氏的獨立假設是什麼？")}
            className="px-2 py-1 bg-slate-850 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-300 rounded-full transition shrink-0"
          >
            ✉️ 貝氏獨立假設
          </button>
        </div>

        {/* Input Box */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/40 rounded-b-2xl flex gap-2">
          <input
            type="text"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSend(inputVal);
            }}
            placeholder="輸入問題..."
            className="flex-1 bg-slate-950 border border-slate-800 text-slate-100 rounded-xl px-3 py-1.5 text-xs focus:outline-none focus:border-indigo-500"
          />
          <button
            onClick={() => handleSend(inputVal)}
            className="bg-indigo-600 hover:bg-indigo-500 text-white p-2 rounded-xl flex items-center justify-center transition shadow-md shadow-indigo-950/30"
          >
            <Send size={14} />
          </button>
        </div>
      </div>
    </>
  );
}
