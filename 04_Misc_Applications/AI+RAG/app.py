import streamlit as st
import pandas as pd
import json
import mock_data_generator
import data_monitor
import compliance_agent
import os

st.set_page_config(page_title="AI 顧問 - ISO 合規監控", page_icon="🏭", layout="wide")

st.title("🏭 廠區數據解析與 ISO 合規 RAG AI 代理系統")
st.markdown("本系統展示如何結合**規則引擎**與 **RAG (檢索增強生成)**，針對廠區異常能耗自動查閱 ISO 規範並生成顧問報告。*(基於本地端 HuggingFace + Ollama 模型)*")

with st.sidebar:
    st.header("⚙️ 系統控制面板")
    if st.button("🔄 重新生成測試數據", use_container_width=True):
        with st.spinner("正在生成廠區測試數據與法規條文..."):
            mock_data_generator.generate_factory_data()
            mock_data_generator.generate_iso_rules()
        st.success("數據生成完畢！")
        
    st.markdown("---")
    st.info("提示：此 Demo 預設異常判定閾值為 `1.2 倍`。")

tab1, tab2 = st.tabs(["📊 廠區營運數據監控", "🤖 AI 顧問合規報告"])

with tab1:
    st.header("近期廠區耗電量監控")
    if os.path.exists("factory_data.csv"):
        df = pd.read_csv("factory_data.csv")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.dataframe(df, use_container_width=True, hide_index=True)
            
        with col2:
            st.subheader("耗電趨勢圖 (實際 vs 基準)")
            # 將產線分開畫圖
            line_a = df[df["Line_ID"] == "Line_A"].set_index("Date")[["Power_Usage", "Baseline_kWh"]]
            line_b = df[df["Line_ID"] == "Line_B"].set_index("Date")[["Power_Usage", "Baseline_kWh"]]
            
            st.markdown("**產線 A (Line_A)**")
            st.line_chart(line_a)
            st.markdown("**產線 B (Line_B)**")
            st.line_chart(line_b)
    else:
        st.warning("尚未生成數據，請點擊左側「重新生成測試數據」按鈕。")

with tab2:
    st.header("自動合規性分析與預警")
    if st.button("🚀 執行 AI 異常分析與報告生成", type="primary"):
        if not os.path.exists("factory_data.csv"):
            st.error("找不到測試數據！請先點擊左側面板生成數據。")
        else:
            with st.status("AI 系統分析中...", expanded=True) as status:
                st.write("🔍 正在透過規則引擎篩選異常數據...")
                anomalies_json = data_monitor.monitor_factory_data(threshold_ratio=1.2)
                
                if not anomalies_json:
                    status.update(label="分析完成", state="complete", expanded=False)
                    st.success("🎉 目前廠區數據一切正常，無異常數據需要處理。")
                else:
                    st.write(f"⚠️ 發現異常數據！提取資料中...")
                    st.json(json.loads(anomalies_json))
                    
                    st.write("📚 正在初始化 RAG 向量知識庫 (HuggingFace Embeddings)...")
                    vectorstore = compliance_agent.setup_rag_system()
                    
                    st.write("🧠 正在呼叫本地 LLM (Ollama) 推理並撰寫報告...")
                    report = compliance_agent.generate_compliance_report(anomalies_json, vectorstore)
                    
                    status.update(label="報告生成完成！", state="complete", expanded=False)
                    
                    st.markdown("---")
                    st.markdown("### 📝 高階企業內控顧問 - 最終報告")
                    st.markdown(report)
