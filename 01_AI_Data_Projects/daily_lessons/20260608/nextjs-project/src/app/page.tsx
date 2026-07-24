"use client";

import React, { useState, useEffect } from "react";
import { BookOpen, Award, ArrowRight, Printer, Sparkles, HelpCircle } from "lucide-react";
import LinearRegressionPlayground from "@/components/LinearRegressionPlayground";
import LogisticRegressionPlayground from "@/components/LogisticRegressionPlayground";
import DecisionTreePlayground from "@/components/DecisionTreePlayground";
import RandomForestPlayground from "@/components/RandomForestPlayground";
import SVMPlayground from "@/components/SVMPlayground";
import KNNPlayground from "@/components/KNNPlayground";
import NaiveBayesPlayground from "@/components/NaiveBayesPlayground";
import KMeansPlayground from "@/components/KMeansPlayground";
import PCAPlayground from "@/components/PCAPlayground";
import FaceApiPlayground from "@/components/FaceApiPlayground";
import AiAssistant from "@/components/AiAssistant";
import AiChatbot from "@/components/AiChatbot";

export default function Home() {
  const [activeSection, setActiveSection] = useState<string>("intro");
  const [activeTab, setActiveTab] = useState<string>("all");

  const sections = [
    { id: "intro", title: "📌 機器學習三大範式", category: "intro" },
    { id: "phase1", title: "📈 第一階段：數值與分類", category: "numbers" },
    { id: "algo1", title: "1. 線性迴歸 (Linear)", category: "numbers" },
    { id: "algo2", title: "2. 邏輯迴歸 (Logistic)", category: "labels" },
    { id: "algo3", title: "3. 決策樹 (Decision Tree)", category: "labels" },
    { id: "algo4", title: "4. 隨機森林 (Random Forest)", category: "labels" },
    { id: "phase2", title: "📐 第二階段：空間與幾何", category: "labels" },
    { id: "algo5", title: "5. 支援向量機 (SVM)", category: "labels" },
    { id: "algo6", title: "6. K-最近鄰 (KNN)", category: "labels" },
    { id: "algo7", title: "7. 單純貝氏 (Naive Bayes)", category: "labels" },
    { id: "phase3", title: "🧩 第三階段：非監督探索", category: "clustering" },
    { id: "algo8", title: "8. K-Means 分群", category: "clustering" },
    { id: "algo9", title: "9. 主成分分析 (PCA)", category: "features" },
    { id: "phase4", title: "🧠 第四階段：神經網路", category: "deep" },
    { id: "algo10", title: "10. 類神經網路 (Deep)", category: "deep" },
    { id: "matrix", title: "📊 演算法綜合矩陣", category: "all" },
  ];

  // Scrollspy logic to automatically update active sidebar item on scroll
  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY + 200;

      for (const section of sections) {
        const el = document.getElementById(section.id);
        if (el) {
          const top = el.offsetTop;
          const height = el.offsetHeight;
          if (scrollPosition >= top && scrollPosition < top + height) {
            setActiveSection(section.id);
            break;
          }
        }
      }
    };

    window.addEventListener("scroll", handleScroll);
    return () => {
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  const handlePrint = () => {
    window.print();
  };

  const handleSidebarClick = (id: string) => {
    setActiveSection(id);
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  // Filter sections by CRISP-DM tabs
  const filteredSections = sections.filter((s) => {
    if (activeTab === "all") return true;
    if (activeTab === "numbers" && (s.category === "numbers" || s.id === "intro" || s.id === "matrix")) return true;
    if (activeTab === "labels" && (s.category === "labels" || s.id === "intro" || s.id === "matrix")) return true;
    if (activeTab === "clustering" && (s.category === "clustering" || s.id === "intro" || s.id === "matrix")) return true;
    if (activeTab === "features" && (s.category === "features" || s.id === "intro" || s.id === "matrix")) return true;
    return false;
  });

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-emerald-500/30 selection:text-emerald-400">
      
      {/* Sidebar Navigation */}
      <aside className="w-80 bg-slate-900 border-r border-slate-800 fixed top-0 bottom-0 left-0 p-6 overflow-y-auto hidden lg:block z-35 no-print shadow-2xl">
        <div className="mb-8 border-b border-emerald-500/30 pb-4">
          <h2 className="text-xl font-black tracking-wider text-white flex items-center gap-2">
            <BookOpen className="text-emerald-400" /> ML 演算法導覽
          </h2>
          <span className="text-[10px] uppercase font-bold tracking-widest text-slate-500 block mt-1">
            NCHU AI Training 互動教材
          </span>
        </div>

        <nav className="space-y-1">
          {sections.map((item) => {
            const isPhase = item.id.startsWith("phase") || item.id === "intro" || item.id === "matrix";
            const isActive = activeSection === item.id;

            return (
              <button
                key={item.id}
                onClick={() => handleSidebarClick(item.id)}
                className={`w-full text-left py-2 px-3 rounded-xl text-xs font-semibold transition duration-150 flex items-center justify-between ${
                  isPhase
                    ? "text-slate-400 mt-4 bg-slate-950/30 font-bold border-l-2 border-emerald-500/20"
                    : isActive
                    ? "bg-emerald-600 text-white shadow-lg shadow-emerald-950/20 scale-[1.02]"
                    : "text-slate-400 hover:bg-slate-800 hover:text-white"
                }`}
              >
                <span>{item.title}</span>
                {isActive && !isPhase && <ArrowRight size={12} className="text-white" />}
              </button>
            );
          })}
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 lg:ml-80 p-6 md:p-10 max-w-5xl mx-auto print-container">
        
        {/* Hero Banner */}
        <header className="relative bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8 shadow-2xl mb-10 overflow-hidden print-header">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-500/10 via-transparent to-transparent pointer-events-none" />
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative z-10">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-widest text-indigo-400 block mb-1">
                NCHU AI TRAINING班 專屬互動教材
              </span>
              <h1 className="text-3xl md:text-4xl font-extrabold text-white tracking-wide leading-tight">
                十大機器學習演算法：全方位動態學習報告
              </h1>
              <p className="text-slate-400 text-xs md:text-sm mt-2 max-w-xl leading-relaxed">
                結合 client-side <strong>Face API 臉部表情偵測</strong> 與互動式數學沙盒，分析你的讀書專注力與困惑度，由 AI 助教為你動態解說演算法精髓！
              </p>
            </div>
            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl text-xs transition duration-150 no-print shadow-lg shadow-emerald-950/30"
            >
              <Printer size={14} /> 一鍵導出 PDF / 列印
            </button>
          </div>
        </header>

        {/* CRISP-DM Filter Tabs */}
        <section className="mb-10 no-print">
          <h3 className="text-xs font-bold uppercase tracking-widest text-indigo-400 mb-3 flex items-center gap-2">
            <span className="w-1.5 h-3 bg-indigo-500 rounded-full"></span> 實戰任務快速篩選器 (CRISP-DM 專題型態)
          </h3>
          <div className="flex flex-wrap gap-2">
            {[
              { id: "all", label: "🌐 顯示全部 10 大", desc: "完整教材" },
              { id: "numbers", label: "🔢 預測連續數值", desc: "迴歸 (Regression)" },
              { id: "labels", label: "🏷️ 分類標籤預測", desc: "分類 (Classification)" },
              { id: "clustering", label: "🧲 盲測自動分群", desc: "分群 (Clustering)" },
              { id: "features", label: "🧪 特徵工程瘦身", desc: "降維 (Dimension)" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-4 rounded-xl text-xs transition flex flex-col items-center justify-center border ${
                  activeTab === tab.id
                    ? "bg-indigo-600 text-white border-indigo-400/20 shadow-lg shadow-indigo-950/20"
                    : "bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-850 hover:text-white"
                }`}
              >
                <span className="font-bold">{tab.label}</span>
                <span className="text-[9px] opacity-60 mt-0.5">{tab.desc}</span>
              </button>
            ))}
          </div>
        </section>

        {/* Core content sections */}
        <div className="space-y-12">
          
          {/* Introduction */}
          <article id="intro" className="bg-slate-900/40 border border-slate-900 rounded-2xl p-6 md:p-8 space-y-4">
            <h2 className="text-xl md:text-2xl font-bold text-white border-b border-slate-800 pb-3 flex items-center gap-2">
              📌 機器學習的核心範式 (Core Paradigms)
            </h2>
            <p className="text-slate-300 text-sm leading-relaxed text-justify">
              機器學習（Machine Learning, ML）是現代數據科學與人工智慧發展的基石。其本質在於開發出能從過往經驗（歷史數據）中自我修正、學習規律的演算法，而無須依賴工程師寫死（Hard-coded）的邏輯規則。在進入各個演算法深度探討前，我們必須清晰界定以下三大核心學習架構：
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
              <div className="bg-slate-900 border border-slate-800/80 p-4 rounded-xl space-y-2">
                <h4 className="text-blue-400 font-bold text-sm">1. 監督式學習 (Supervised)</h4>
                <p className="text-slate-400 text-xs leading-relaxed">資料庫中同時包含輸入特徵與標籤 (答案)。尋找映射函數，預測連續變數的迴歸任務，與預測離散類別的分類任務。</p>
              </div>
              <div className="bg-slate-900 border border-slate-800/80 p-4 rounded-xl space-y-2">
                <h4 className="text-purple-400 font-bold text-sm">2. 非監督式學習 (Unsupervised)</h4>
                <p className="text-slate-400 text-xs leading-relaxed">資料不具備標籤，模型自主探索結構。主要用於客戶特徵的「分群任務」與降低維度複雜度的「降維任務」。</p>
              </div>
              <div className="bg-slate-900 border border-slate-800/80 p-4 rounded-xl space-y-2">
                <h4 className="text-emerald-400 font-bold text-sm">3. 強化學習 (Reinforcement)</h4>
                <p className="text-slate-400 text-xs leading-relaxed">智能體 (Agent) 與環境互動，透過獲取即時的獎勵或懲罰機制，逐步迭代出長期的最優決策鏈。</p>
              </div>
            </div>
          </article>

          {/* Phase 1 */}
          {(activeTab === "all" || activeTab === "numbers" || activeTab === "labels") && (
            <section id="phase1" className="space-y-8">
              <h2 className="text-xl md:text-2xl font-bold text-white border-b border-slate-800 pb-3">
                📈 第一階段：數值預測與基礎分類 (Predictive Models)
              </h2>

              {/* 1. Linear Regression */}
              {(activeTab === "all" || activeTab === "numbers") && (
                <article id="algo1" className="bg-slate-900/20 border border-slate-850 rounded-2xl p-6 space-y-4">
                  <div className="flex justify-between items-start">
                    <h3 className="text-lg font-bold text-blue-400 flex items-center gap-2">
                      1. 線性迴歸 (Linear Regression)
                    </h3>
                    <span className="px-2.5 py-0.5 bg-blue-500/10 text-blue-400 text-[10px] font-bold rounded-full border border-blue-500/20">監督式</span>
                  </div>
                  <p className="text-slate-350 text-xs leading-relaxed text-justify">
                    線性迴歸是歷史最悠久、同時也是產業界用來建立基礎建模（Baseline Model）的首選工具。其基本假設為特徵與預測目標之間存在連續的線性映射關係，並透過最小化殘差平方和 (OLS) 來尋找最佳擬合參數。
                  </p>
                  <div className="bg-slate-950 border border-slate-850 p-3 rounded-xl font-mono text-xs text-blue-400 font-bold">
                    數學模型：Y = β₀ + β₁X₁ + β₂X₂ + ... + ε
                  </div>

                  <div className="no-print">
                    <LinearRegressionPlayground />
                  </div>

                  <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl space-y-2">
                    <h5 className="text-xs font-bold text-white">💡 實務應用案例：房地產自動估價系統</h5>
                    <p className="text-slate-400 text-xs leading-relaxed">
                      利用房屋的建坪、屋齡、公設比等多元特徵作為自變數 X，歷史實價登錄金額作為應變數 Y。透過多元線性迴歸模型，系統可在新物件上架的一瞬間給予客觀的合理市價估算。
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-emerald-950/20 border border-emerald-900/30 p-3 rounded-xl">
                      <span className="text-emerald-400 text-xs font-bold block">✓ 優點 (Pros)</span>
                      <p className="text-slate-450 text-[11px] mt-1">計算速度快，對大型數據集的即時預測表現出色，且各特徵係數具有強烈的業務解釋性。</p>
                    </div>
                    <div className="bg-rose-950/20 border border-rose-900/30 p-3 rounded-xl">
                      <span className="text-rose-450 text-xs font-bold block">✗ 缺點 (Cons)</span>
                      <p className="text-slate-450 text-[11px] mt-1">容易受極端異常值 (Outliers) 干擾，且無法捕捉現實世界中複雜的非線性關係。</p>
                    </div>
                  </div>
                </article>
              )}

              {/* 2. Logistic Regression */}
              {(activeTab === "all" || activeTab === "labels") && (
                <article id="algo2" className="bg-slate-900/20 border border-slate-850 rounded-2xl p-6 space-y-4">
                  <div className="flex justify-between items-start">
                    <h3 className="text-lg font-bold text-emerald-400 flex items-center gap-2">
                      2. 邏輯迴歸 (Logistic Regression)
                    </h3>
                    <span className="px-2.5 py-0.5 bg-blue-500/10 text-blue-400 text-[10px] font-bold rounded-full border border-blue-500/20">監督式</span>
                  </div>
                  <p className="text-slate-350 text-xs leading-relaxed text-justify">
                    雖然名為迴歸，但邏輯迴歸實質上為二元分類系統的核心骨幹。它將線性迴歸的連續預測值，透過 Sigmoid 函數投射到 0 到 1 之間的機率區間，以劃分出清晰的分類邊界。
                  </p>
                  <div className="bg-slate-950 border border-slate-850 p-3 rounded-xl font-mono text-xs text-emerald-400 font-bold">
                    Sigmoid 函數：P(Y=1|X) = 1 / (1 + e^-(wX + b))
                  </div>

                  <div className="no-print">
                    <LogisticRegressionPlayground />
                  </div>

                  <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl space-y-2">
                    <h5 className="text-xs font-bold text-white">💡 實務應用案例：信用卡欺詐與信用违約預測</h5>
                    <p className="text-slate-400 text-xs leading-relaxed">
                      分析交易金額、交易地點、刷卡頻率等特徵，輸出 0 到 1 之間的數值代表欺詐的機率。銀行得藉此即時發出阻斷訊號。
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-emerald-950/20 border border-emerald-900/30 p-3 rounded-xl">
                      <span className="text-emerald-400 text-xs font-bold block">✓ 優點 (Pros)</span>
                      <p className="text-slate-450 text-[11px] mt-1">輸出具有明確的機率物理意義，便於配合特徵權重進行業務決策與風險評估。</p>
                    </div>
                    <div className="bg-rose-950/20 border border-rose-900/30 p-3 rounded-xl">
                      <span className="text-rose-450 text-xs font-bold block">✗ 缺點 (Cons)</span>
                      <p className="text-slate-450 text-[11px] mt-1">其本質為線性邊界分割，在處理複雜、高度非線性交互作用的資料時表現欠佳。</p>
                    </div>
                  </div>
                </article>
              )}

              {/* 3. Decision Tree */}
              {(activeTab === "all" || activeTab === "labels") && (
                <article id="algo3" className="bg-slate-900/20 border border-slate-850 rounded-2xl p-6 space-y-4">
                  <div className="flex justify-between items-start">
                    <h3 className="text-lg font-bold text-purple-400 flex items-center gap-2">
                      3. 決策樹 (Decision Tree)
                    </h3>
                    <span className="px-2.5 py-0.5 bg-blue-500/10 text-blue-400 text-[10px] font-bold rounded-full border border-blue-500/20">監督式</span>
                  </div>
                  <p className="text-slate-350 text-xs leading-relaxed text-justify">
                    決策樹運用訊息增益（如不純度 Gini）作為指標，像做心理測驗般建立一連串條件分支篩選。其結構完全透明，是最經典的「白箱」演算法。
                  </p>
                  <div className="bg-slate-950 border border-slate-850 p-3 rounded-xl font-mono text-xs text-purple-400 font-bold">
                    不純度計算 (Gini Index)：Gini(D) = 1 - ∑ p_i^2
                  </div>

                  <div className="no-print">
                    <DecisionTreePlayground />
                  </div>

                  <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl space-y-2">
                    <h5 className="text-xs font-bold text-white">💡 實務應用案例：銀行核貸信用審查系統</h5>
                    <p className="text-slate-400 text-xs leading-relaxed">
                      「年收入是否大於 100 萬？」➡️「是」➡️「是否有債務拖欠？」➡️「否」➡️「核發貸款」。決策樹的規則能被稽核與法遵部門輕易理解並導入系統。
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-emerald-950/20 border border-emerald-900/30 p-3 rounded-xl">
                      <span className="text-emerald-400 text-xs font-bold block">✓ 優點 (Pros)</span>
                      <p className="text-slate-450 text-[11px] mt-1">不需對特徵欄位做繁瑣的標準化處理，規則可視化強，解釋性極佳。</p>
                    </div>
                    <div className="bg-rose-950/20 border border-rose-900/30 p-3 rounded-xl">
                      <span className="text-rose-450 text-xs font-bold block">✗ 缺點 (Cons)</span>
                      <p className="text-slate-450 text-[11px] mt-1">樹木容易生長過深，導致模型死背特徵（過擬合），且對微小的訓練資料變動極為敏感。</p>
                    </div>
                  </div>
                </article>
              )}

              {/* 4. Random Forest */}
              {(activeTab === "all" || activeTab === "labels") && (
                <article id="algo4" className="bg-slate-900/20 border border-slate-850 rounded-2xl p-6 space-y-4">
                  <div className="flex justify-between items-start">
                    <h3 className="text-lg font-bold text-indigo-400 flex items-center gap-2">
                      4. 隨機森林 (Random Forest)
                    </h3>
                    <span className="px-2.5 py-0.5 bg-blue-500/10 text-blue-400 text-[10px] font-bold rounded-full border border-blue-500/20">監督式</span>
                  </div>
                  <p className="text-slate-350 text-xs leading-relaxed text-justify">
                    隨機森林是集成學習 (Ensemble) 的經典作。它隨機抽取數據樣本和特徵，建立數百棵獨立的決策樹進行多數決投票，大幅降低了單棵樹容易過擬合的缺點。
                  </p>
                  <div className="bg-slate-950 border border-slate-850 p-3 rounded-xl font-mono text-xs text-indigo-400 font-bold">
                    {"集成多數決 (Ensemble Voting): y = mode{ T_1(x), T_2(x), ..., T_B(x) }"}
                  </div>

                  <div className="no-print">
                    <RandomForestPlayground />
                  </div>

                  <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl space-y-2">
                    <h5 className="text-xs font-bold text-white">💡 實務應用案例：電商顧客流失預測</h5>
                    <p className="text-slate-400 text-xs leading-relaxed">
                      結合用戶點擊流、消費金額、活躍天數等數十種複雜特徵，預測用戶是否即將流失，並輸出特徵重要性評估，協助營運團隊找出核心流失因素。
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-emerald-950/20 border border-emerald-900/30 p-3 rounded-xl">
                      <span className="text-emerald-400 text-xs font-bold block">✓ 優點 (Pros)</span>
                      <p className="text-slate-450 text-[11px] mt-1">泛化能力極強，能有效避免過擬合，且能直接評估每個特徵對預測目標的重要性。</p>
                    </div>
                    <div className="bg-rose-950/20 border border-rose-900/30 p-3 rounded-xl">
                      <span className="text-rose-450 text-xs font-bold block">✗ 缺點 (Cons)</span>
                      <p className="text-slate-450 text-[11px] mt-1">由於包含大量樹木，計算與儲存資源消耗較大，且難以用單一規則簡單解釋（黑箱傾向）。</p>
                    </div>
                  </div>
                </article>
              )}
            </section>
          )}

          {/* Phase 2 */}
          {(activeTab === "all" || activeTab === "labels") && (
            <section id="phase2" className="space-y-8">
              <h2 className="text-xl md:text-2xl font-bold text-white border-b border-slate-800 pb-3">
                📐 第二階段：空間與幾何 (Spatial & Geometric Models)
              </h2>

              {/* 5. SVM */}
              <article id="algo5" className="bg-slate-900/20 border border-slate-850 rounded-2xl p-6 space-y-4">
                <div className="flex justify-between items-start">
                  <h3 className="text-lg font-bold text-cyan-400 flex items-center gap-2">
                    5. 支援向量機 (Support Vector Machine, SVM)
                  </h3>
                  <span className="px-2.5 py-0.5 bg-blue-500/10 text-blue-400 text-[10px] font-bold rounded-full border border-blue-500/20">監督式</span>
                </div>
                <p className="text-slate-350 text-xs leading-relaxed text-justify">
                  SVM 的目標是尋找一個具有最大安全邊際 (Margin) 的超平面來切分資料。若資料混雜，SVM 可以使用核技巧 (Kernel Trick) 將資料拉高至高維度，實現完美分類。
                </p>
                <div className="bg-slate-950 border border-slate-850 p-3 rounded-xl font-mono text-xs text-cyan-400 font-bold">
                  最大化間距：Max Margin = 2 / ||w|| 滿足 y_i(wᵀx_i + b) ≥ 1
                </div>

                <div className="no-print">
                  <SVMPlayground />
                </div>

                <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl space-y-2">
                  <h5 className="text-xs font-bold text-white">💡 實務應用案例：醫學影像組織特徵診斷與分類</h5>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    在基因特徵與醫學磁振造影 (MRI) 中，資料維度極高但樣本數相對有限。SVM 在此類小樣本高維度分類任務中具有極佳的數學穩定度。
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-emerald-950/20 border border-emerald-900/30 p-3 rounded-xl">
                    <span className="text-emerald-400 text-xs font-bold block">✓ 優點 (Pros)</span>
                    <p className="text-slate-450 text-[11px] mt-1">在高維空間中依然非常有效，且有核技巧可處理複雜的非線性關係，能避免局部極值。</p>
                  </div>
                  <div className="bg-rose-950/20 border border-rose-900/30 p-3 rounded-xl">
                    <span className="text-rose-450 text-xs font-bold block">✗ 缺點 (Cons)</span>
                    <p className="text-slate-450 text-[11px] mt-1">對大規模樣本的計算開銷十分龐大，且核函數及參數的調校極為困難。</p>
                  </div>
                </div>
              </article>

              {/* 6. KNN */}
              <article id="algo6" className="bg-slate-900/20 border border-slate-850 rounded-2xl p-6 space-y-4">
                <div className="flex justify-between items-start">
                  <h3 className="text-lg font-bold text-pink-400 flex items-center gap-2">
                    6. K-最近鄰 (K-Nearest Neighbors, KNN)
                  </h3>
                  <span className="px-2.5 py-0.5 bg-blue-500/10 text-blue-400 text-[10px] font-bold rounded-full border border-blue-500/20">監督式</span>
                </div>
                <p className="text-slate-350 text-xs leading-relaxed text-justify">
                  KNN 貫徹「物以類聚」的觀念。新資料進來時，不需前期模型訓練，直接計算與所有點的距離，看最近的 K 個鄰居誰佔多數，就決定自己屬於哪一類。
                </p>
                <div className="bg-slate-950 border border-slate-850 p-3 rounded-xl font-mono text-xs text-pink-400 font-bold">
                  歐氏距離：d(p, q) = √ ∑ (p_i - q_i)^2
                </div>

                <div className="no-print">
                  <KNNPlayground />
                </div>

                <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl space-y-2">
                  <h5 className="text-xs font-bold text-white">💡 實務應用案例：影音平台個性化相似推薦</h5>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    將用戶喜好向量化，找出特徵空間中最鄰近的 K 個相似用戶，並將他們喜愛的影音內容推薦給目標用戶。
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-emerald-950/20 border border-emerald-900/30 p-3 rounded-xl">
                    <span className="text-emerald-400 text-xs font-bold block">✓ 優點 (Pros)</span>
                    <p className="text-slate-450 text-[11px] mt-1">極其簡單直觀，完全不需要前期訓練時間 (Lazy Learner)，非常適合在線即時插入新點。</p>
                  </div>
                  <div className="bg-rose-950/20 border border-rose-900/30 p-3 rounded-xl">
                    <span className="text-rose-450 text-xs font-bold block">✗ 缺點 (Cons)</span>
                    <p className="text-slate-450 text-[11px] mt-1">預測時需要計算與所有樣本的距離，計算量極大，且在高維空間中容易受到維度災難影響。</p>
                  </div>
                </div>
              </article>

              {/* 7. Naive Bayes */}
              <article id="algo7" className="bg-slate-900/20 border border-slate-850 rounded-2xl p-6 space-y-4">
                <div className="flex justify-between items-start">
                  <h3 className="text-lg font-bold text-amber-500 flex items-center gap-2">
                    7. 單純貝氏 (Naive Bayes)
                  </h3>
                  <span className="px-2.5 py-0.5 bg-blue-500/10 text-blue-400 text-[10px] font-bold rounded-full border border-blue-500/20">監督式</span>
                </div>
                <p className="text-slate-350 text-xs leading-relaxed text-justify">
                  單純貝氏基於貝氏定理，並「單純」地假設所有特徵在給定類別下皆互相獨立。它能在大規模文本中，光速計算出分類的後驗機率分佈，效率極佳。
                </p>
                <div className="bg-slate-950 border border-slate-850 p-3 rounded-xl font-mono text-xs text-amber-500 font-bold">
                  貝氏定理：P(C|X) = [P(X|C) · P(C)] / P(X)
                </div>

                <div className="no-print">
                  <NaiveBayesPlayground />
                </div>

                <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl space-y-2">
                  <h5 className="text-xs font-bold text-white">💡 實務應用案例：電子郵件系統中的垃圾郵件過濾</h5>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    計算特定關鍵詞（如「免費」、「中獎」）在垃圾郵件中出現的機率。一旦乘積後的後驗機率超過閥值，系統便自動將信件歸類為垃圾信。
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-emerald-950/20 border border-emerald-900/30 p-3 rounded-xl">
                    <span className="text-emerald-400 text-xs font-bold block">✓ 優點 (Pros)</span>
                    <p className="text-slate-450 text-[11px] mt-1">計算開銷極小，能以極快速度處理海量文本數據，且非常適合小規模數據的建模。</p>
                  </div>
                  <div className="bg-rose-950/20 border border-rose-900/30 p-3 rounded-xl">
                    <span className="text-rose-450 text-xs font-bold block">✗ 缺點 (Cons)</span>
                    <p className="text-slate-450 text-[11px] mt-1">其前提假設「特徵之間完全獨立」在真實世界中幾乎不成立，限制了特定複雜場景下的精度。</p>
                  </div>
                </div>
              </article>
            </section>
          )}

          {/* Phase 3 */}
          {(activeTab === "all" || activeTab === "clustering" || activeTab === "features") && (
            <section id="phase3" className="space-y-8">
              <h2 className="text-xl md:text-2xl font-bold text-white border-b border-slate-800 pb-3">
                🧩 第三階段：非監督探索與特徵工程 (Unsupervised & Feature Engineering)
              </h2>

              {/* 8. K-Means */}
              {(activeTab === "all" || activeTab === "clustering") && (
                <article id="algo8" className="bg-slate-900/20 border border-slate-850 rounded-2xl p-6 space-y-4">
                  <div className="flex justify-between items-start">
                    <h3 className="text-lg font-bold text-fuchsia-400 flex items-center gap-2">
                      8. K-Means 分群 (K-Means Clustering)
                    </h3>
                    <span className="px-2.5 py-0.5 bg-fuchsia-500/10 text-fuchsia-400 text-[10px] font-bold rounded-full border border-fuchsia-500/20">非監督式</span>
                  </div>
                  <p className="text-slate-350 text-xs leading-relaxed text-justify">
                    在沒有任何答案標籤的狀況下，K-Means 藉由設定群體數 K，讓電腦不斷更新群心，利用歐氏距離最小化，將數據自動聚集、黏合為 K 個大類別。
                  </p>
                  <div className="bg-slate-950 border border-slate-850 p-3 rounded-xl font-mono text-xs text-fuchsia-400 font-bold">
                    {"最小化內誤差 (Objective): J = ∑_{i=1}^K ∑_{x ∈ S_i} ||x - μ_i||^2"}
                  </div>

                  <div className="no-print">
                    <KMeansPlayground />
                  </div>

                  <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl space-y-2">
                    <h5 className="text-xs font-bold text-white">💡 實務應用案例：零售業的客群劃分與精準行銷</h5>
                    <p className="text-slate-400 text-xs leading-relaxed">
                      分析消費金額、頻率、喜好類別，自動將百萬客戶劃分成 3 到 5 個聚類（例如高消費高頻率、低消費高敏感等），幫助營運團隊投放不同的促銷方案。
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-emerald-950/20 border border-emerald-900/30 p-3 rounded-xl">
                      <span className="text-emerald-400 text-xs font-bold block">✓ 優點 (Pros)</span>
                      <p className="text-slate-450 text-[11px] mt-1">原理簡單，演算法收斂速度極快，能作為大規模無標籤資料的優秀探索工具。</p>
                    </div>
                    <div className="bg-rose-950/20 border border-rose-900/30 p-3 rounded-xl">
                      <span className="text-rose-450 text-xs font-bold block">✗ 缺點 (Cons)</span>
                      <p className="text-slate-450 text-[11px] mt-1">必須預先指定 K 值，且對異常值 (Outliers) 以及群心的初始隨機位置非常敏感。</p>
                    </div>
                  </div>
                </article>
              )}

              {/* 9. PCA */}
              {(activeTab === "all" || activeTab === "features") && (
                <article id="algo9" className="bg-slate-900/20 border border-slate-850 rounded-2xl p-6 space-y-4">
                  <div className="flex justify-between items-start">
                    <h3 className="text-lg font-bold text-teal-400 flex items-center gap-2">
                      9. 主成分分析 (Principal Component Analysis, PCA)
                    </h3>
                    <span className="px-2.5 py-0.5 bg-fuchsia-500/10 text-fuchsia-400 text-[10px] font-bold rounded-full border border-fuchsia-500/20">非監督式</span>
                  </div>
                  <p className="text-slate-350 text-xs leading-relaxed text-justify">
                    PCA 就像數據的精華濃縮相機。它將高維度、具高度相關性的眾多欄位特徵，壓扁成少數幾個彼此正交的主成分 (PCs)，並保留數據中最大變異數（代表最高資訊量）。
                  </p>
                  <div className="bg-slate-950 border border-slate-850 p-3 rounded-xl font-mono text-xs text-teal-400 font-bold">
                    特徵值方程式：Σ v = λ v (Σ 為協方差矩陣, v 為特徵向量, λ 為特徵值)
                  </div>

                  <div className="no-print">
                    <PCAPlayground />
                  </div>

                  <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl space-y-2">
                    <h5 className="text-xs font-bold text-white">💡 實務應用案例：機器視覺臉部特徵降維與圖像壓縮</h5>
                    <p className="text-slate-400 text-xs leading-relaxed">
                      在高維度的圖像像素中，運用 PCA 擷取前幾個主成分（特徵臉 Eigenfaces），既能保留主要面部輪廓特徵，又能將後續模型的運算負載縮減 90% 以上。
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-emerald-950/20 border border-emerald-900/30 p-3 rounded-xl">
                      <span className="text-emerald-400 text-xs font-bold block">✓ 優點 (Pros)</span>
                      <p className="text-slate-450 text-[11px] mt-1">消除變數間的多重共線性，節省運算成本與儲存空間，避免遭遇高維度災難。</p>
                    </div>
                    <div className="bg-rose-950/20 border border-rose-900/30 p-3 rounded-xl">
                      <span className="text-rose-450 text-xs font-bold block">✗ 缺點 (Cons)</span>
                      <p className="text-slate-450 text-[11px] mt-1">轉換後的主成分是原始維度的線性組合，難以對應回實務物理意義，且可能丟失細微的重要資訊。</p>
                    </div>
                  </div>
                </article>
              )}
            </section>
          )}

          {/* Phase 4 */}
          {(activeTab === "all") && (
            <section id="phase4" className="space-y-8">
              <h2 className="text-xl md:text-2xl font-bold text-white border-b border-slate-800 pb-3">
                🧠 第四階段：神經網路與深度表徵 (Deep Representation)
              </h2>

              {/* 10. Neural Network / Deep Learning */}
              <article id="algo10" className="bg-slate-900/20 border border-slate-850 rounded-2xl p-6 space-y-4">
                <div className="flex justify-between items-start">
                  <h3 className="text-lg font-bold text-rose-400 flex items-center gap-2">
                    10. 類神經網路 / 深度學習 (Neural Network / Deep Learning)
                  </h3>
                  <span className="px-2.5 py-0.5 bg-indigo-500/10 text-indigo-400 text-[10px] font-bold rounded-full border border-indigo-500/20">混合/多層</span>
                </div>
                <p className="text-slate-350 text-xs leading-relaxed text-justify">
                  類神經網路模擬人類大腦的突觸連接結構。它將大量邏輯迴歸像積木一樣疊加成多個隱藏層 (Hidden Layers)，利用反向傳播演算法自動提取高維特徵與非線性擬合。
                </p>
                <div className="bg-slate-950 border border-slate-850 p-3 rounded-xl font-mono text-xs text-rose-400 font-bold">
                  人工神經元模型：y = f( ∑ w_i x_i + b ) (f 為非線性激活函數，如 ReLU)
                </div>

                <div className="no-print">
                  <FaceApiPlayground />
                </div>

                <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl space-y-2">
                  <h5 className="text-xs font-bold text-white">💡 實務應用案例：Face API 臉部地標定位與表情辨識</h5>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    在前端（瀏覽器）環境中，透過卷積神經網路 (CNN) 即時定位相機畫面中人臉的 68 個地標特徵點，並運算判定目前的表情概率，實現智慧情緒適應學習。
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-emerald-950/20 border border-emerald-900/30 p-3 rounded-xl">
                    <span className="text-emerald-400 text-xs font-bold block">✓ 優點 (Pros)</span>
                    <p className="text-slate-450 text-[11px] mt-1">模型表徵能力極限，能自動做特徵工程與提取，擅長擬合極端複雜非線性模型 (如圖像、語音)。</p>
                  </div>
                  <div className="bg-rose-950/20 border border-rose-900/30 p-3 rounded-xl">
                    <span className="text-rose-450 text-xs font-bold block">✗ 缺點 (Cons)</span>
                    <p className="text-slate-450 text-[11px] mt-1">是極致的「黑箱模型」，幾乎無法給出白箱決策鏈，且需極大數據集與強大算力 (GPU) 支援。</p>
                  </div>
                </div>
              </article>
            </section>
          )}

          {/* Algorithm Matrix */}
          {(activeTab === "all") && (
            <article id="matrix" className="bg-slate-900/40 border border-slate-900 rounded-2xl p-6 md:p-8 space-y-4">
              <h2 className="text-xl md:text-2xl font-bold text-white border-b border-slate-800 pb-3 flex items-center gap-2">
                📊 演算法綜合矩陣 (Summary Matrix)
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-950 border-b border-slate-800 text-slate-400 font-bold">
                      <th className="py-3 px-3">演算法名稱</th>
                      <th className="py-3 px-3">學習型態</th>
                      <th className="py-3 px-3">解釋度</th>
                      <th className="py-3 px-3">運算開銷</th>
                      <th className="py-3 px-3">核心主要用途</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-850">
                    <tr>
                      <td className="py-2.5 px-3 font-semibold text-blue-400">1. 線性迴歸</td>
                      <td className="py-2.5 px-3 text-slate-300">監督式</td>
                      <td className="py-2.5 px-3 text-emerald-400 font-bold">極高 (白箱)</td>
                      <td className="py-2.5 px-3 text-slate-400">極低</td>
                      <td className="py-2.5 px-3 text-slate-400">預測連續數值量化</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-semibold text-emerald-400">2. 邏輯迴歸</td>
                      <td className="py-2.5 px-3 text-slate-300">監督式</td>
                      <td className="py-2.5 px-3 text-emerald-400 font-bold">高 (白箱)</td>
                      <td className="py-2.5 px-3 text-slate-400">極低</td>
                      <td className="py-2.5 px-3 text-slate-400">二分類機率估計</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-semibold text-purple-400">3. 決策樹</td>
                      <td className="py-2.5 px-3 text-slate-300">監督式</td>
                      <td className="py-2.5 px-3 text-emerald-400 font-bold">極高 (白箱)</td>
                      <td className="py-2.5 px-3 text-slate-400">低</td>
                      <td className="py-2.5 px-3 text-slate-400">條件分支決策分類</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-semibold text-indigo-400">4. 隨機森林</td>
                      <td className="py-2.5 px-3 text-slate-300">監督式</td>
                      <td className="py-2.5 px-3 text-amber-500 font-bold">中等</td>
                      <td className="py-2.5 px-3 text-slate-400">中等</td>
                      <td className="py-2.5 px-3 text-slate-400">高強度特徵分类</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-semibold text-cyan-400">5. SVM</td>
                      <td className="py-2.5 px-3 text-slate-300">監督式</td>
                      <td className="py-2.5 px-3 text-rose-500 font-bold">低 (黑箱)</td>
                      <td className="py-2.5 px-3 text-slate-400">高</td>
                      <td className="py-2.5 px-3 text-slate-400">高維複雜邊界切分</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-semibold text-pink-400">6. KNN</td>
                      <td className="py-2.5 px-3 text-slate-300">監督式</td>
                      <td className="py-2.5 px-3 text-emerald-400 font-bold">極高 (白箱)</td>
                      <td className="py-2.5 px-3 text-slate-400">高 (預測階段)</td>
                      <td className="py-2.5 px-3 text-slate-400">鄰近比對相似推荐</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-semibold text-amber-500">7. 單純貝氏</td>
                      <td className="py-2.5 px-3 text-slate-300">監督式</td>
                      <td className="py-2.5 px-3 text-emerald-400 font-bold">高 (白箱)</td>
                      <td className="py-2.5 px-3 text-slate-400">極低</td>
                      <td className="py-2.5 px-3 text-slate-400">高速垃圾郵件過濾</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-semibold text-fuchsia-400">8. K-Means</td>
                      <td className="py-2.5 px-3 text-slate-300">非監督式</td>
                      <td className="py-2.5 px-3 text-emerald-400 font-bold">高 (白箱)</td>
                      <td className="py-2.5 px-3 text-slate-400">低</td>
                      <td className="py-2.5 px-3 text-slate-400">未知群組自動凝聚分流</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-semibold text-teal-400">9. PCA</td>
                      <td className="py-2.5 px-3 text-slate-300">非監督式</td>
                      <td className="py-2.5 px-3 text-rose-500 font-bold">低 (黑箱)</td>
                      <td className="py-2.5 px-3 text-slate-400">中等</td>
                      <td className="py-2.5 px-3 text-slate-400">高維特徵提取與投影瘦身</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-semibold text-rose-400">10. 深度學習</td>
                      <td className="py-2.5 px-3 text-slate-300">混合/多層</td>
                      <td className="py-2.5 px-3 text-rose-500 font-bold">極低 (極限黑箱)</td>
                      <td className="py-2.5 px-3 text-slate-400">極高</td>
                      <td className="py-2.5 px-3 text-slate-400">非線性高維圖像語音提取</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </article>
          )}

        </div>

        {/* Footer */}
        <footer className="mt-12 border-t border-slate-900 pt-6 text-center text-slate-500 text-xs pb-12">
          <p>© 2026 NCHU AI Training Program. All rights reserved.</p>
        </footer>

      </main>

      {/* Floating Emotion Adaptive Learning Assistant */}
      <AiAssistant activeSection={activeSection} />

      {/* Floating Chatbot Assistant */}
      <AiChatbot />

    </div>
  );
}
