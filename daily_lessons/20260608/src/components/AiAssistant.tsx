"use client";

import React, { useState, useEffect } from "react";
import { Sparkles, HelpCircle, CheckCircle, XCircle } from "lucide-react";
import confetti from "canvas-confetti";

interface AiAssistantProps {
  activeSection: string; // The ID of the section the user is currently reading (e.g. "algo1", "algo2"...)
}

interface Analogy {
  title: string;
  text: string;
}

interface Quiz {
  question: string;
  options: string[];
  answerIdx: number;
  explanation: string;
}

export default function AiAssistant({ activeSection }: AiAssistantProps) {
  const [emotionHistory, setEmotionHistory] = useState<string[]>([]);
  const [status, setStatus] = useState<"focused" | "confused" | "confident">("focused");
  const [showMessage, setShowMessage] = useState<boolean>(false);
  const [messageType, setMessageType] = useState<"analogy" | "quiz" | "idle">("idle");
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [quizAnswered, setQuizAnswered] = useState<boolean>(false);

  // Define analogies and quizzes for all 10 algorithms
  const analogies: { [key: string]: Analogy } = {
    intro: {
      title: "機器學習三大範式",
      text: "這就像教小狗：『監督式』是你丟飛盤告訴牠『這是飛盤』；『非監督式』是把一堆玩具丟給牠，讓牠自己去把球分一堆、骨頭分一堆；『強化學習』則是做對了給骨頭，做錯了罰站，讓牠在嘗試中學會最聰明的做法！",
    },
    algo1: {
      title: "線性迴歸 (Linear Regression)",
      text: "這就像去菜市場買蘋果，1顆蘋果10元，買越多元就越貴。線性迴歸就是在這中間點與點之間畫出一條最直的公式線，幫你預測買 20 顆蘋果大概要花多少錢！",
    },
    algo2: {
      title: "邏輯迴歸 (Logistic Regression)",
      text: "這就像是銀行的『防詐騙警報』，它的輸出只有兩種：『是詐騙 (1)』或『正常交易 (0)』。它把所有刷卡特徵化為分數，並用 Sigmoid 壓縮在 0 到 1 之間，代表是詐騙的機率。",
    },
    algo3: {
      title: "決策樹 (Decision Tree)",
      text: "這就像做心理測驗：第一關『年滿18歲？』是 ➡️ 第二關『有駕照？』是 ➡️ 可以合法開車。這就是一連串『是與否』的條件分支篩選！",
    },
    algo4: {
      title: "隨機森林 (Random Forest)",
      text: "這就像多數決！如果只有一個醫生（決策樹）可能會診斷錯誤（過擬合），但如果請 100 位醫生各自診斷並進行多數決投票，集體智慧的判斷就會比單一醫生準確很多！",
    },
    algo5: {
      title: "支援向量機 (SVM)",
      text: "這就像在兩軍交戰時畫出一條『楚河漢界』。而且這條邊界線必須距離兩邊最前線的士兵（支援向量）都盡可能地遠，安全距離（Margin）最大，兩國才最不容易起衝突！",
    },
    algo6: {
      title: "K-最近鄰 (KNN)",
      text: "俗話說『物以類聚』。新搬來的鄰居是什麼人，只要看他家周圍最近的 3 個（K=3）鄰居是做什麼的。如果 2 個是工程師，1 個是醫生，那麼他大概也是工程師！",
    },
    algo7: {
      title: "單純貝氏 (Naive Bayes)",
      text: "這就像是一個『垃圾郵件過濾器』。它單純地假設信件中出現的詞彙（例如『中獎』、『免費』）都是完全獨立無關的，然後把這些詞同時在垃圾信出現的機率乘起來，快速判斷是不是垃圾信！",
    },
    algo8: {
      title: "K-Means 分群",
      text: "這就像班上要分組報告。大家隨機選出 3 個組長（中心點），其他人自動靠攏到距離自己最近的組長身邊。接著組長再往組員的中間移動，大家反覆調整，直到分出最完美的 3 大組！",
    },
    algo9: {
      title: "主成分分析 (PCA)",
      text: "這就像幫 3D 的雕像拍一張 2D 的照片。雖然少了一個維度，但只要角度選得好，還是能完全看出雕像的樣子。PCA 就是幫你找出那個『最能保留立體特徵的拍照角度』！",
    },
    algo10: {
      title: "類神經網路 (Deep Learning)",
      text: "這就像是把幾百個邏輯迴歸像樂高積木一樣疊成很多層！低層學習線條，中層學習形狀，高層學習人臉（就像此時此刻 Face API 正在努力辨識你的表情一樣）！",
    },
    matrix: {
      title: "演算法綜合矩陣",
      text: "這就像是你出門時的工具箱：釘釘子用鐵鎚（線性迴歸），鎖螺絲用螺絲起子（決策樹）。沒有最強的工具，只有最適合當前資料任務的演算法！",
    },
  };

  const quizzes: { [key: string]: Quiz } = {
    intro: {
      question: "K-Means 客戶分群屬於以下哪一種機器學習範式？",
      options: ["監督式學習", "非監督式學習", "強化學習"],
      answerIdx: 1,
      explanation: "K-Means 分群不需要歷史標籤（標準答案），而是由演算法自主探索資料點的距離結構進行分群，因此屬於『非監督式學習』。",
    },
    algo1: {
      question: "線性迴歸主要用來解決以下哪一種預測任務？",
      options: ["預測連續型數值 (如房價)", "預測二元類別 (如是否購買)", "將資料分成未知群體"],
      answerIdx: 0,
      explanation: "線性迴歸是用來預測連續變數（如房價、溫度、良率）的迴歸任務。分類任務通常使用邏輯迴歸或決策樹。",
    },
    algo2: {
      question: "邏輯迴歸中，常用來將輸出數值壓縮到 0 與 1 之間的函數是？",
      options: ["ReLU 函數", "Sigmoid 函數", "Tanh 函數"],
      answerIdx: 1,
      explanation: "Sigmoid 函數（S型曲線）能將任何實數輸入壓縮映射到 [0, 1] 區間，正好代表分類機率。",
    },
    algo3: {
      question: "決策樹演算法在選擇分割特徵時，主要基於以下哪種概念？",
      options: ["計算歐氏距離", "最小化不純度 (如 Gini 指標)", "尋找最大邊際"],
      answerIdx: 1,
      explanation: "決策樹藉由計算基尼係數 (Gini) 或訊息熵 (Entropy) 的降低程度（訊息增益），尋找能讓子節點數據最純淨的特徵進行切割。",
    },
    algo4: {
      question: "隨機森林藉由建立多棵獨立決策樹進行多數決，主要解決了決策樹的什麼缺點？",
      options: ["計算速度太慢", "容易過擬合 (Overfitting) 死背資料", "無法處理非線性資料"],
      answerIdx: 1,
      explanation: "單棵決策樹很容易生長過深，從而完美死背訓練集（過擬合）。隨機森林透過隨機隨機抽樣，大幅降低了模型的變異數並防止過擬合。",
    },
    algo5: {
      question: "支援向量機 (SVM) 尋找的最佳超平面，是基於以下哪個指標的最大化？",
      options: ["分類正確率", "楚河漢界邊際 (Margin)", "梯度下降斜率"],
      answerIdx: 1,
      explanation: "SVM 的核心目標是極大化決策邊界到最近樣本點（支援向量）的『邊際距離 (Margin)』，以取得最強的模型泛化能力。",
    },
    algo6: {
      question: "如果 KNN 的 K 值設定得極小 (例如 K=1)，模型會偏向如何？",
      options: ["極容易受到局部噪點干擾，導致模型過於複雜且不穩定", "模型非常平滑穩定，對雜訊不敏感", "模型退化為線性分類"],
      answerIdx: 0,
      explanation: "當 K=1 時，模型僅看最近的一個點。如果該點是異常雜訊，就會直接被錯誤分類，因此模型會非常敏感且不穩定。",
    },
    algo7: {
      question: "單純貝氏演算法中的『單純 (Naive)』是指什麼假設？",
      options: ["假設所有特徵特徵都是無用的", "假設所有特徵在給定類別下皆互相獨立、互不關聯", "假設數據呈完美的線性分布"],
      answerIdx: 1,
      explanation: "『單純』指強烈假設所有屬性特徵彼此獨立無關。雖然在現實中極少成立，但能大幅簡化機率乘積計算，且在垃圾郵件分類等任務上表現優異。",
    },
    algo8: {
      question: "K-Means 分群中，K 值的決定代表了什麼？",
      options: ["迭代的次數", "最終要分出的群體個數", "計算距離時的鄰居個數"],
      answerIdx: 1,
      explanation: "K-Means 中的 K 代表最終希望將所有樣本聚類分成的群組總數，需要使用者在初始時手動設定。",
    },
    algo9: {
      question: "PCA (主成分分析) 進行特徵降維時，核心是尋找投影後擁有最大什麼的軸向？",
      options: ["平均數 (Mean)", "變異數 (Variance, 資訊保留量)", "斜率 (Slope)"],
      answerIdx: 1,
      explanation: "PCA 旨在尋找投影後變異數（分散程度）最大的方向，因為變異數越大，代表保留的原始資訊特徵越豐富。",
    },
    algo10: {
      question: "類神經網路 (Deep Learning) 之所以強大，主要因為它能透過多層堆疊自動完成什麼？",
      options: ["資料清理", "特徵提取與特徵工程 (Representation Learning)", "資料庫備份"],
      answerIdx: 1,
      explanation: "深度學習能透過層層網路的組合，從小特徵（線條）自動拼湊成大特徵（眼睛、臉部），無須人類專家手動設計特徵欄位，此稱為表徵學習。",
    },
    matrix: {
      question: "機器學習實務上選擇演算法時，最核心的黃金法則是什麼？",
      options: ["一律使用最複雜的深度學習", "根據奧卡姆剃刀，簡單好解釋且效果足夠的優先 (沒有免費午餐定理)", "挑選名字聽起來最酷的"],
      answerIdx: 1,
      explanation: "根據『沒有免費午餐定理』，沒有任何一個演算法能在所有問題上都表現最好。一般實務上偏好簡單好解釋、運算快且效果能滿足業務目標的模型。",
    },
  };

  useEffect(() => {
    // Reset message state when switching sections
    setShowMessage(false);
    setMessageType("idle");
    setSelectedOption(null);
    setQuizAnswered(false);
    setStatus("focused");
  }, [activeSection]);

  useEffect(() => {
    const handleEmotion = (e: Event) => {
      const customEvent = e as CustomEvent;
      const { emotion } = customEvent.detail;

      // Keep rolling queue of last 6 readings
      setEmotionHistory((prev) => {
        const next = [...prev, emotion].slice(-6);

        // Analyze rolling history
        // If 3 or more of the last 6 are 'sad' (which represents struggle/confusion) or 'angry' / 'fearful'
        const confusionCount = next.filter((em) => em === "sad" || em === "angry" || em === "fearful").length;
        const happinessCount = next.filter((em) => em === "happy" || em === "surprised").length;

        if (confusionCount >= 2 && status !== "confused" && !showMessage) {
          setStatus("confused");
          setMessageType("analogy");
          setShowMessage(true);
        } else if (happinessCount >= 2 && status !== "confident" && !showMessage) {
          setStatus("confident");
          setMessageType("quiz");
          setShowMessage(true);
        }

        return next;
      });
    };

    window.addEventListener("faceapi-emotion", handleEmotion);
    return () => {
      window.removeEventListener("faceapi-emotion", handleEmotion);
    };
  }, [status, showMessage]);

  const handleOptionClick = (idx: number) => {
    if (quizAnswered) return;
    setSelectedOption(idx);
    setQuizAnswered(true);

    const currentQuiz = quizzes[activeSection] || quizzes["intro"];
    if (idx === currentQuiz.answerIdx) {
      // Trigger confetti celebration
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.8 },
      });
    }
  };

  const currentAnalogy = analogies[activeSection] || analogies["intro"];
  const currentQuiz = quizzes[activeSection] || quizzes["intro"];

  return (
    <div className="fixed bottom-6 left-6 z-40 max-w-sm w-full transition-all duration-300 no-print">
      {showMessage && (
        <div className="bg-slate-900/90 backdrop-blur-md border border-slate-700/80 rounded-2xl p-5 shadow-2xl relative overflow-hidden animate-slide-up">
          {/* Top glowing ambient gradient */}
          <div
            className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${
              messageType === "analogy" ? "from-cyan-500 to-blue-500" : "from-emerald-500 to-teal-500"
            }`}
          />

          <div className="flex items-start gap-3">
            <div
              className={`p-2 rounded-xl flex items-center justify-center shrink-0 ${
                messageType === "analogy" ? "bg-cyan-500/10 text-cyan-400" : "bg-emerald-500/10 text-emerald-400"
              }`}
            >
              {messageType === "analogy" ? <Sparkles size={20} /> : <HelpCircle size={20} />}
            </div>

            <div className="flex-1 space-y-2">
              <h5 className="text-white font-bold text-sm tracking-wide">
                {messageType === "analogy" ? "💡 AI 助教的生活化比喻" : "❓ AI 助教的小小挑戰"}
              </h5>

              {messageType === "analogy" ? (
                <div className="space-y-2.5">
                  <p className="text-slate-200 text-xs font-semibold">{currentAnalogy.title}</p>
                  <p className="text-slate-350 text-xs leading-relaxed leading-normal">{currentAnalogy.text}</p>
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-slate-200 text-xs font-semibold leading-relaxed">
                    {currentQuiz.question}
                  </p>
                  <div className="space-y-1.5">
                    {currentQuiz.options.map((opt, idx) => {
                      let btnStyle = "bg-slate-950 border border-slate-800 hover:bg-slate-850 text-slate-300";
                      
                      if (quizAnswered) {
                        if (idx === currentQuiz.answerIdx) {
                          btnStyle = "bg-emerald-500/20 border-emerald-500 text-emerald-400 font-bold";
                        } else if (idx === selectedOption) {
                          btnStyle = "bg-rose-500/20 border-rose-500 text-rose-400 font-bold";
                        } else {
                          btnStyle = "bg-slate-950 border border-slate-800 text-slate-500 opacity-60";
                        }
                      }

                      return (
                        <button
                          key={idx}
                          disabled={quizAnswered}
                          onClick={() => handleOptionClick(idx)}
                          className={`w-full text-left py-2 px-3 rounded-lg text-xs transition duration-150 flex items-center justify-between ${btnStyle}`}
                        >
                          <span>{opt}</span>
                          {quizAnswered && idx === currentQuiz.answerIdx && <CheckCircle size={12} className="text-emerald-400 shrink-0" />}
                          {quizAnswered && idx === selectedOption && idx !== currentQuiz.answerIdx && <XCircle size={12} className="text-rose-400 shrink-0" />}
                        </button>
                      );
                    })}
                  </div>

                  {quizAnswered && (
                    <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-850">
                      <p className="text-[10px] text-slate-450 leading-relaxed">
                        <strong className="text-slate-300 font-bold">解析：</strong>
                        {currentQuiz.explanation}
                      </p>
                    </div>
                  )}
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                {messageType === "analogy" && (
                  <button
                    onClick={() => {
                      setMessageType("quiz");
                      setSelectedOption(null);
                      setQuizAnswered(false);
                    }}
                    className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-[10px] rounded-lg transition"
                  >
                    挑戰測驗
                  </button>
                )}
                <button
                  onClick={() => setShowMessage(false)}
                  className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-400 text-[10px] font-bold rounded-lg transition"
                >
                  關閉
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Floating button toggle if closed */}
      {!showMessage && cameraActiveHistory() && (
        <button
          onClick={() => {
            setMessageType(status === "confused" ? "analogy" : "quiz");
            setShowMessage(true);
          }}
          className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold p-3.5 rounded-full shadow-2xl flex items-center justify-center transition transform hover:scale-105 active:scale-95 border border-emerald-400/20"
        >
          <Sparkles size={20} className="animate-pulse" />
        </button>
      )}
    </div>
  );

  function cameraActiveHistory() {
    return emotionHistory.length > 0;
  }
}
