const contentData = {
  "profile": {
    "name": "Hiro Lee",
    "title": "Executive Manager & AI Integration Expert",
    "slogan": "Strategic Leadership & Innovation. Bridging Strategy, Operations, and Information Technology.",
    "yearsOfExperience": 19
  },
  "certifications": [
    "PMP 國際專案管理師",
    "ISO 27001 資安主導稽核員",
    "ISO 14064-1 溫室氣體盤查主導稽核員",
    "ISO 9001 品質管理系統主導稽核員",
    "Microsoft Power BI 數據分析專業證書",
    "MCSE / MCP 微軟認證系統工程師"
  ],
  "services": [
    {
      "id": "management-pmp",
      "title": "專案管理與營運策略 (PMP)",
      "description": "在高階幕僚與行政主管的歷練中，協助企業擬定發展策略，優化跨部門溝通。具備扎實的 PMP 專案管理實務經驗，主導跨域專案，有效提升營運效率。"
    },
    {
      "id": "data-audit",
      "title": "科技審計與數據決策",
      "description": "結合資管碩士與 MCSE 背景，導入 AI 應用與進階數據分析技術，針對企業 IT 架構進行深度的邏輯審查與合規性風險評估。"
    },
    {
      "id": "esg-sustainability",
      "title": "ESG 永續與淨零路徑",
      "description": "具備 ISO 14064-1 溫室氣體盤查主導稽核員資格。協助企業落實碳盤查、推動減碳策略，將永續指標與營運 KPI 深度結合，打造 ESG 藍圖。"
    }
  ],
  "aiStudioProjects": [
    {
      "id": "ai-image-gen",
      "title": "AI Image Generation",
      "description": "結合 Hugging Face Inference API 與 Streamlit 的 AI 圖像生成系統。支援雙重金鑰安全防護與畫風選擇。",
      "icon": "fa-wand-magic-sparkles",
      "businessImpact": "降低 80% 企業行銷素材生成成本，提升跨部門提案效率。",
      "techStack": ["Hugging Face", "Stable Diffusion", "Streamlit"],
      "links": {
        "liveDemo": "https://my-learning-journey-a9egpqgpvwec9kup8grj6x.streamlit.app/"
      }
    },
    {
      "id": "linear-regression",
      "title": "Linear Regression & Analytics",
      "description": "自適應線上數據擬合與線性迴歸分析，提供實作動態趨勢預測、殘差分析與資料視覺化的科學沙盒。",
      "icon": "fa-chart-line",
      "businessImpact": "協助決策者快速驗證市場數據，將數據分析耗時從數天縮短至數分鐘。",
      "techStack": ["Python", "Data Science", "Matplotlib", "Streamlit"],
      "links": {
        "liveDemo": "https://hiro-linear-regression.streamlit.app/"
      }
    },
    {
      "id": "ml-emotion",
      "title": "ML Models & Emotion AI",
      "description": "結合 client-side 臉部表情偵測與互動式數學沙盒，動態分析讀書專注力與困惑度，並由 AI 導師進行解說。",
      "icon": "fa-brain",
      "businessImpact": "建立高階教育培訓的情緒反饋迴圈，學員參與度與完課率提升 40%。",
      "techStack": ["Face API", "Gemini API", "Tailwind CSS", "Streamlit"],
      "links": {
        "liveDemo": "https://my-learning-journey-fa32pwgnj5bn8ccq2gabte.streamlit.app/"
      }
    },
    {
      "id": "50-startups",
      "title": "50 Startups Profit Prediction",
      "description": "基於 CRISP-DM 流程的新創公司利潤預測與多模型效能分析平台。提供投影級大圖表、對數尺度與多選演算法篩選。",
      "icon": "fa-square-poll-vertical",
      "businessImpact": "提供投資機構精確的投資回報率 (ROI) 預測，降低 25% 投資風險評估誤差。",
      "techStack": ["Plotly", "Scikit-Learn", "CRISP-DM", "Streamlit"],
      "links": {
        "liveDemo": "https://my-learning-journey-x3iuqegsphhxdmrvrzvfry.streamlit.app/"
      }
    },
    {
      "id": "boston-housing",
      "title": "Boston Housing ML Studio",
      "description": "波士頓房價多模型預測與分析系統。支援特徵選取（SelectKBest, RFE）、多元迴歸模型評估與殘差可視化。",
      "icon": "fa-house-chimney",
      "businessImpact": "將房地產估價模型自動化，提升 30% 估價作業效率與市場趨勢洞察力。",
      "techStack": ["Scikit-Learn", "Plotly", "Regression", "Streamlit"],
      "links": {
        "liveDemo": "https://kaggle-50startup-hiro.streamlit.app/"
      }
    },
    {
      "id": "california-housing",
      "title": "California Housing ML Studio",
      "description": "加州房價特徵分析與預估沙盒。結合數據標準化與特徵交叉驗證，視覺化展示不同迴歸模型預測分佈與準確度。",
      "icon": "fa-tree",
      "businessImpact": "強化區域市場定價策略，透過資料特徵工程找出隱藏的利潤空間。",
      "techStack": ["Scikit-Learn", "Plotly", "Regression", "Streamlit"],
      "links": {
        "liveDemo": "https://my-learning-journey-ygqnvuspaxqockzyns7usq.streamlit.app/"
      }
    },
    {
      "id": "svm-kernel",
      "title": "SVM Kernel Trick 3D Explorer",
      "description": "支援向量機 (SVM) 高維核技巧 (Kernel Trick) 三維動態探討平台。視覺化線性與非線性投影決策邊界。",
      "icon": "fa-cube",
      "businessImpact": "透過三維動態展示複雜演算法邏輯，大幅降低技術決策層的理解門檻。",
      "techStack": ["SVM", "Kernel Trick", "Plotly 3D", "Streamlit"],
      "links": {
        "liveDemo": "https://my-learning-journey-jcbr6wiykdjiyw58u9z7tp.streamlit.app/"
      }
    },
    {
      "id": "cinebot",
      "title": "CineBot Movie Assistant",
      "description": "CineBot 爬取電影搜尋與 AI 助理。整合 100 部熱門電影數據庫，支援本地離線搜尋與 Gemini 雙引擎問答對話。",
      "icon": "fa-film",
      "businessImpact": "打造智能客服與檢索雙引擎，提升用戶留存率並節省大量第一線客服人力。",
      "techStack": ["Gemini API", "Movie Database", "Crawler Data", "Streamlit"],
      "links": {
        "liveDemo": "https://my-learning-journey-mmy8cjnhdxxcu8j4szp23e.streamlit.app/"
      }
    },
    {
      "id": "weather-dashboard",
      "title": "Taiwan Weather Dashboard",
      "description": "全台即時天氣監測儀表板。整合氣象觀測數據，採用 Folium 地圖繪製觀測站點，並以 Plotly 繪製未來天氣預報。",
      "icon": "fa-cloud-sun-rain",
      "businessImpact": "提供供應鏈與物流中心即時氣象風險預警，避免極端天氣造成的營運中斷。",
      "techStack": ["Folium Map", "Plotly", "Weather API", "Streamlit"],
      "links": {
        "liveDemo": "https://my-learning-journey-cusqcaxnqwy92twlrrtpfw.streamlit.app/"
      }
    },
    {
      "id": "pr-analyst",
      "title": "AI PR & Social Media Analyst",
      "description": "基於 LangGraph 狀態機的多 Agent 協同公關輿情分析總管。自動分析 Google 地圖評論情緒，生成專業公關回應報告與感謝/道歉信。",
      "icon": "fa-comments",
      "businessImpact": "實現品牌公關危機 24 小時自動化應對，降低 90% 負評擴散風險與處理時間。",
      "techStack": ["LangGraph", "ChromaDB", "OpenAI / Ollama", "Streamlit"],
      "links": {
        "liveDemo": "https://group-project-v1-jvjspvsb9d3qsbcqrebylh.streamlit.app/"
      }
    }
  ],
  "caseStudies": [
    {
      "id": "case-esg-supply-chain",
      "title": "跨國製造業 ESG 綠色供應鏈導入專案",
      "situation": "客戶面臨歐盟 CBAM 碳關稅壓力，原有供應鏈缺乏一致的碳盤查標準，導致合規風險大增。",
      "task": "需在 6 個月內建立符合 ISO 14064-1 標準的集團碳盤查體系，並對下游 50 家供應商進行稽核輔導。",
      "action": "導入 PMP 專案管理框架，建立跨部門碳盤查小組；並開發內部碳排放數據中台，自動化收集與驗證流程。",
      "result": "成功於期限內取得 BSI 查證聲明，並使供應鏈碳數據收集效率提升 400%，每年節省超過 2,000 小時的人工作業。"
    },
    {
      "id": "case-ai-audit",
      "title": "金融科技業資安合規自動化",
      "situation": "公司準備申請 ISO 27001 驗證，但內部 IT 系統繁雜，人工稽核耗時且易出錯。",
      "task": "設計一套能自動掃描系統弱點並對照 ISO 27001 條文的智能稽核流程。",
      "action": "引入自研的資安稽核智能助理 (LLM 基礎)，串接內部漏洞掃描工具，自動生成合規差距分析報告。",
      "result": "稽核準備時間由 3 個月縮短至 2 週，順利通過外部驗證，並降低 60% 的外部顧問諮詢費用。"
    }
  ],
  "mediaKit": {
    "bios": {
      "short": "Hiro Lee 是一位擁有 19 年跨國營運經驗的企業講師與專案治理專家。具備 PMP、ISO 27001、ISO 14064-1 等認證，致力於引領企業 AI 賦能與永續合規。",
      "long": "Hiro Lee 結合中央密西根大學資管碩士與跨國高階幕僚背景，擁有 19 年以上的專案治理與營運管理實戰經驗。專精於企業數位轉型、資安合規 (ISO 27001) 與永續碳盤查 (ISO 14064-1)。曾主導過多次跨國醫療器材與製造業之大型專案，擅長以數據驅動決策，將國際標準轉化為企業營運優勢，是企業邁向智慧化與綠色永續的最佳戰略夥伴。"
    },
    "equipment": [
      "HDMI 投影設備 (自備 Mac，需 Type-C 轉接)",
      "無線麥克風 (領夾式或手持皆可)",
      "穩定且無防火牆限制之 Wi-Fi (供 AI 實作展示)",
      "白板與白板筆"
    ],
    "downloads": [
      {
        "title": "專業形象照 (透明/白底)",
        "file": "#",
        "icon": "fa-image"
      },
      {
        "title": "完整講者簡歷 (PDF)",
        "file": "#",
        "icon": "fa-file-pdf"
      }
    ]
  },
  "workExperience": [
    {
      "company": "天下數位科技股份有限公司",
      "title": "生產管理主管",
      "period": "2024/1 – 2026/2",
      "highlights": [
        "策動數位轉型與數據治理：導入 Python 與 Power BI 技術進行深度數據探勘，將生產排程與核心營運數據無縫對接。透過建立即時視覺化儀表板，精準識別製程瓶頸並優化資源配置，將管理決策由經驗導向轉為數據驅動。",
        "建構數位產線與資安防禦網：結合 ISO 27001 主導稽核員專業，全面審查與重構軟體服務及生產製程的合規流程，成功落實數位產線資料防護，達成「零資安外洩」的卓越營運指標。",
        "敏捷流程再造 (BPR) 與效能躍升：導入敏捷專案管理 (Agile) 思維，打破部門穀倉效應，重新設計跨部門協作機制。成功將專案交付週期（Lead Time）大幅縮短 30%，同時提升交付準確率與整體組織的營運敏捷度。"
      ]
    },
    {
      "company": "芙瑞醫療器材 / 廣州藍鼎",
      "title": "行政與業務專案經理 (經營管理主管)",
      "period": "2014/10 – 仍在職",
      "highlights": [
        "跨國營運統籌與供應鏈合規：全面執掌財務、採購、倉儲與行政後勤體系。熟稔 ISO 13485 醫療品質管理標準，主導對接全球前十大醫療巨頭之嚴苛品質驗收，確保跨國供應鏈 100% 達成國際合規要求。",
        "組織架構重塑與風險控管：針對跨國企業擴張需求，重新設計組織架構與營運 SOP。透過導入嚴謹的內部稽核機制與 KPI 績效體系，確保跨國團隊在快速擴張中保持穩定，同時將行政與法遵風險降至最低。",
        "推動流程再造與效能提升：發起並執行跨職能業務流程再造 (BPR)，優化跨部門協作斷層，成功縮短營運週轉時間，顯著提升企業整體交付效率與獲利能力。"
      ]
    },
    {
      "company": "光宇醫療儀器股份有限公司",
      "title": "業務專案特助 (總經理幕僚)",
      "period": "2012/10 – 2014/6",
      "highlights": [
        "專案生命週期治理與品質把關：嚴格控管從產品設計到量產交付的全生命週期。確保所有交付物皆符合醫療器材產業最高規格之品質標準，有效控管專案時程與成本風險。",
        "國際大廠合規談判與戰略決策：針對全球頂尖客戶之交易條件與 ISO 13485 規範進行深度合規性初評，協助最高決策層擬定精準的商業談判策略與回應方案。",
        "跨領域衝突協調與資源整合：作為總經理核心幕僚，負責處理跨部門之利益衝突與溝通障礙。透過高效的利害關係人管理，成功打造高凝聚力與高產出的跨部門專案團隊。"
      ]
    }
  ]
};
