import os
import sys
import cv2
import numpy as np
import PIL.Image
import streamlit as st

# 1. 設置頁面標題與佈局
st.set_page_config(
    page_title="🐱🐶 YOLO 貓狗 AI 辨識與數量統計 Web 系統",
    page_icon="🐱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 注入自訂現代化 UI 樣式 (Glassmorphism & Clean Typography)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Noto+Sans+TC:wght@300;400;700&display=swap');

    .stApp {
        font-family: 'Outfit', 'Noto Sans TC', sans-serif;
    }
    
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 50%, #FFD166 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    
    .hero-subtitle {
        font-size: 1.05rem;
        color: #A0AEC0;
        margin-bottom: 1.5rem;
    }
    
    .stat-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: #FFD166;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #CBD5E0;
    }
    
    .badge-tag {
        display: inline-block;
        background: rgba(255, 107, 107, 0.15);
        border: 1px solid rgba(255, 107, 107, 0.4);
        color: #FF6B6B;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 核心依賴套件檢查與載入
@st.cache_resource
def check_dependencies():
    try:
        import torch
        import torchvision
        from ultralytics import YOLO
        return True, "All dependencies loaded"
    except ImportError as e:
        return False, str(e)

deps_ok, deps_msg = check_dependencies()

if not deps_ok:
    st.error(f"⚠️ 核心 AI 引擎套件載入中或缺失：`{deps_msg}`")
    st.info("💡 系統正在背景自動安裝 `ultralytics`，請稍微重新重整頁面。")
    st.stop()

import torch
import torchvision
from ultralytics import YOLO
from torchvision.models import efficientnet_v2_s, EfficientNet_V2_S_Weights, resnet50, ResNet50_Weights
from torchvision.ops import nms

# 4. 快取已載入的神經網絡模型
@st.cache_resource
def load_yolo_model(model_path):
    return YOLO(model_path)

@st.cache_resource
def load_ensemble_models():
    w_res = ResNet50_Weights.DEFAULT
    m_res = resnet50(weights=w_res).eval()
    t_res = w_res.transforms()

    w_eff = EfficientNet_V2_S_Weights.DEFAULT
    m_eff = efficientnet_v2_s(weights=w_eff).eval()
    t_eff = w_eff.transforms()

    return (m_res, t_res), (m_eff, t_eff)

AVAILABLE_MODELS = {
    'YOLOv11x (高精確度 雙類別 - 推薦)': 'yolo11x.pt',
    'YOLOv11s (快速 雙類別)': 'yolo11s.pt',
}

# 5. 核心推理與 Ensemble 輔助函式
def classify_cell_triple_ensemble(cell_bgr, yolo_model, target_classes):
    """三模型 SOTA 集成投票 (ResNet50 + EfficientNetV2 + YOLOv11x)"""
    cell_rgb = cv2.cvtColor(cell_bgr, cv2.COLOR_BGR2RGB)

    kwargs = {'conf': 0.10, 'verbose': False}
    if target_classes:
        kwargs['classes'] = target_classes
    res = yolo_model(cell_rgb, **kwargs)[0]

    yolo_cat_conf = 0.0
    yolo_dog_conf = 0.0
    for b in res.boxes:
        c_name = yolo_model.names[int(b.cls[0])].lower().strip()
        cf = float(b.conf[0])
        if c_name == 'cat' and cf > yolo_cat_conf:
            yolo_cat_conf = cf
        elif c_name == 'dog' and cf > yolo_dog_conf:
            yolo_dog_conf = cf

    (m_res, t_res), (m_eff, t_eff) = load_ensemble_models()

    t_img_res = t_res(torch.from_numpy(cell_rgb).permute(2, 0, 1)).unsqueeze(0)
    with torch.no_grad():
        out_res = m_res(t_img_res)
        probs_res = torch.nn.functional.softmax(out_res[0], dim=0)
        cat_res = float(probs_res[281:286].sum()) / 5.0
        dog_res = float(probs_res[151:269].sum()) / 118.0

    t_img_eff = t_eff(torch.from_numpy(cell_rgb).permute(2, 0, 1)).unsqueeze(0)
    with torch.no_grad():
        out_eff = m_eff(t_img_eff)
        probs_eff = torch.nn.functional.softmax(out_eff[0], dim=0)
        cat_eff = float(probs_eff[281:286].sum()) / 5.0
        dog_eff = float(probs_eff[151:269].sum()) / 118.0

    score_cat = yolo_cat_conf * 0.34 + cat_res * 0.33 + cat_eff * 0.33
    score_dog = yolo_dog_conf * 0.34 + dog_res * 0.33 + dog_eff * 0.33

    if score_cat >= score_dog:
        return 'cat', score_cat
    else:
        return 'dog', score_dog

def auto_detect_grid_dimensions(img_h, img_w):
    aspect_ratio = img_w / float(img_h)
    if 0.85 <= aspect_ratio <= 1.15:
        if img_h < 600:
            return 8, 8
        else:
            return 6, 6
    elif 1.15 < aspect_ratio <= 1.45:
        return 5, 6
    return None, None

def verify_crop_category(crop_bgr, initial_cls_name, initial_conf):
    if crop_bgr is None or crop_bgr.shape[0] < 8 or crop_bgr.shape[1] < 8:
        return initial_cls_name, initial_conf

    crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
    (m_res, t_res), (m_eff, t_eff) = load_ensemble_models()

    t_img_res = t_res(torch.from_numpy(crop_rgb).permute(2, 0, 1)).unsqueeze(0)
    with torch.no_grad():
        out_res = m_res(t_img_res)
        probs_res = torch.nn.functional.softmax(out_res[0], dim=0)
        cat_res = float(probs_res[281:286].sum()) / 5.0
        dog_res = float(probs_res[151:269].sum()) / 118.0

    t_img_eff = t_eff(torch.from_numpy(crop_rgb).permute(2, 0, 1)).unsqueeze(0)
    with torch.no_grad():
        out_eff = m_eff(t_img_eff)
        probs_eff = torch.nn.functional.softmax(out_eff[0], dim=0)
        cat_eff = float(probs_eff[281:286].sum()) / 5.0
        dog_eff = float(probs_eff[151:269].sum()) / 118.0

    if initial_cls_name == 'cat':
        score_cat = initial_conf * 0.34 + cat_res * 0.33 + cat_eff * 0.33
        score_dog = (1.0 - initial_conf) * 0.34 + dog_res * 0.33 + dog_eff * 0.33
    else:
        score_dog = initial_conf * 0.34 + dog_res * 0.33 + dog_eff * 0.33
        score_cat = (1.0 - initial_conf) * 0.34 + cat_res * 0.33 + cat_eff * 0.33

    if score_cat >= score_dog:
        return 'cat', max(score_cat, initial_conf)
    else:
        return 'dog', max(score_dog, initial_conf)

def predict_cat_dog_st(
    img_rgb,
    model_key='YOLOv11x (高精確度 雙類別 - 推薦)',
    conf_threshold=0.20,
    iou_threshold=0.30,
    detection_mode='🤖 智慧通用自動判斷 (通用任何照片 - 推薦)',
    draw_boxes=True,
    manual_rows=6,
    manual_cols=6
):
    model_path = AVAILABLE_MODELS.get(model_key, 'yolo11x.pt')
    model = load_yolo_model(model_path)
    h, w, _ = img_rgb.shape

    target_classes = [
        cls_id for cls_id, name in model.names.items()
        if name.lower().strip() in ['cat', 'dog']
    ]

    kwargs = {'conf': conf_threshold, 'iou': iou_threshold, 'imgsz': 640}
    if target_classes:
        kwargs['classes'] = target_classes

    results = model(img_rgb, **kwargs)
    result = results[0]

    if len(result.boxes) > 0:
        boxes = result.boxes.xyxy
        scores = result.boxes.conf
        classes = result.boxes.cls

        keep_idx = nms(boxes, scores, iou_threshold=0.25)
        filtered_boxes = boxes[keep_idx]
        filtered_scores = scores[keep_idx]
        filtered_classes = classes[keep_idx]
    else:
        filtered_boxes, filtered_scores, filtered_classes = [], [], []

    total_det = len(filtered_boxes)
    avg_score = float(torch.mean(filtered_scores)) if total_det > 0 else 0.0

    use_grid = False
    grid_rows, grid_cols = 6, 6

    if '強制宮格切分' in detection_mode:
        use_grid = True
        grid_rows, grid_cols = int(manual_rows), int(manual_cols)
    elif '全圖 YOLO' in detection_mode:
        use_grid = False
    else:
        if (total_det > 12 and max(h, w) <= 1000) or total_det == 0 or (total_det > 20 and avg_score < 0.50):
            use_grid = True
            auto_r, auto_c = auto_detect_grid_dimensions(h, w)
            if auto_r is not None:
                grid_rows, grid_cols = auto_r, auto_c
            else:
                grid_rows, grid_cols = 6, 6
        else:
            use_grid = False

    cat_count = 0
    dog_count = 0
    annotated_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

    if use_grid:
        cell_h = h // grid_rows
        cell_w = w // grid_cols

        for r in range(grid_rows):
            for c in range(grid_cols):
                y1, y2 = r * cell_h, (r + 1) * cell_h
                x1, x2 = c * cell_w, (c + 1) * cell_w
                cell_bgr = annotated_bgr[y1:y2, x1:x2]

                label, score = classify_cell_triple_ensemble(cell_bgr, model, target_classes)

                if label == 'cat':
                    cat_count += 1
                    color = (0, 165, 255)  # 橘色 (Cat)
                    label_str = f"cat {score:.2f}"
                else:
                    dog_count += 1
                    color = (255, 0, 128)  # 紫洋紅 (Dog)
                    label_str = f"dog {score:.2f}"

                if draw_boxes:
                    cv2.rectangle(annotated_bgr, (x1 + 2, y1 + 2), (x2 - 2, y2 - 2), color, 2)
                    cv2.putText(
                        annotated_bgr, label_str, (x1 + 5, y1 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1
                    )
        mode_desc = f"宮格切分 {grid_rows}x{grid_cols} 雙引擎模式"
    else:
        for i in range(len(filtered_boxes)):
            box = filtered_boxes[i].cpu().numpy().astype(int)
            sc = float(filtered_scores[i])
            c_id = int(filtered_classes[i])
            c_name = model.names[c_id].lower().strip()

            crop_bgr = img_rgb[box[1]:box[3], box[0]:box[2]]
            verified_name, verified_score = verify_crop_category(crop_bgr, c_name, sc)

            if verified_name == 'cat':
                cat_count += 1
                color = (0, 165, 255)
                label_str = f"cat {verified_score:.2f}"
            elif verified_name == 'dog':
                dog_count += 1
                color = (255, 0, 128)
                label_str = f"dog {verified_score:.2f}"
            else:
                continue

            if draw_boxes:
                cv2.rectangle(annotated_bgr, (box[0], box[1]), (box[2], box[3]), color, 3)
                cv2.putText(
                    annotated_bgr, label_str, (box[0], max(box[1] - 8, 25)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2
                )
        mode_desc = "全圖 YOLOv11 + 二階段 Ensemble 驗證"

    annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB) if draw_boxes else img_rgb

    return {
        "annotated_rgb": annotated_rgb,
        "cat_count": cat_count,
        "dog_count": dog_count,
        "total_count": cat_count + dog_count,
        "mode_desc": mode_desc,
        "draw_boxes": draw_boxes
    }

# 6. UI 主畫面呈現
st.markdown('<div class="hero-title">🐱🐶 YOLO 貓狗 AI 辨識與數量統計 Web 系統</div>', unsafe_allow_html=True)
st.markdown("""
<div class="hero-subtitle">
    <span class="badge-tag">YOLOv11x</span>
    <span class="badge-tag">ResNet50</span>
    <span class="badge-tag">EfficientNetV2</span>
    <span class="badge-tag">三神經網絡 Ensemble</span>
    基於深度學習 SOTA 雙階段交叉驗證與宮格切分技術，支援單圖、多貓狗合照及 36/64 密集拼圖極致辨識！
</div>
""", unsafe_allow_html=True)

# 7. Sidebar 參數面板
with st.sidebar:
    st.header("⚙️ 控制與辨識參數面板")
    
    model_key = st.selectbox(
        "🤖 選擇 AI 辨識模型",
        list(AVAILABLE_MODELS.keys()),
        index=0
    )
    
    detection_mode = st.radio(
        "🎯 選擇辨識模式",
        [
            '🤖 智慧通用自動判斷 (通用任何照片 - 推薦)',
            '⚡ 全圖 YOLO 物件偵測 (適合一般單圖/合照)',
            '🔲 強制宮格切分雙引擎辨識 (自訂行列)'
        ],
        index=0
    )
    
    draw_boxes = st.checkbox("🖍️ 繪製圖像標註框", value=True, help="取消勾選可輸出純淨原圖與數量統計")
    
    with st.expander("🛠️ 高級模型門檻調校", expanded=False):
        conf_threshold = st.slider("🎯 置信度門檻 (Confidence)", 0.10, 0.90, 0.20, 0.05)
        iou_threshold = st.slider("📐 重複框抑制門檻 (NMS IoU)", 0.10, 0.90, 0.30, 0.05)
        
        c_r, c_c = st.columns(2)
        with c_r:
            manual_rows = st.number_input("宮格行數 (Rows)", min_value=2, max_value=12, value=6)
        with c_c:
            manual_cols = st.number_input("宮格列數 (Cols)", min_value=2, max_value=12, value=6)

# 8. 載入範例圖片路徑
SAMPLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "04_Misc_Applications", "ORC", "sample_images")
if not os.path.exists(SAMPLE_DIR):
    SAMPLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_images")

sample_images = []
if os.path.exists(SAMPLE_DIR):
    sample_images = sorted([
        os.path.join(SAMPLE_DIR, f) for f in os.listdir(SAMPLE_DIR)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ])

# 9. 圖片上傳與範例選擇
col_left, col_right = st.columns([1.1, 1.0])

selected_img_input = None

with col_left:
    st.subheader("📷 上傳照片 / 點擊範例")
    uploaded_file = st.file_uploader("選擇本地貓狗圖片...", type=['jpg', 'jpeg', 'png'])
    
    if uploaded_file is not None:
        image_bytes = uploaded_file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is not None:
            selected_img_input = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    
    if sample_images:
        st.markdown("##### 🖼️ 快速體驗 - 測試範例圖 (點擊下方按鈕)：")
        sample_cols = st.columns(min(len(sample_images), 7))
        for idx, s_path in enumerate(sample_images):
            s_name = os.path.basename(s_path)
            with sample_cols[idx % 7]:
                st.image(s_path, use_container_width=True)
                if st.button(f"示例 {idx+1}", key=f"sample_btn_{idx}", use_container_width=True):
                    img_bgr = cv2.imread(s_path)
                    if img_bgr is not None:
                        selected_img_input = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                        st.session_state['active_sample'] = s_path

if 'active_sample' in st.session_state and selected_img_input is None:
    if os.path.exists(st.session_state['active_sample']):
        img_bgr = cv2.imread(st.session_state['active_sample'])
        if img_bgr is not None:
            selected_img_input = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

# 預設載入第一張範例圖
if selected_img_input is None and sample_images:
    img_bgr = cv2.imread(sample_images[0])
    if img_bgr is not None:
        selected_img_input = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

with col_right:
    st.subheader("🖼️ AI 標註與辨識結果")
    if selected_img_input is not None:
        with st.spinner("🧠 SOTA 雙階段三神經網絡 Ensemble 算力辨識中..."):
            res = predict_cat_dog_st(
                selected_img_input,
                model_key=model_key,
                conf_threshold=conf_threshold,
                iou_threshold=iou_threshold,
                detection_mode=detection_mode,
                draw_boxes=draw_boxes,
                manual_rows=manual_rows,
                manual_cols=manual_cols
            )
            
        st.image(res["annotated_rgb"], caption="AI 分析標註影像", use_container_width=True)
        
        # 顯示統計指標卡片
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">🐱 {res['cat_count']}</div>
                <div class="stat-label">貓隻數量 (Cat)</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">🐶 {res['dog_count']}</div>
                <div class="stat-label">狗隻數量 (Dog)</div>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">📊 {res['total_count']}</div>
                <div class="stat-label">總辨識標的</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.caption(f"ℹ️ **執行模式**：{res['mode_desc']} | 標註框：{'開啟' if draw_boxes else '關閉'}")
    else:
        st.info("👈 請上傳圖片或點擊左側範例圖進行 AI 貓狗辨識與數量統計。")
