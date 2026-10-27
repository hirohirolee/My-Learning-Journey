"""EU CBAM 歐盟碳關稅財務衝擊試算引擎 (Carbon Border Adjustment Mechanism).

Definitive-period logic (2026+), simplified for executive scenario planning:

    SEE_counted        = direct + (indirect if sector counts indirect emissions)
    free_alloc_adj/t   = min(SEE_counted, EU benchmark x CBAM phase-in factor[year])
    certificates       = tonnage x (SEE_counted - free_alloc_adj)
    origin deduction   = carbon price effectively paid in origin (capped at ETS price)
    net liability      = certificates x ETS price - origin deduction  (floor 0)

All presets are ILLUSTRATIVE defaults; replace with verified installation data
(supplier communication template) before any filing or pricing decision.
"""

import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from egs_theme import (  # noqa: E402
    AMBER, BLUE, GOLD, PLOTLY_LAYOUT, RED, TEAL,
    banner, disclaimer, hero, inject_theme, section,
)

# Share of free allocation still granted under EU ETS (CBAM Art. 31 phase-out).
CBAM_FACTOR = {
    2026: 0.975, 2027: 0.950, 2028: 0.900, 2029: 0.775, 2030: 0.515,
    2031: 0.390, 2032: 0.265, 2033: 0.140, 2034: 0.000,
}

# Illustrative presets (tCO2e per tonne of product).
PRESETS = {
    "螺絲螺帽 / 扣件 (高爐鋼 BF-BOF)": dict(hs="7318.15", direct=2.05, indirect=0.38, benchmark=1.37, indirect_counted=False, fob=1450.0),
    "螺絲螺帽 / 扣件 (電爐鋼 EAF)":   dict(hs="7318.15", direct=0.55, indirect=0.42, benchmark=0.28, indirect_counted=False, fob=1500.0),
    "熱軋鋼捲 / 鋼材":                 dict(hs="7208.39", direct=1.95, indirect=0.30, benchmark=1.37, indirect_counted=False, fob=650.0),
    "未鍛軋鋁錠 (原生鋁)":             dict(hs="7601.10", direct=1.65, indirect=7.50, benchmark=1.46, indirect_counted=False, fob=2400.0),
    "水泥熟料 / 波特蘭水泥":           dict(hs="2523.29", direct=0.78, indirect=0.06, benchmark=0.69, indirect_counted=True,  fob=95.0),
    "氮肥 (尿素 / 氨)":               dict(hs="3102.10", direct=1.90, indirect=0.12, benchmark=1.57, indirect_counted=True,  fob=420.0),
    "氫氣":                           dict(hs="2804.10", direct=9.00, indirect=0.60, benchmark=6.84, indirect_counted=False, fob=3500.0),
    "自訂 (Custom)":                   dict(hs="",        direct=1.00, indirect=0.20, benchmark=0.80, indirect_counted=False, fob=1000.0),
}


def compute(tonnage, direct, indirect, indirect_counted, benchmark, year, ets, origin_price, origin_cov):
    see = direct + (indirect if indirect_counted else 0.0)
    factor = CBAM_FACTOR[year]
    free_per_t = min(see, benchmark * factor)
    gross_t = tonnage * see
    free_t = tonnage * free_per_t
    cert_t = max(0.0, gross_t - free_t)
    gross_cost = gross_t * ets
    free_cost = free_t * ets
    pre_deduction = cert_t * ets
    origin_ded = min(pre_deduction, min(origin_price, ets) * gross_t * origin_cov)
    net = max(0.0, pre_deduction - origin_ded)
    return dict(see=see, factor=factor, free_per_t=free_per_t, gross_t=gross_t, free_t=free_t,
                cert_t=cert_t, gross_cost=gross_cost, free_cost=free_cost,
                origin_ded=origin_ded, net=net, net_certs=net / ets if ets else 0.0)


inject_theme()
hero(
    "EU CBAM · Definitive Period 2026+",
    "⚖️ EU CBAM 歐盟碳關稅財務衝擊試算引擎",
    "依產品隱含排放量、EU ETS 免費配額遞減係數與原產國碳價抵減，量化出口歐盟之碳關稅財務曝險，供 CFO / CSO 進行定價與供應鏈決策。",
)

# ---------------------------------------------------------------- Inputs
section("① 產品與出口情境")
c1, c2, c3 = st.columns(3)
with c1:
    preset_name = st.selectbox("產業預設情境", list(PRESETS.keys()), key="cbam_preset")
    p = PRESETS[preset_name]
    hs_code = st.text_input("HS / CN 稅則號列", value=p["hs"], key=f"cbam_hs_{preset_name}")
with c2:
    tonnage = st.number_input("年出口量 (公噸)", min_value=0.0, value=5000.0, step=100.0, key="cbam_tonnage")
    fob = st.number_input("FOB 單價 (€/公噸)", min_value=1.0, value=p["fob"], step=10.0, key=f"cbam_fob_{preset_name}")
with c3:
    year = st.select_slider("申報年度", options=list(CBAM_FACTOR.keys()), value=2026, key="cbam_year")
    fx = st.number_input("匯率 (NT$ / €)", min_value=1.0, value=35.0, step=0.5, key="cbam_fx")

section("② 隱含排放量 (tCO₂e / 公噸產品)")
e1, e2, e3, e4 = st.columns(4)
with e1:
    direct = st.number_input("直接排放 (Direct)", min_value=0.0, value=p["direct"], step=0.05, format="%.2f", key=f"cbam_dir_{preset_name}")
with e2:
    indirect = st.number_input("間接排放 (Indirect, 外購電力)", min_value=0.0, value=p["indirect"], step=0.05, format="%.2f", key=f"cbam_ind_{preset_name}")
with e3:
    benchmark = st.number_input("EU ETS 產品基準值", min_value=0.0, value=p["benchmark"], step=0.01, format="%.2f", key=f"cbam_bm_{preset_name}",
                                help="用於計算免費配額調整額；正式值以執委會實施法規公告之 CBAM benchmark 為準。")
with e4:
    indirect_counted = st.toggle("間接排放納入計費", value=p["indirect_counted"], key=f"cbam_indc_{preset_name}",
                                 help="依 CBAM 附件 II：鋼鐵、鋁、氫僅計直接排放；水泥、肥料須計入間接排放。")

section("③ 碳價參數")
k1, k2, k3 = st.columns(3)
with k1:
    ets = st.number_input("EU ETS 碳價基準 (€/tCO₂e)", min_value=1.0, value=85.0, step=1.0, key="cbam_ets")
with k2:
    origin_price = st.number_input("原產國已付碳價 (€/tCO₂e)", min_value=0.0, value=8.5, step=0.5, key="cbam_origin",
                                   help="例：台灣碳費一般費率 NT$300/t ≈ €8.5/t（未計優惠費率）。抵減上限為 EU ETS 價格。")
with k3:
    origin_cov = st.slider("原產國碳價涵蓋比例", 0, 100, 60, step=5, format="%d%%", key="cbam_cov",
                           help="實際被課徵碳費之排放量佔產品隱含排放量比例（扣除免徵額、退費等）。") / 100.0

r = compute(tonnage, direct, indirect, indirect_counted, benchmark, year, ets, origin_price, origin_cov)
revenue = tonnage * fob
burden_pct = (r["net"] / revenue * 100) if revenue else 0.0

if tonnage < 50:
    st.info("ℹ️ 年進口量低於 50 公噸：依 2025 年 CBAM 簡化修正（Omnibus）之質量門檻，歐盟進口商可能豁免申報義務，請與進口商確認。")

# ---------------------------------------------------------------- KPIs
section("④ 財務曝險總覽")
m1, m2, m3, m4 = st.columns(4)
m1.metric("淨 CBAM 碳關稅負擔", f"€{r['net']:,.0f}", f"≈ NT${r['net'] * fx / 1e6:,.1f} 百萬", delta_color="off")
m2.metric("每公噸產品成本", f"€{r['net'] / tonnage if tonnage else 0:,.1f}", f"FOB 的 {burden_pct:.1f}%", delta_color="inverse")
m3.metric("需購 CBAM 憑證", f"{r['net_certs']:,.0f} 張", f"計費排放 {r['see']:.2f} tCO₂e/t", delta_color="off")
m4.metric("免費配額調整係數", f"{r['factor'] * 100:.1f}%", f"{year} 年", delta_color="off")

if burden_pct >= 10:
    banner("🔴 高度財務曝險", f"碳關稅已達營收 {burden_pct:.1f}%，將實質侵蝕毛利；建議啟動綠電 / 電爐轉換評估並重新議定歐盟報價條款。", RED)
elif burden_pct >= 3:
    banner("🟠 中度財務曝險", f"碳關稅約佔營收 {burden_pct:.1f}%，建議建立實際排放數據 (actual data) 取代預設值，以降低憑證採購量。", AMBER)
else:
    banner("🟢 可控曝險", f"碳關稅約佔營收 {burden_pct:.1f}%；請關注 2030 年後免費配額大幅退場之成本跳升。", TEAL)

# ---------------------------------------------------------------- Charts
g1, g2 = st.columns(2)
with g1:
    wf = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "total"],
        x=["隱含排放總成本", "免費配額調整", "原產國碳價抵減", "淨 CBAM 負擔"],
        y=[r["gross_cost"], -r["free_cost"], -r["origin_ded"], 0],
        text=[f"€{v:,.0f}" for v in (r["gross_cost"], -r["free_cost"], -r["origin_ded"], r["net"])],
        textposition="outside",
        connector=dict(line=dict(color="rgba(128,128,128,0.4)")),
        increasing=dict(marker=dict(color=RED)),
        decreasing=dict(marker=dict(color=TEAL)),
        totals=dict(marker=dict(color=GOLD)),
    ))
    wf.update_layout(title=f"{year} 年碳關稅成本瀑布圖 (€)", **PLOTLY_LAYOUT)
    st.plotly_chart(wf, width="stretch")

with g2:
    years = list(CBAM_FACTOR.keys())
    phase = [compute(tonnage, direct, indirect, indirect_counted, benchmark, y, ets, origin_price, origin_cov)["net"] for y in years]
    bar = go.Figure(go.Bar(
        x=[str(y) for y in years], y=phase,
        marker_color=[GOLD if y == year else BLUE for y in years],
        text=[f"€{v / 1e6:,.2f}M" for v in phase], textposition="outside",
    ))
    bar.update_layout(title="2026–2034 免費配額退場：年度淨負擔路徑 (€)", **PLOTLY_LAYOUT)
    st.plotly_chart(bar, width="stretch")

prices = list(range(50, 155, 5))
sens = go.Figure()
for y, color in ((year, GOLD), (2030, AMBER), (2034, RED)):
    sens.add_trace(go.Scatter(
        x=prices,
        y=[compute(tonnage, direct, indirect, indirect_counted, benchmark, y, px, origin_price, origin_cov)["net"] for px in prices],
        mode="lines+markers", name=f"{y} 年", line=dict(color=color, width=3),
    ))
sens.add_vline(x=ets, line_dash="dash", line_color="rgba(128,128,128,0.4)", annotation_text=f"基準 €{ets:.0f}")
sens.update_layout(title="EU ETS 碳價敏感度分析 (€50–€150 / tCO₂e)", xaxis_title="EU ETS 碳價 (€/tCO₂e)",
                   yaxis_title="淨 CBAM 負擔 (€)", legend=dict(orientation="h", y=1.08), **PLOTLY_LAYOUT)
st.plotly_chart(sens, width="stretch")

with st.expander("📋 計算明細 (可匯出)"):
    detail = pd.DataFrame([
        ("HS / CN 稅則", hs_code or "—"),
        ("計費隱含排放 (tCO₂e/t)", f"{r['see']:.3f}"),
        ("免費配額調整 (tCO₂e/t)", f"{r['free_per_t']:.3f}"),
        ("隱含排放總量 (tCO₂e)", f"{r['gross_t']:,.1f}"),
        ("需繳排放量 (tCO₂e)", f"{r['cert_t']:,.1f}"),
        ("原產國碳價抵減 (€)", f"{r['origin_ded']:,.0f}"),
        ("淨 CBAM 負擔 (€)", f"{r['net']:,.0f}"),
        ("出口營收 (€)", f"{revenue:,.0f}"),
    ], columns=["項目", "數值"])
    st.dataframe(detail, hide_index=True, width="stretch")
    st.download_button("⬇️ 下載 CSV", detail.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"cbam_exposure_{year}.csv", mime="text/csv")

disclaimer("本工具為管理決策情境模擬，預設排放係數與基準值僅供示意；正式申報請依歐盟 CBAM 實施法規、"
           "經認證查證機構確認之實際排放數據辦理。2026 年度憑證將於 2027 年起開放購買並依季度均價計價。")
