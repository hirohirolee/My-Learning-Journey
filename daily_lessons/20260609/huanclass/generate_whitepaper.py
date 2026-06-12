import os
import sys
import pandas as pd
import numpy as np

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MD_PATH = os.path.join(BASE_DIR, '50startup_log.md')
PDF_PATH = os.path.join(BASE_DIR, '50_Startups_Whitepaper_v1.pdf')

# User media attachments and project images
BRAIN_DIR = r"C:\Users\admin\.gemini\antigravity-ide\brain\9b20897f-84ba-46e0-a5dd-16db9c0eb0f3"
IMAGE_B1D5D9 = os.path.join(BRAIN_DIR, "media__1781232602821.png") # The attached IDE view
EXEC_IMPORTANCE = os.path.join(BASE_DIR, "images", "executive_importance.png")
EXEC_ACTUAL_PRED = os.path.join(BASE_DIR, "images", "executive_actual_vs_predicted.png")
RD_VS_PROFIT = os.path.join(BASE_DIR, "images", "rd_vs_profit_regplot.png")

# Register Chinese font
font_path = "C:\\Windows\\Fonts\\msjh.ttc"
pdfmetrics.registerFont(TTFont('ChineseFont', font_path))

def build_pdf():
    # Setup document
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles supporting Chinese
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='ChineseFont',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1e3a8a'),
        alignment=1, # Center
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='ChineseFont',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#64748b'),
        alignment=1,
        spaceAfter=30
    )
    
    h1_style = ParagraphStyle(
        'H1_Chinese',
        parent=styles['Normal'],
        fontName='ChineseFont',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1e3a8a'),
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'H2_Chinese',
        parent=styles['Normal'],
        fontName='ChineseFont',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0d9488'),
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True
    )
    
    h3_style = ParagraphStyle(
        'H3_Chinese',
        parent=styles['Normal'],
        fontName='ChineseFont',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#f59e0b'),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body_Chinese',
        parent=styles['Normal'],
        fontName='ChineseFont',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8
    )
    
    bullet_style = ParagraphStyle(
        'Bullet_Chinese',
        parent=body_style,
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=4
    )
    
    code_style = ParagraphStyle(
        'Code_Style',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0f172a'),
        backColor=colors.HexColor('#f1f5f9'),
        borderColor=colors.HexColor('#cbd5e1'),
        borderWidth=1,
        borderPadding=6,
        spaceAfter=8
    )
    
    story = []
    
    # --- Title Page ---
    story.append(Spacer(1, 40))
    story.append(Paragraph("50 Startups 利潤預測與決策分析專案", title_style))
    story.append(Paragraph("技術白皮書與商業決策指引報告 (Technical Whitepaper)", subtitle_style))
    story.append(Spacer(1, 20))
    
    # Metadata block
    meta_data = [
        [Paragraph("<b>專案名稱:</b> 50 Startups Profit Prediction", body_style), Paragraph("<b>發佈日期:</b> 2026 年 6 月 12 日", body_style)],
        [Paragraph("<b>協作開發:</b> Gemini (Antigravity)", body_style), Paragraph("<b>架構標準:</b> CRISP-DM 數據科學流程", body_style)],
        [Paragraph("<b>專案路徑:</b> hirohirolee/My-Learning-Journey", body_style), Paragraph("<b>系統版本:</b> Web App v1.2 (Optimized)", body_style)]
    ]
    t_meta = Table(meta_data, colWidths=[250, 250])
    t_meta.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 40))
    
    # Brief Intro
    story.append(Paragraph("<b>前言:</b> 本白皮書完整彙整了基於 CRISP-DM 流程的新創公司利潤預測專案。內容包含高階商業決策（Executive Summary）、雙語統計與機器學習技術報告（Technical Analysis）、系統效能與程式優化日誌（Change Logs）以及完整的雲端部署指引。旨在為投資人、創始人以及技術開發團隊提供全方位的商業與技術對照手冊。", body_style))
    story.append(PageBreak())
    
    # --- Part 1: Executive Summary ---
    story.append(Paragraph("第一篇：高階商業決策與互動分析 (Executive Summary)", h1_style))
    story.append(Paragraph("本章節專為經營決策層設計，以最直觀的商業語言總結 <i>50_Startups</i> 專案模型的核心發現與決策指引，避開生硬的數學公式。", body_style))
    
    story.append(Paragraph("1. 模型總結：預測利潤到底準不準？", h2_style))
    story.append(Paragraph("• <b>結論</b>：極度精準！本模型可解釋市場上 92.6% 的新創年利潤變化。", bullet_style))
    story.append(Paragraph("• 在測試新創公司時，平均預測誤差僅在 <b>$6,500</b> 左右。相對於公司平均 $11.2 萬的年利潤，誤差率僅為 5.8%，具有極高的實務參考價值。", bullet_style))
    
    story.append(Paragraph("2. 資金配置黃金法則：100 萬美金該投在哪？", h2_style))
    story.append(Paragraph("• <b>黃金分配</b>：壓倒性投入「研發 (R&D)」，行銷適量，行政費用越低越好。", bullet_style))
    story.append(Paragraph("• <b>研發 (R&D)</b>：每多投入 $1.00，預期帶回 $0.81 的新增利潤（回報率達 81%）。", bullet_style))
    story.append(Paragraph("• <b>行銷 (Marketing)</b>：每多投入 $1.00，預期帶回 $0.03 的新增利潤（回報率僅 3%）。", bullet_style))
    story.append(Paragraph("• <b>行政 (Admin)</b>：每多投入 $1.00，利潤反而倒扣 $0.07（為淨損失、負向效應）。", bullet_style))
    story.append(Paragraph("• <b>顧問建議</b>：優先撥出 80%~85% 的預算投入研發以確保產品核心優勢，15% 進行精準行銷，並嚴格控管行政管理成本。", bullet_style))
    
    story.append(Paragraph("3. 地區決策與選址分析", h2_style))
    story.append(Paragraph("• <b>結論</b>：三個州獲利無顯著差異，選擇「營運成本最低」的地方即可。地理位置對利潤的預測影響力低於 0.2%。新創公司無需迷信「加州」等高成本熱點，哪裡租金低、稅率划算，就是最好的選址。", bullet_style))
    
    story.append(Paragraph("4. 異常點啟示：Index 49 給我們的警示？", h2_style))
    story.append(Paragraph("• 被剔除的 Index 49 公司呈現了典型的失敗特徵：「重行政、輕產品，無核心競爭力」。該公司研發支出為 $0，行銷花了 $4.5 萬，而行政費用卻高達 $11.7 萬，最終只換來 $1.4 萬的利潤。這警告我們：沒有技術研發，只靠行銷與虛胖的行政組織是行不通的。", bullet_style))
    
    # Executive Images
    story.append(Spacer(1, 15))
    story.append(Paragraph("5. 直觀圖表視覺化 (Executive Visuals)", h2_style))
    story.append(Paragraph("下圖展示了新創公司利潤決定因子的權重排行，研發以 91.7% 的決策權重佔據絕對主導地位，行銷占 7.3%，其餘特徵均小於 1%：", body_style))
    
    if os.path.exists(EXEC_IMPORTANCE):
        story.append(Image(EXEC_IMPORTANCE, width=4.5*inch, height=2.8*inch))
        story.append(Paragraph("<font size=8>圖 1: 新創公司利潤驅動因子重要性排行 (研發支出佔絕對主導 91.7%)</font>", subtitle_style))
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("下圖為實際值與預測值的對比圖，藍色圓點代表測試集中的真實公司，紅色斜虛線代表完美預測線。所有藍色點均緊貼在紅色虛線兩側，並未出現大幅度偏離，證明模型的實際預估能力極強：", body_style))
    
    if os.path.exists(EXEC_ACTUAL_PRED):
        story.append(Image(EXEC_ACTUAL_PRED, width=4.5*inch, height=2.8*inch))
        story.append(Paragraph("<font size=8>圖 2: 預估利潤 vs 真實利潤散佈圖 (測試集 R² 可解釋度達 92.6%)</font>", subtitle_style))
        
    story.append(PageBreak())
    
    # --- Part 2: Technical Analysis ---
    story.append(Paragraph("第二篇：CRISP-DM 雙語技術與統計分析報告 (Technical Analysis)", h1_style))
    story.append(Paragraph("本章節詳述針對 <i>50_Startups.csv</i> 資料集進行的統計清洗、資料工程與機器學習建模評估。", body_style))
    
    story.append(Paragraph("2.1 商業與資料理解 (Business & Data Understanding)", h2_style))
    story.append(Paragraph("本專案的核心目標是利用企業在研發支出 (R&D Spend), 行政管理 (Administration), 行銷推廣 (Marketing Spend) 的投入以及所在的地區 (State), 來精準預測其產出的利潤 (Profit)。資料集包含 50 筆記錄，其中含有 3 項連續型支出特徵、1 項地區類別特徵以及 1 項 Profit 目標變數。", body_style))
    
    story.append(Paragraph("2.2 數據清洗與準備 (Data Preparation)", h2_style))
    story.append(Paragraph("<b>1) 極端值剔除 (IQR Outlier Filtering):</b> 利用四分位距 (IQR) 檢驗目標欄位 `Profit` 的分布。計算出 IQR 為 $49,627.07，極端低值門檻為 $15,698.29，極端高值門檻為 $214,206.59。偵測發現 Index 49 的 Profit 為 $14,681.40，低於門檻，判定為異常值並直接剔除。剔除後建模樣本數為 49 筆，可防範異常值干擾迴歸線擬合。", body_style))
    story.append(Paragraph("<b>2) 0 值處理 (Zero Values):</b> 數據集中 Index 19, 47, 48 包含部分 0 值。這些代表草創或不投放行銷的真實業務狀況，因此保持原樣，不進行插值填補。", body_style))
    story.append(Paragraph("<b>3) 類別編碼與防共線 (Encoding):</b> 針對類別變數 `State`（加州/佛州/紐約）進行 One-Hot 編碼，並設定 `drop_first=True` 剔除基底地區（加州），僅保留 `State_Florida` 與 `State_New York`。此舉能有效避開虛擬變數陷阱 (Dummy Variable Trap)。", body_style))
    story.append(Paragraph("<b>4) 特徵縮放 (Feature Scaling):</b> 僅針對 `R&D Spend`, `Administration`, `Marketing Spend` 等數值連續欄位套用 `StandardScaler`；One-Hot 編碼虛擬變數則維持 0-1 不縮放以保留可解釋性。", body_style))
    
    story.append(Paragraph("2.3 模型建立與效能對比 (Modeling & Evaluation)", h2_style))
    story.append(Paragraph("我們將資料集切分為 80% 訓練集與 20% 測試集，並訓練了多個迴歸模型進行對比。以下為兩款核心模型的效能評估：", body_style))
    
    # Table of Model performance
    table_data = [
        [Paragraph("<b>評估模型 (ML Model)</b>", body_style), Paragraph("<b>解釋能力 (R-squared)</b>", body_style), Paragraph("<b>平均絕對誤差 (MAE)</b>", body_style)],
        [Paragraph("多元線性迴歸 (Linear Regression - OLS)", body_style), Paragraph("0.91908", body_style), Paragraph("$6,550.86", body_style)],
        [Paragraph("隨機森林迴歸 (Random Forest)", body_style), Paragraph("0.92601", body_style), Paragraph("$6,892.37", body_style)]
    ]
    t_perf = Table(table_data, colWidths=[220, 140, 140])
    t_perf.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e2e8f0')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_perf)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("2.4 特徵權重與重要性分析 (Feature Weights & Importance)", h2_style))
    story.append(Paragraph("<b>多元線性迴歸特徵權重 (標準化係數)</b>：研發支出 (+34,885.07) > 行銷支出 (+4,342.70) > 行政管理 (-425.04)。地理位置虛擬變數則小於 0.2% 影響力。這表明研發支出是主導獲利的第一驅動力。", body_style))
    
    # Equations
    story.append(Paragraph("<b>複線性迴歸數學方程式 (原始數據):</b>", h3_style))
    story.append(Paragraph("<code>Profit = 51,306.76 + 0.7619 * (R&D Spend) - 0.0147 * (Administration) + 0.0400 * (Marketing Spend) - 1860.88 * (State_Florida) - 2877.86 * (State_New York)</code>", code_style))
    
    story.append(Paragraph("2.5 專案深度觀察與統計檢定", h2_style))
    story.append(Paragraph("• <b>共線性檢驗 (VIF)</b>：計算出各支出特徵之變異數膨脹因子（R&D Spend VIF: 2.40，Marketing Spend VIF: 2.32，Admin VIF: 1.18），皆小於臨界值 5，驗證無顯著共線性，係數具備高信賴度。", bullet_style))
    story.append(Paragraph("• <b>地區消融實驗 (Ablation Test)</b>：包含地區時 OLS解釋力為 96.18%；完全剔除地區特徵後為 96.13%。模型解釋力僅微幅下降 0.05%，證實設點州別無實務顯著影響。", bullet_style))
    story.append(Paragraph("• <b>異常點敏感性檢驗</b>：若不剔除異常值 Index 49，佛州係數為正數 (+$198.79)；剔除異常值後，佛州係數轉為負數 (-$1,564.22)，證明 OLS 對單一極端值具有高敏感性，印證了 IQR 清洗的重要性。", bullet_style))
    
    # Feature Selection Image
    if os.path.exists(IMAGE_B1D5D9):
        story.append(Spacer(1, 10))
        story.append(Paragraph("<b>逐步特徵篩選評估與 9 種特徵選擇演算法對照表 (Feature Selection Study)</b>：", body_style))
        story.append(Image(IMAGE_B1D5D9, width=5.0*inch, height=2.8*inch))
        story.append(Paragraph("<font size=8>圖 3: 9 種特徵篩選算法隨特徵數增加之指標收斂對比 (摘自 L6 50 Startup 專案篩選圖像)</font>", subtitle_style))
    
    story.append(PageBreak())
    
    # --- Part 3: Change Logs & Deployment ---
    story.append(Paragraph("第三篇：系統變更與今日優化全紀錄 (Change & Modification Logs)", h1_style))
    story.append(Paragraph("本章節總結了專案程式碼變更日誌，包含架構與效能重構、Plotly 視覺化升級以及 Bug 修復。", body_style))
    
    story.append(Paragraph("3.1 架構與效能重構", h2_style))
    story.append(Paragraph("• <b>演算法模型擴展</b>：由原本的 2 種模型擴充為 5 種（多元線性迴歸、脊迴歸、SVR、隨機森林、梯度提升迴歸），並在 Streamlit Web 排行榜中動態高亮最優模型。", bullet_style))
    story.append(Paragraph("• <b>最佳化向量化重構 (Vectorization)</b>：將預算配置搜尋邏輯從單筆迴圈改寫為 NumPy 向量化批量運算。最佳化運算時間從 <b>2,000 毫秒縮短至 5 毫秒（0.005 秒）以內</b>，徹底消除介面卡頓，實現即時秒響應。", bullet_style))
    
    story.append(Paragraph("3.2 互動式視覺化優化", h2_style))
    story.append(Paragraph("• <b>對數尺度 Y 軸 (Log Scale)</b>：針對各模型 MSE 差距大導致底層折線擠壓的問題，新增 Log Scale 切換控制（預設開啟），拉開並分離折線，解決線條擠壓問題。", bullet_style))
    story.append(Paragraph("• <b>演算法多選篩選器 (Multi-Select)</b>：側邊欄配置勾選選單，可動態顯示/隱藏特定模型。", bullet_style))
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("第四篇：雲端與本地端部署指南 (Deployment Guide)", h1_style))
    
    story.append(Paragraph("4.1 本地運行指南", h2_style))
    story.append(Paragraph("在本地端運行 Streamlit Web 應用程式，請執行以下步驟：", body_style))
    story.append(Paragraph("<code># 1. 確保 Python 環境滿足 (3.9+)\npython --version\n\n# 2. 安裝 requirements.txt 所列套件\npip install -r requirements.txt\n\n# 3. 啟動 Streamlit 應用程式\nstreamlit run app.py</code>", code_style))
    
    story.append(Paragraph("4.2 Streamlit Community Cloud 部署設定", h2_style))
    story.append(Paragraph("1. 將所有程式碼（包含 50_Startups.csv）推送至 GitHub `My-Learning-Journey` 的主分支。", bullet_style))
    story.append(Paragraph("2. 登入 Streamlit Share，點擊 <b>New App</b> 並設定：\n   • Repository: <code>hirohirolee/My-Learning-Journey</code>\n   • Branch: <code>master</code>\n   • Main file path: <code>daily_lessons/20260609/huanclass/app.py</code>", bullet_style))
    story.append(Paragraph("3. 點擊 <b>Deploy!</b> 部署。1-2 分鐘後容器啟動即可獲取專屬公網網址。", bullet_style))
    
    # Build
    doc.build(story)
    print("PDF whitepaper generated successfully at:", PDF_PATH)

if __name__ == "__main__":
    build_pdf()
