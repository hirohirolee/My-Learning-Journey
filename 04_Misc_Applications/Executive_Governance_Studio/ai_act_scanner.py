"""EU AI Act 企業人工智慧風險分級掃描器.

Implements a simplified decision tree of Regulation (EU) 2024/1689:

    Art. 5  prohibited practices         -> Unacceptable risk  (Art. 99(3): €35M / 7%)
    Annex I safety component / Annex III -> High risk          (Art. 99(4): €15M / 3%)
        (Art. 6(3) derogation unless the system performs profiling)
    Art. 50 transparency triggers        -> Limited / transparency risk (€15M / 3%)
    otherwise                            -> Minimal risk (voluntary codes of conduct)

SMEs / start-ups: the LOWER of the fixed amount and the turnover percentage (Art. 99(6)).
"""

import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from egs_theme import (  # noqa: E402
    AMBER, GOLD, PLOTLY_LAYOUT, RED, TEAL,
    banner, disclaimer, hero, inject_theme, section,
)

PROHIBITED = {
    "p_subliminal": "運用潛意識、操縱或欺騙性技術，實質扭曲人類行為並造成重大傷害 (Art. 5(1)(a))",
    "p_vulnerable": "利用年齡、身心障礙或社經弱勢等脆弱性扭曲行為 (Art. 5(1)(b))",
    "p_scoring":    "社會評分：依社會行為或人格特質評分並導致不利對待 (Art. 5(1)(c))",
    "p_policing":   "僅憑側寫或人格特質預測個人犯罪風險 (Art. 5(1)(d))",
    "p_scraping":   "無差別爬取網路或監視器影像以建立臉部辨識資料庫 (Art. 5(1)(e))",
    "p_emotion":    "於職場或教育場域進行情緒辨識（醫療 / 安全用途除外）(Art. 5(1)(f))",
    "p_biocat":     "以生物特徵推斷種族、政治傾向、宗教、性傾向等敏感屬性 (Art. 5(1)(g))",
    "p_rbi":        "執法目的於公共場所進行即時遠端生物特徵辨識 (Art. 5(1)(h))",
}

ANNEX_III = {
    "h_bio":      "生物特徵辨識 / 分類（非禁止範圍）",
    "h_infra":    "關鍵基礎設施安全元件（電網、供水、交通、數位基礎設施）",
    "h_edu":      "教育與職業訓練（入學、評分、考試監控）",
    "h_hr":       "就業與人力資源（招募篩選、升遷、解僱、績效監控）",
    "h_credit":   "基本私人 / 公共服務（信用評分、壽險健康險定價、社福資格）",
    "h_law":      "執法（證據可信度評估、再犯風險）",
    "h_migr":     "移民、庇護與邊境管理",
    "h_justice":  "司法與民主程序（判決輔助、影響選舉）",
}

TRANSPARENCY = {
    "t_chatbot":  "與自然人直接互動之 AI（聊天機器人、語音客服）",
    "t_genai":    "生成合成圖像、音訊、影片或文字內容（需機器可讀標記）",
    "t_deepfake": "產製深度偽造 (Deepfake) 內容",
    "t_emotion":  "情緒辨識或生物特徵分類系統（非禁止場域）之部署",
}

GAP_CHECKLIST = {
    "Art. 10 資料與資料治理": [
        "訓練 / 驗證 / 測試資料集具備書面化治理與來源紀錄",
        "已完成資料偏差 (bias) 檢測與緩解措施",
        "資料具相關性、代表性且盡可能無錯誤與完整",
    ],
    "Art. 11 技術文件": [
        "依附件 IV 編製技術文件並於上市前完成",
        "文件含系統架構、演算法邏輯、效能指標與限制",
        "建立技術文件版本控管與 10 年保存機制",
    ],
    "Art. 12 紀錄保存 (Logging)": [
        "系統自動記錄事件日誌，具全生命週期可追溯性",
        "日誌可識別風險情境與實質變更",
        "日誌保存期限至少 6 個月",
    ],
    "Art. 13 透明度與使用者資訊": [
        "提供部署者清楚之使用說明 (instructions for use)",
        "揭露準確度、穩健性指標與已知風險",
        "說明人類監督措施與輸出解讀方式",
    ],
    "Art. 14 人類監督": [
        "設計可由自然人有效監督之介面與停止機制",
        "監督人員具備理解系統能力與限制之訓練",
        "防範自動化偏誤 (automation bias) 之控制",
    ],
    "Art. 15 準確性、穩健性與資安": [
        "宣告並持續監測準確度指標",
        "具備錯誤、故障與不一致之韌性及備援",
        "防禦資料投毒、對抗樣本、模型竄改等 AI 特有攻擊",
    ],
}

PENALTY = {
    "prohibited":   (35_000_000, 0.07, "Art. 99(3)"),
    "high":         (15_000_000, 0.03, "Art. 99(4)"),
    "transparency": (15_000_000, 0.03, "Art. 99(4)"),
    "minimal":      (7_500_000,  0.01, "Art. 99(5) 提供不實資訊"),
}


def max_fine(tier: str, turnover_eur: float, sme: bool) -> float:
    fixed, pct, _ = PENALTY[tier]
    pct_amount = turnover_eur * pct
    return min(fixed, pct_amount) if sme else max(fixed, pct_amount)


inject_theme()
hero(
    "Regulation (EU) 2024/1689 · Risk-Based Classification",
    "🛡️ EU AI Act 企業人工智慧風險分級掃描器",
    "依歐盟人工智慧法風險金字塔，即時判定 AI 系統之風險等級、法定罰鍰曝險與 Art. 10–15 高風險義務落差，供 CIO / CDO 於立項前完成合規可行性評估。",
)

banner(
    "⚠️ 法定罰鍰警示：最高 €35,000,000 或全球年營業額 7%（取高者）",
    "違反 Art. 5 禁止性 AI 實務之罰則；其他義務違反最高 €15M / 3%，提供不實資訊最高 €7.5M / 1%。禁止條款自 2025-02-02 起適用。",
    RED,
)

# ---------------------------------------------------------------- Profile
section("① 系統與組織概況")
a1, a2, a3, a4 = st.columns([2, 1.3, 1.2, 1])
with a1:
    system_name = st.text_input("AI 系統名稱", value="智慧招募履歷篩選引擎", key="aia_name")
with a2:
    role = st.selectbox("組織角色", ["提供者 (Provider)", "部署者 (Deployer)", "進口商 / 經銷商"], key="aia_role")
with a3:
    turnover_m = st.number_input("全球年營業額 (€ 百萬)", min_value=0.0, value=800.0, step=50.0, key="aia_turnover")
with a4:
    sme = st.toggle("中小企業 / 新創", value=False, key="aia_sme")

tab1, tab2, tab3 = st.tabs(["🚫 Art. 5 禁止性實務", "⚠️ 高風險用途 (Annex I / III)", "👁️ Art. 50 透明度義務"])
with tab1:
    sel_prohibited = [k for k, label in PROHIBITED.items() if st.checkbox(label, key=f"aia_{k}")]
with tab2:
    annex_i = st.checkbox("屬附件 I 歐盟產品安全法規之安全元件（如醫療器材、機械、玩具、車輛）且須第三方符合性評鑑", key="aia_annex_i")
    sel_annex = [k for k, label in ANNEX_III.items() if st.checkbox(label, value=(k == "h_hr"), key=f"aia_{k}")]
    st.divider()
    derog = st.checkbox("Art. 6(3) 例外：僅執行狹窄程序性任務 / 改善已完成之人類活動結果，不構成重大風險", key="aia_derog")
    profiling = st.checkbox("系統對自然人進行側寫 (Profiling)", value=True, key="aia_profiling",
                            help="涉及側寫之附件 III 系統一律視為高風險，不得主張 Art. 6(3) 例外。")
with tab3:
    sel_transp = [k for k, label in TRANSPARENCY.items() if st.checkbox(label, key=f"aia_{k}")]

# ---------------------------------------------------------------- Classification
high_by_annex_iii = bool(sel_annex) and not (derog and not profiling)
if sel_prohibited:
    tier, label, color = "prohibited", "⛔ 不可接受風險 (Unacceptable Risk) — 禁止上市 / 使用", RED
    advice = "此系統落入 Art. 5 禁止性實務，必須立即停止開發、上市或使用，並啟動法務與董事會層級事件通報。"
elif annex_i or high_by_annex_iii:
    tier, label, color = "high", "🟠 高風險 (High-Risk AI System)", AMBER
    advice = "須於上市 / 投入使用前完成風險管理系統、符合性評鑑、CE 標示、歐盟資料庫登錄與上市後監測（Art. 9–17, 43, 49, 72）。"
elif sel_transp or (sel_annex and derog and not profiling):
    tier, label, color = "transparency", "🟡 有限風險 / 透明度義務 (Specific Transparency Risk)", GOLD
    advice = "須告知使用者正與 AI 互動、標記合成內容；若主張 Art. 6(3) 例外，應於上市前書面記錄評估並登錄。"
else:
    tier, label, color = "minimal", "🟢 極小風險 (Minimal Risk)", TEAL
    advice = "無強制性義務；建議採行自願性行為準則，並確保員工具備 AI 素養（Art. 4，自 2025-02-02 起適用）。"

fine = max_fine(tier, turnover_m * 1e6, sme)
fixed, pct, article = PENALTY[tier]

section("② 即時分級結果")
banner(f"{system_name}：{label}", advice, color)

k1, k2, k3 = st.columns(3)
k1.metric("風險等級", label.split(" ")[1] if " " in label else label)
k2.metric("最高罰鍰曝險", f"€{fine / 1e6:,.1f}M", f"{article}｜€{fixed / 1e6:.1f}M 或 {pct * 100:.0f}%{'（取低者）' if sme else '（取高者）'}", delta_color="off")
k3.metric("觸發條件數", f"{len(sel_prohibited) + len(sel_annex) + int(annex_i) + len(sel_transp)} 項", role, delta_color="off")

# ---------------------------------------------------------------- Gap checklist
section("③ 高風險義務落差檢核 (Art. 10–15)")
if tier != "high":
    st.caption("目前分級非高風險；以下檢核可作為自願性對標 (voluntary benchmarking) 使用。")

scores = {}
cols = st.columns(2)
for i, (article_name, items) in enumerate(GAP_CHECKLIST.items()):
    with cols[i % 2]:
        with st.container(border=True):
            st.markdown(f"**{article_name}**")
            done = sum(st.checkbox(item, key=f"aia_gap_{i}_{j}") for j, item in enumerate(items))
            scores[article_name] = done / len(items) * 100
            st.progress(scores[article_name] / 100, text=f"就緒度 {scores[article_name]:.0f}%")

overall = sum(scores.values()) / len(scores)
fig = go.Figure(go.Bar(
    x=list(scores.values()), y=list(scores.keys()), orientation="h",
    marker_color=[RED if v < 34 else AMBER if v < 67 else TEAL for v in scores.values()],
    text=[f"{v:.0f}%" for v in scores.values()], textposition="outside",
))
fig.update_layout(title=f"高風險義務整體就緒度：{overall:.0f}%", xaxis=dict(range=[0, 110], title="就緒度 (%)"),
                  yaxis=dict(autorange="reversed"), height=360, **PLOTLY_LAYOUT)
st.plotly_chart(fig, width="stretch")

gaps = pd.DataFrame(
    [(a, item) for i, (a, items) in enumerate(GAP_CHECKLIST.items())
     for j, item in enumerate(items) if not st.session_state.get(f"aia_gap_{i}_{j}")],
    columns=["條文", "待補強項目"],
)
with st.expander(f"📋 待補強項目清單（{len(gaps)} 項）", expanded=tier == "high" and len(gaps) > 0):
    st.dataframe(gaps, hide_index=True, width="stretch")
    st.download_button("⬇️ 下載落差清單 CSV", gaps.to_csv(index=False).encode("utf-8-sig"),
                       file_name="ai_act_gap_list.csv", mime="text/csv")

with st.expander("🗓️ 適用時程"):
    st.markdown(
        "- **2025-02-02**：Art. 5 禁止性實務、Art. 4 AI 素養\n"
        "- **2025-08-02**：通用目的 AI 模型 (GPAI) 義務、罰則章節\n"
        "- **2026-08-02**：附件 III 高風險系統義務、Art. 50 透明度義務\n"
        "- **2027-08-02**：附件 I 產品安全元件之高風險系統\n\n"
        "_歐盟執委會之 Digital Omnibus 提案可能調整高風險義務時程，請以最新官方公報為準。_"
    )

disclaimer("本掃描器為簡化之決策樹，僅供初步合規分級與內部溝通，不構成法律意見；正式判定請依法規全文、指引與專業法律顧問意見。")
