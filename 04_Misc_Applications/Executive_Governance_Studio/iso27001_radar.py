"""ISO/IEC 27001:2022 資安治理成熟度雷達圖.

Annex A's 4 themes / 93 controls are consolidated into 8 strategic axes
(control counts sum to 93: Organizational 37 · People 8 · Physical 14 · Technological 34).
Each axis is scored on a 0–5 maturity scale (CMMI-style) and compared with an
audit benchmark profile. Remediation priority = maturity gap x control weight.
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

# axis -> (Annex A references, control count, default score, remediation playbook)
AXES = {
    "治理與政策":      ("A.5.1–5.8, A.5.31–5.37", 15, 3.0,
                       ("建立資安治理委員會與年度管理審查，更新適用性聲明 (SoA) 與法規遵循清冊", "中", "CISO / 法遵", "管理審查完成率 100%")),
    "資產與資訊管理":   ("A.5.9–5.14",              6, 2.5,
                       ("建置 CMDB 資產清冊、資訊分級標示與資料傳輸規範", "中", "IT 營運", "資產盤點覆蓋率 ≥ 95%")),
    "身分與存取控制":   ("A.5.15–5.18, A.8.2–8.5",   8, 2.0,
                       ("全面導入 MFA、特權帳號管理 (PAM) 與每季存取權限覆核", "中", "IAM 團隊", "特權帳號 MFA 覆蓋率 100%")),
    "供應商與雲端安全": ("A.5.19–5.23",              5, 2.0,
                       ("建立供應商資安分級、合約資安條款與雲端服務安全評估 (A.5.23)", "低", "採購 / 資安", "關鍵供應商評鑑完成率 100%")),
    "事件管理與營運持續": ("A.5.24–5.30",            7, 2.5,
                       ("制定事件應變劇本、威脅情資 (A.5.7) 串接與年度 BCP / DR 演練", "中", "SOC / BCM", "MTTR 下降 30%、演練 ≥ 1 次/年")),
    "人員安全":         ("A.6.1–6.8",                8, 3.0,
                       ("新進 / 離職資安作業標準化、年度社交工程演練與資安意識訓練", "低", "人資 / 資安", "釣魚點擊率 < 5%")),
    "實體與環境安全":   ("A.7.1–7.14",              14, 3.5,
                       ("機房門禁與監控整合、實體安全監控 (A.7.4) 與桌面淨空政策稽核", "低", "總務 / 設施", "門禁異常 100% 追蹤結案")),
    "技術營運與開發安全": ("A.8.1, A.8.6–8.34",       30, 2.0,
                       ("弱點管理 SLA、集中化日誌 (SIEM)、安全開發生命週期 (SSDLC) 與備份還原測試", "高", "IT / 研發", "高風險弱點 30 日內修補率 ≥ 95%")),
}
assert sum(v[1] for v in AXES.values()) == 93

BENCHMARKS = {
    "驗證就緒基準 (Certification-Ready)": 3.0,
    "金融 / 關鍵基礎設施 (Regulated Sector)": 3.5,
    "國際標竿 (Best-in-Class)": 4.0,
}

MATURITY_LEVELS = "0 不存在 · 1 臨時性 · 2 可重複 · 3 已定義 · 4 已量化管理 · 5 持續優化"

inject_theme()
hero(
    "ISO/IEC 27001:2022 · Annex A 93 Controls",
    "🎯 ISO 27001:2022 資安治理成熟度雷達圖",
    "將附件 A 四大主題、93 項控制措施濃縮為 8 大策略軸向，對照稽核基準即時產出董事會等級的成熟度雷達圖與前三大改善行動矩陣。",
)

# ---------------------------------------------------------------- Inputs
section("① 評估設定")
s1, s2 = st.columns([2, 1])
with s1:
    org = st.text_input("受評組織 / 範圍", value="集團總部 ISMS 驗證範圍", key="iso_org")
with s2:
    bench_name = st.selectbox("稽核基準輪廓", list(BENCHMARKS.keys()), key="iso_bench")
bench = BENCHMARKS[bench_name]

section("② 八大軸向成熟度評分")
st.caption(f"評分尺度：{MATURITY_LEVELS}")
scores = {}
cols = st.columns(4)
for i, (axis, (refs, count, default, _)) in enumerate(AXES.items()):
    with cols[i % 4]:
        scores[axis] = st.slider(axis, 0.0, 5.0, default, 0.5, key=f"iso_{i}",
                                 help=f"{refs}｜{count} 項控制措施")

# ---------------------------------------------------------------- Metrics
weighted = sum(scores[a] * AXES[a][1] for a in AXES) / 93
readiness = sum(min(scores[a] / bench, 1.0) * AXES[a][1] for a in AXES) / 93 * 100
below_controls = sum(AXES[a][1] for a in AXES if scores[a] < bench)
critical_axes = [a for a in AXES if scores[a] < 2.0]

section("③ 治理成熟度總覽")
m1, m2, m3, m4 = st.columns(4)
m1.metric("加權成熟度", f"{weighted:.2f} / 5", f"基準 {bench:.1f}", delta_color="off")
m2.metric("驗證就緒度", f"{readiness:.0f}%")
m3.metric("低於基準之控制措施", f"{below_controls} / 93", delta_color="off")
m4.metric("關鍵弱項 (< 2.0)", f"{len(critical_axes)} 軸", "、".join(critical_axes) or "無", delta_color="off")

if critical_axes or readiness < 70:
    banner("🔴 尚未具備驗證條件", f"{org} 存在重大不符合 (Major NC) 風險，建議先完成前三大改善行動後再安排第一階段稽核。", RED)
elif readiness < 90:
    banner("🟠 有條件就緒", "預期可能出現輕微不符合 (Minor NC)；建議於 90 天內完成改善並進行內部稽核。", AMBER)
else:
    banner("🟢 驗證就緒", "各軸向均達基準，可安排驗證機構進行第一 / 二階段稽核。", TEAL)

# ---------------------------------------------------------------- Radar
axes = list(AXES.keys())
radar = go.Figure()
radar.add_trace(go.Scatterpolar(
    r=[bench] * len(axes) + [bench], theta=axes + [axes[0]], name=f"稽核基準 ({bench:.1f})",
    line=dict(color=GOLD, dash="dash", width=2), fill="toself", fillcolor="rgba(197,168,128,0.08)",
))
radar.add_trace(go.Scatterpolar(
    r=[scores[a] for a in axes] + [scores[axes[0]]], theta=axes + [axes[0]], name="企業現況分數",
    line=dict(color="#4FA8D1", width=3), fill="toself", fillcolor="rgba(79,168,209,0.30)",
    marker=dict(size=8),
))
radar.update_layout(
    title=f"{org}｜Current Enterprise Score vs Audit Benchmark",
    polar=dict(bgcolor="rgba(0,0,0,0)",
               radialaxis=dict(range=[0, 5], tickvals=[1, 2, 3, 4, 5], gridcolor="rgba(128,128,128,0.4)"),
               angularaxis=dict(gridcolor="rgba(128,128,128,0.4)")),
    legend=dict(orientation="h", y=-0.08), height=560, **PLOTLY_LAYOUT,
)
st.plotly_chart(radar, width="stretch")

# ---------------------------------------------------------------- Remediation matrix
section("④ 稽核員建議：前三大優先改善行動矩陣")
rows = []
for a in axes:
    refs, count, _, (action, effort, owner, kpi) = AXES[a]
    gap = max(0.0, bench - scores[a])
    rows.append(dict(軸向=a, 附件A條款=refs, 控制數=count, 現況=scores[a], 落差=gap,
                     優先分數=round(gap * count, 2), 改善行動=action, 投入程度=effort, 權責單位=owner, 九十日KPI=kpi))
df = pd.DataFrame(rows).sort_values(["優先分數", "落差"], ascending=False)
top3 = df[df["落差"] > 0].head(3)

if top3.empty:
    st.success("✅ 所有軸向皆已達到稽核基準，建議聚焦持續改善 (Clause 10) 與下一級標竿。")
else:
    cards = st.columns(len(top3))
    for col, (rank, row) in zip(cards, enumerate(top3.itertuples(index=False), start=1)):
        with col, st.container(border=True):
            st.markdown(f"### #{rank} {row.軸向}")
            st.markdown(f"**落差** {row.落差:.1f}｜**控制數** {row.控制數}｜**投入** {row.投入程度}")
            st.markdown(f"🛠️ {row.改善行動}")
            st.caption(f"👤 {row.權責單位}　📏 {row.九十日KPI}　📖 {row.附件A條款}")

with st.expander("📋 完整軸向落差分析表"):
    st.dataframe(df, hide_index=True, width="stretch")
    st.download_button("⬇️ 下載 CSV", df.to_csv(index=False).encode("utf-8-sig"),
                       file_name="iso27001_maturity_gap.csv", mime="text/csv")

disclaimer("本雷達圖為管理層級自評工具；正式驗證須依 ISO/IEC 27001:2022 條文 4–10 及附件 A，"
           "並由經認證之驗證機構執行稽核。附件 A 控制措施之適用性應以組織之適用性聲明 (SoA) 為準。")
