import streamlit as st
import pandas as pd
import numpy as np
import io
import json
import plotly.express as px
from typing import Dict, Any, Tuple
from btc_core.probability import get_probability_over_horizons, calculate_waiting_time_metrics, get_poisson_probability_of_success
from btc_core.finance import calculate_financials, run_scenarios
from btc_core.simulation import run_monte_carlo_simulation
from btc_config import ASIC_DATABASE
from btc_utils.formatter import format_currency, format_duration, format_probability, format_hashrate
from btc_ui.metrics import render_kpi_card, render_risk_panel
from btc_ui.charts import (
    create_probability_curve_chart,
    create_blocks_distribution_chart,
    create_cash_flow_fan_chart,
    create_waterfall_chart,
    create_expenses_pie_chart,
    create_sensitivity_tornado_chart,
    create_roi_heatmap,
    COLOR_TEXT,
    COLOR_GRID
)

def _evaluate_risk_profile(
    financials: Dict[str, Any],
    prob_lifetime: float,
    wait_time_secs: float
) -> Tuple[float, str, str, str, str, str]:
    """Evaluates the composite risk score and generates qualitative indicators in Traditional Chinese."""
    # 1. Expected Waiting Time Rating
    year_secs = 31536000.0
    if wait_time_secs < (30.0 * 86400.0): # < 1 month
        time_rating = "極佳"
        time_color = "green"
        time_score_penalty = 5
    elif wait_time_secs < year_secs: # < 1 year
        time_rating = "良好"
        time_color = "yellow"
        time_score_penalty = 20
    elif wait_time_secs < (5.0 * year_secs): # < 5 years
        time_rating = "普通"
        time_color = "orange"
        time_score_penalty = 50
    else:
        time_rating = "極低機率 / 極長"
        time_color = "red"
        time_score_penalty = 80

    # 2. Financial Rating
    net_profit = financials["total_net_profit"]
    roi = financials["roi"]
    monthly_net = financials["monthly_net_profit"]
    
    if net_profit > 0:
        financial_rating = "具獲利性"
        financial_color = "green"
        fin_score_penalty = 10
    elif monthly_net > 0:
        financial_rating = "投機 (可能虧損折舊)"
        financial_color = "orange"
        fin_score_penalty = 50
    else:
        financial_rating = "無可行性 (營運赤字)"
        financial_color = "red"
        fin_score_penalty = 90

    # 3. Composite Risk Score (1 to 100)
    risk_score = (time_score_penalty * 0.6) + (fin_score_penalty * 0.4)
    risk_score = max(1.0, min(100.0, risk_score))

    # 4. Recommendation text
    if time_rating == "極低機率 / 極長" and financial_rating == "無可行性 (營運赤字)":
        rec = (
            "在此配置下強烈不建議進行單機挖礦。由於您的電費與運維支出（每月 "
            f"${financials['monthly_opex']:.2f}）已超出您的預期收益，您每月都在面臨營運赤字。此外，"
            f"預期出塊等待時間高達 {format_duration(wait_time_secs)}。您幾乎注定會損失所有的硬體購置及營運資金。"
        )
    elif time_rating == "極低機率 / 極長":
        rec = (
            "投機性彩票挖礦：雖然您每月的現金流為正（挖礦預期收益高於電費），但您預期挖到單個區塊的時間長達 "
            f"{format_duration(wait_time_secs)}。由於這是單機挖礦，在您礦機的 {financials['cash_flows'].__len__() - 1} "
            "個月生命週期內，有極高機率挖到 0 個區塊，意味著您極可能完全無法收回硬體購置成本。"
        )
    elif financial_rating == "無可行性 (營運赤字)":
        rec = (
            "營運赤字：儘管您的預估等待出塊時間相對較短，但您的電費單價過高，導致每月的營運淨利潤為負。只要礦機持續運轉，"
            "您每個月都會虧損。建議加入礦池或搬遷至電費更低的地區。"
        )
    else:
        rec = (
            "高可行性配置！您的預估出塊等待時間較短，且電費支出支持正向的每月淨利潤。您有很高的機率收回硬體投資。"
            "在此配置下，單機挖礦在數學上是合理的。"
        )

    return risk_score, time_rating, time_color, financial_rating, financial_color, rec

def render_dashboard(user_settings: Dict[str, Any], live_data: Dict[str, Any]) -> None:
    """Orchestrates the primary tab layout and visual dashboard in Traditional Chinese."""
    # 1. Run core models using inputs
    financials = calculate_financials(
        miner_hashrate_h_s=user_settings["miner_hashrate_h_s"],
        power_watts=user_settings["power_watts"],
        asic_cost_usd=user_settings["asic_cost_usd"],
        electricity_cost_usd_kwh=user_settings["electricity_cost_usd_kwh"],
        pue=user_settings["pue"],
        maintenance_cost_usd_month=user_settings["maintenance_cost_usd_month"],
        lifetime_months=user_settings["lifetime_months"],
        difficulty=user_settings["difficulty"],
        block_reward_btc=user_settings["block_reward_btc"],
        est_tx_fees_btc=user_settings["est_tx_fees_btc"],
        btc_price_usd=user_settings["btc_price_usd"],
        annual_discount_rate=user_settings["annual_discount_rate"]
    )
    
    horizons = get_probability_over_horizons(
        miner_hashrate_h_s=user_settings["miner_hashrate_h_s"],
        difficulty=user_settings["difficulty"]
    )
    
    wait_time_data = calculate_waiting_time_metrics(
        miner_hashrate_h_s=user_settings["miner_hashrate_h_s"],
        difficulty=user_settings["difficulty"]
    )
    
    prob_lifetime = get_poisson_probability_of_success(
        miner_hashrate_h_s=user_settings["miner_hashrate_h_s"],
        difficulty=user_settings["difficulty"],
        period_seconds=float(user_settings["lifetime_months"]) * 30.416 * 86400.0
    )
    
    # Evaluate risk score
    risk_score, time_rating, time_color, fin_rating, fin_color, recommendation = _evaluate_risk_profile(
        financials=financials,
        prob_lifetime=prob_lifetime,
        wait_time_secs=wait_time_data["expected_waiting_time_seconds"]
    )

    # 2. Render Tabs (Traditional Chinese)
    tab_overview, tab_finance, tab_sim, tab_math, tab_hw = st.tabs([
        "📊 項目總覽", 
        "💰 財務預測表", 
        "🎲 蒙特卡洛與場景分析", 
        "📐 數學機率與等待時間", 
        "💾 挖礦硬體比對"
    ])

    # -----------------
    # TAB 1: OVERVIEW
    # -----------------
    with tab_overview:
        st.subheader("挖礦分析儀表板摘要")
        
        # Grid of KPI Cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            render_kpi_card(
                title="預期出塊時間",
                value=format_duration(wait_time_data["expected_waiting_time_seconds"]).split(",")[0],
                subtext=f"中位數: {format_duration(wait_time_data['median_waiting_time_seconds']).split(',')[0]}",
                delta=None
            )
        with col2:
            render_kpi_card(
                title="預期挖出 BTC",
                value=f"{financials['total_btc_earned']:.6f} BTC",
                subtext=f"共 {user_settings['lifetime_months']} 個月",
                delta=None
            )
        with col3:
            net_profit_formatted = format_currency(financials["total_net_profit"])
            render_kpi_card(
                title="預期淨利潤",
                value=net_profit_formatted,
                subtext=f"投資回報率: {financials['roi']:.2f}%",
                delta=None,
                delta_positive=financials["total_net_profit"] > 0
            )
        with col4:
            render_kpi_card(
                title="生命週期出塊成功率",
                value=format_probability(prob_lifetime, 4),
                subtext="找到至少 1 個區塊的機率",
                delta=None
            )

        # Risk Assessment Block
        render_risk_panel(
            risk_score=risk_score,
            time_rating=time_rating,
            time_color=time_color,
            financial_rating=fin_rating,
            financial_color=fin_color,
            recommendation=recommendation
        )

        # Summary Visualizations
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            # Waterfall Chart
            fig_waterfall = create_waterfall_chart(
                asic_cost=user_settings["asic_cost_usd"],
                opex=financials["total_opex"],
                expected_revenue=financials["total_revenue_usd"],
                net_profit=financials["total_net_profit"]
            )
            st.plotly_chart(fig_waterfall, use_container_width=True)
            
        with col_chart2:
            # Expense Pie Chart
            standard_elec = (user_settings["power_watts"] / 1000.0) * 24.0 * (user_settings["lifetime_months"] * 30.416) * user_settings["electricity_cost_usd_kwh"]
            cooling_overhead = standard_elec * (user_settings["pue"] - 1.0)
            maintenance_total = user_settings["maintenance_cost_usd_month"] * user_settings["lifetime_months"]
            
            fig_pie = create_expenses_pie_chart(
                asic_cost=user_settings["asic_cost_usd"],
                electricity_cost=standard_elec,
                cooling_cost=cooling_overhead,
                maintenance_cost=maintenance_total
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    # -----------------
    # TAB 2: FINANCIAL PROJECTIONS
    # -----------------
    with tab_finance:
        st.subheader("財務預測明細賬")
        st.markdown(
            "本表預測了每月的預期財務明細。請注意，由於單機挖礦具有高度隨機性，"
            "此處的值代表統計學上的**期望值**（加權平均值），而非保證收益。"
        )

        # Build Month-by-month DataFrame
        cf_list = financials["cash_flows"]
        monthly_opex = financials["monthly_opex"]
        monthly_rev = financials["monthly_revenue_usd"]
        monthly_btc = financials["monthly_btc_earned"]
        monthly_net = financials["monthly_net_profit"]

        records = []
        cum_cash = cf_list[0]
        # Month 0 record
        records.append({
            "月份": 0,
            "挖礦收益 (USD)": 0.0,
            "挖礦收益 (BTC)": 0.0,
            "營運成本 (USD)": 0.0,
            "淨現金流 (USD)": cf_list[0],
            "累計現金流 (USD)": cum_cash
        })
        
        for m in range(1, len(cf_list)):
            cum_cash += monthly_net
            records.append({
                "月份": m,
                "挖礦收益 (USD)": monthly_rev,
                "挖礦收益 (BTC)": monthly_btc,
                "營運成本 (USD)": monthly_opex,
                "淨現金流 (USD)": monthly_net,
                "累計現金流 (USD)": cum_cash
            })

        df_projections = pd.DataFrame(records)
        
        # Display formatted dataframe
        st.dataframe(
            df_projections.style.format({
                "挖礦收益 (USD)": "${:,.2f}",
                "挖礦收益 (BTC)": "{:.6f}",
                "營運成本 (USD)": "${:,.2f}",
                "淨現金流 (USD)": "${:,.2f}",
                "累計現金流 (USD)": "${:,.2f}"
            }),
            use_container_width=True
        )

        # Financial Summary KPI metrics
        st.markdown("### 折現現金流 (DCF) 分析")
        col_dcf1, col_dcf2, col_dcf3 = st.columns(3)
        with col_dcf1:
            st.metric(
                label="淨現值 (NPV)", 
                value=format_currency(financials["npv"]),
                help="淨現值 (NPV) 用於評估未來各期淨現金流折現到當前的總和，再扣除初始 ASIC 硬體購置成本。"
            )
        with col_dcf2:
            irr_val = financials["irr_annual"]
            irr_text = f"{irr_val*100:.2f}%" if not np.isnan(irr_val) else "無可解"
            st.metric(
                label="年化內部收益率 (IRR)", 
                value=irr_text,
                help="內部收益率 (IRR) 是使項目淨現值 (NPV) 等於零的折現率，反映項目的實際年化回報率。"
            )
        with col_dcf3:
            pb_val = financials["payback_period_months"]
            pb_text = f"{pb_val} 個月" if pb_val != float("inf") else "無法回本"
            st.metric(
                label="動態回本週期", 
                value=pb_text,
                help="透過各期營運淨利潤收回初始硬體購置成本所需的月數。"
            )

        # Break-Even Analysis
        st.markdown("### 營運盈虧平衡點 (關機幣價與難度)")
        col_be1, col_be2 = st.columns(2)
        with col_be1:
            st.metric(
                label="盈虧平衡折算幣價 (關機幣價)", 
                value=format_currency(financials["breakeven_btc_price"]),
                help="彌補每月營運成本（電費與維護費）所需的最低比特幣價格。幣價低於此值將導致營運赤字。"
            )
        with col_be2:
            st.metric(
                label="盈虧平衡全網難度上限", 
                value=f"{financials['breakeven_difficulty']:,.4e}",
                help="彌補每月營運成本所允許的全網難度上限。難度高於此值將導致營運赤字。"
            )

        # Export Options
        st.markdown("### 匯出財務數據")
        
        # CSV Data
        csv_buffer = io.StringIO()
        df_projections.to_csv(csv_buffer, index=False)
        csv_bytes = csv_buffer.getvalue().encode("utf-8")
        
        # JSON Data
        json_bytes = df_projections.to_json(orient="records", indent=2).encode("utf-8")
        
        # Excel Data
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            df_projections.to_excel(writer, index=False, sheet_name="財務預測")
        excel_bytes = excel_buffer.getvalue()

        col_exp1, col_exp2, col_exp3 = st.columns(3)
        with col_exp1:
            st.download_button(
                label="下載 CSV 報表",
                data=csv_bytes,
                file_name="bitcoin_solo_mining_projections.csv",
                mime="text/csv"
            )
        with col_exp2:
            st.download_button(
                label="下載 Excel 報表",
                data=excel_bytes,
                file_name="bitcoin_solo_mining_projections.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col_exp3:
            st.download_button(
                label="下載 JSON 報表",
                data=json_bytes,
                file_name="bitcoin_solo_mining_projections.json",
                mime="application/json"
            )

    # -----------------
    # TAB 3: MONTE CARLO & SCENARIOS
    # -----------------
    with tab_sim:
        st.subheader("蒙特卡洛模擬引擎")
        st.markdown(
            f"正在模擬 **{user_settings['simulation_count']:,} 次獨立隨機挖礦路徑**，"
            "以估算生命週期內出塊機率與現金流分布。這能客觀反映單機挖礦的高隨機性。"
        )

        with st.spinner("正在執行蒙特卡洛模擬計算..."):
            sim_results = run_monte_carlo_simulation(
                miner_hashrate_h_s=user_settings["miner_hashrate_h_s"],
                power_watts=user_settings["power_watts"],
                asic_cost_usd=user_settings["asic_cost_usd"],
                electricity_cost_usd_kwh=user_settings["electricity_cost_usd_kwh"],
                pue=user_settings["pue"],
                maintenance_cost_usd_month=user_settings["maintenance_cost_usd_month"],
                lifetime_months=user_settings["lifetime_months"],
                initial_difficulty=user_settings["difficulty"],
                difficulty_annual_growth=user_settings["difficulty_annual_growth"],
                block_reward_btc=user_settings["block_reward_btc"],
                est_tx_fees_btc=user_settings["est_tx_fees_btc"],
                btc_price_usd=user_settings["btc_price_usd"],
                btc_price_annual_growth=user_settings["btc_price_annual_growth"],
                simulation_count=user_settings["simulation_count"]
            )

        # Simulation KPIs
        col_sim1, col_sim2, col_sim3 = st.columns(3)
        with col_sim1:
            st.metric(
                label="模擬成功出塊率",
                value=f"{sim_results['success_rate']*100:.4f}%",
                help="在所有模擬路徑中，成功挖到至少 1 個區塊的路徑比例。"
            )
        with col_sim2:
            st.metric(
                label="模擬最終盈利機率",
                value=f"{sim_results['profit_rate']*100:.4f}%",
                help="扣除硬體購置成本與所有電費/維護支出後，最終淨回報大於零的路徑比例。"
            )
        with col_sim3:
            st.metric(
                label="模擬平均 ROI",
                value=f"{(sim_results['mean_profit_usd'] / user_settings['asic_cost_usd']) * 100:.2f}%" if user_settings['asic_cost_usd'] > 0 else "0.00%",
                help="所有模擬路徑的平均投資回報率 (ROI)。"
            )

        # Simulation Fan Chart
        fig_fan = create_cash_flow_fan_chart(
            months=user_settings["lifetime_months"],
            mean_cf_path=sim_results["mean_cf_path"],
            cf_percentiles=sim_results["cf_percentiles"]
        )
        st.plotly_chart(fig_fan, use_container_width=True)

        st.markdown("### 市場情境對比分析")
        st.markdown(
            "對比分析礦機生命週期內不同的宏觀市場情境："
        )

        scenarios_data = run_scenarios(
            miner_hashrate_h_s=user_settings["miner_hashrate_h_s"],
            power_watts=user_settings["power_watts"],
            asic_cost_usd=user_settings["asic_cost_usd"],
            electricity_cost_usd_kwh=user_settings["electricity_cost_usd_kwh"],
            pue=user_settings["pue"],
            maintenance_cost_usd_month=user_settings["maintenance_cost_usd_month"],
            lifetime_months=user_settings["lifetime_months"],
            base_difficulty=user_settings["difficulty"],
            block_reward_btc=user_settings["block_reward_btc"],
            est_tx_fees_btc=user_settings["est_tx_fees_btc"],
            base_btc_price_usd=user_settings["btc_price_usd"],
            annual_discount_rate=user_settings["annual_discount_rate"]
        )

        # Format scenario comparisons into a summary table
        scenario_records = []
        for name, data in scenarios_data.items():
            # Translate scenario names to Traditional Chinese
            c_name = name
            if name == "Bear Market":
                c_name = "熊市情境"
            elif name == "Neutral Market":
                c_name = "震蕩市情境"
            elif name == "Bull Market":
                c_name = "牛市情境"
                
            scenario_records.append({
                "情境": c_name,
                "均價 (USD)": data["adjusted_price"],
                "生命週期總收益": data["total_revenue_usd"],
                "生命週期總電費成本": data["total_opex"],
                "淨利潤 (期望值)": data["total_net_profit"],
                "淨現值 (NPV)": data["npv"],
                "投資回報率 (ROI)": data["roi"]
            })

        df_scenarios = pd.DataFrame(scenario_records)
        st.dataframe(
            df_scenarios.style.format({
                "均價 (USD)": "${:,.2f}",
                "生命週期總收益": "${:,.2f}",
                "生命週期總電費成本": "${:,.2f}",
                "淨利潤 (期望值)": "${:,.2f}",
                "淨現值 (NPV)": "${:,.2f}",
                "投資回報率 (ROI)": "{:.2f}%"
            }),
            use_container_width=True
        )

        # Sensitivity Heatmap Generator
        st.markdown("### 預期 ROI 雙維度敏感性分析熱力圖")
        st.caption("展示不同年難度增長率與比特幣價格組合下的預期生命週期投資回報率 (ROI)：")
        
        # Grid range values
        price_grid = np.linspace(user_settings["btc_price_usd"] * 0.5, user_settings["btc_price_usd"] * 2.0, 5)
        diff_grid = np.linspace(0.0, 0.4, 5)
        
        roi_matrix = np.zeros((len(price_grid), len(diff_grid)))
        for p_idx, p_val in enumerate(price_grid):
            for d_idx, d_val in enumerate(diff_grid):
                # Calculate average difficulty based on growth rate
                years = user_settings["lifetime_months"] / 12.0
                avg_diff = user_settings["difficulty"]
                if d_val > 0:
                    avg_diff = user_settings["difficulty"] * (((1.0 + d_val) ** years - 1.0) / (years * np.log(1.0 + d_val)))
                
                fin = calculate_financials(
                    miner_hashrate_h_s=user_settings["miner_hashrate_h_s"],
                    power_watts=user_settings["power_watts"],
                    asic_cost_usd=user_settings["asic_cost_usd"],
                    electricity_cost_usd_kwh=user_settings["electricity_cost_usd_kwh"],
                    pue=user_settings["pue"],
                    maintenance_cost_usd_month=user_settings["maintenance_cost_usd_month"],
                    lifetime_months=user_settings["lifetime_months"],
                    difficulty=avg_diff,
                    block_reward_btc=user_settings["block_reward_btc"],
                    est_tx_fees_btc=user_settings["est_tx_fees_btc"],
                    btc_price_usd=p_val,
                    annual_discount_rate=user_settings["annual_discount_rate"]
                )
                roi_matrix[p_idx, d_idx] = fin["roi"]
                
        fig_heatmap = create_roi_heatmap(price_grid, diff_grid, roi_matrix)
        st.plotly_chart(fig_heatmap, use_container_width=True)

    # -----------------
    # TAB 4: MATHEMATICAL PROBABILITY
    # -----------------
    with tab_math:
        st.subheader("區塊發現機率與預估等待時間")
        st.markdown(
            "基於機率論分布進行單機挖礦分析。比特幣的出塊過程被建模為無記憶性的 Poisson 隨機過程。"
        )

        col_math1, col_math2 = st.columns(2)
        with col_math1:
            st.markdown("### 等待出塊時間置信區間 (指數分布)")
            
            ci_lower_desc = format_duration(wait_time_data["ci_95_lower_seconds"])
            ci_upper_desc = format_duration(wait_time_data["ci_95_upper_seconds"])
            
            st.write(f"**預期 (平均) 等待時間:** {format_duration(wait_time_data['expected_waiting_time_seconds'])}")
            st.write(f"**中位數 (50% 機率) 等待時間:** {format_duration(wait_time_data['median_waiting_time_seconds'])}")
            st.write(f"**95% 概率的出塊時間區間:**")
            st.info(f"介於 **{ci_lower_desc}** 與 **{ci_upper_desc}** 之間")
            
            st.caption(
                "說明：指數分布的特點是置信區間非常寬。您有 2.5% 的極小機率在極短時間內（低於下限）"
                "挖到區塊，但也有 2.5% 的機率需要等待比上限更長的時間。"
            )
            
        with col_math2:
            st.markdown("### 標準時間跨度下的出塊機率")
            df_horizons = pd.DataFrame(horizons)
            # Translate time horizons
            horizon_translation = {
                "1 day": "1 天",
                "7 days": "7 天",
                "30 days": "30 天",
                "90 days": "90 天",
                "180 days": "180 天",
                "365 days": "365 天 (1 年)",
                "730 days": "730 天 (2 年)",
                "1825 days": "1825 天 (5 年)"
            }
            df_horizons["時間跨度"] = df_horizons["horizon"].map(horizon_translation)
            df_horizons["成功機率 (%)"] = df_horizons["probability"].apply(lambda p: format_probability(p, 10))
            st.table(df_horizons[["時間跨度", "成功機率 (%)"]])

        col_math_chart1, col_math_chart2 = st.columns(2)
        with col_math_chart1:
            fig_prob = create_probability_curve_chart(horizons)
            st.plotly_chart(fig_prob, use_container_width=True)
        with col_math_chart2:
            # Distribution of block count from Monte Carlo simulation results
            fig_dist = create_blocks_distribution_chart(sim_results["blocks_distribution"])
            st.plotly_chart(fig_dist, use_container_width=True)

    # -----------------
    # TAB 5: HARDWARE DATABASE & COMPARISON
    # -----------------
    with tab_hw:
        st.subheader("主流礦機規格與性能基準數據庫")
        st.markdown(
            "內置的標準 ASIC 礦機規格列表，您可參考此表進行硬體效能比對與基準分析。"
        )

        # Present the ASIC database in a formatted table
        asic_list = []
        for name, specs in ASIC_DATABASE.items():
            asic_list.append({
                "礦機名稱": specs.name,
                "額定算力 (TH/s)": specs.hashrate_th,
                "消耗功率 (W)": specs.power_watts,
                "算力能效比 (J/TH)": specs.efficiency_j_th,
                "發布年份": specs.release_year,
                "預估售價 (USD)": specs.typical_price_usd
            })

        df_asic = pd.DataFrame(asic_list)
        st.dataframe(
            df_asic.style.format({
                "額定算力 (TH/s)": "{:,.1f}",
                "消耗功率 (W)": "{:,.0f}",
                "算力能效比 (J/TH)": "{:,.1f}",
                "發布年份": "{}",
                "預估售價 (USD)": "${:,.2f}"
            }),
            use_container_width=True
        )

        # Performance benchmarking
        st.markdown("### 能效比與算力基準對比圖")
        fig_hw = px.scatter(
            df_asic,
            x="額定算力 (TH/s)",
            y="算力能效比 (J/TH)",
            text="礦機名稱",
            size="預估售價 (USD)",
            color="發布年份",
            color_continuous_scale="Viridis",
            title="礦機效能前沿分布圖 (J/TH 越小能效越佳)"
        )
        fig_hw.update_traces(textposition='top center')
        fig_hw.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=COLOR_TEXT),
            xaxis=dict(gridcolor=COLOR_GRID, title="額定算力 (TH/s)"),
            yaxis=dict(gridcolor=COLOR_GRID, title="算力能效比 (J/TH)")
        )
        st.plotly_chart(fig_hw, use_container_width=True)
