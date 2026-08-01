import os, sys
_dir = os.path.dirname(os.path.abspath(__file__))
if _dir not in sys.path:
    sys.path.insert(0, _dir)
try:
    from utils.data_generator import generate_data
except ImportError:
    from data_generator import generate_data

st.set_page_config(page_title="SVM 核技巧 3D v2.2", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0F1117;
        color: #F3F4F6;
    }
    header[data-testid="stHeader"] {
        background-color: rgba(0,0,0,0);
    }
    section[data-testid="stSidebar"] {
        background-color: #0F1117 !important;
        border-right: 1px solid #1E293B !important;
    }
    div[data-testid="stSidebarCollapseButton"] {
        color: white;
    }
    .pill-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        font-size: 0.85rem;
        font-weight: 600;
        border-radius: 9999px;
        background-color: #1E293B;
        color: #38BDF8;
        border: 1px solid #2563EB;
        margin-bottom: 1.5rem;
    }
    .pill-badge-purple {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        font-size: 0.75rem;
        font-weight: 700;
        border-radius: 9999px;
        background-color: #6366F1;
        color: white;
        margin-left: 0.5rem;
    }
    .section-header {
        font-size: 0.8rem;
        font-weight: 700;
        color: #9CA3AF;
        letter-spacing: 0.05em;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
    }
    div.stButton > button {
        background-color: #6366F1 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100%;
        font-weight: bold;
        padding: 0.5rem 1rem;
        transition: background-color 0.2s;
    }
    div.stButton > button:hover {
        background-color: #4F46E5 !important;
    }
    .caption-box {
        background-color: #161922;
        border-left: 4px solid #6366F1;
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
        margin-bottom: 1.5rem;
        border: 1px solid #232735;
        border-left: 4px solid #6366F1;
    }
    .insight-card {
        background-color: #161922;
        border-radius: 8px;
        padding: 1.25rem;
        height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    }
    .footer-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-top: 1px solid #232735;
        padding-top: 1rem;
        margin-top: 2rem;
        color: #6B7280;
        font-size: 0.85rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "animate" not in st.session_state:
    st.session_state.animate = True
if "frame_index" not in st.session_state:
    st.session_state.frame_index = 0
if "data_seed" not in st.session_state:
    st.session_state.data_seed = 42
if "reset_clicked" not in st.session_state:
    st.session_state.reset_clicked = False

st.sidebar.markdown(
    '<div style="display: flex; align-items: center; margin-bottom: 0.5rem;">'
    '<span style="font-size: 1.6rem; font-weight: 800; color: white;">SVM 核技巧 3D</span>'
    '<span class="pill-badge-purple">v2.2</span>'
    '</div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    '<p style="color: #9CA3AF; font-size: 0.9rem; margin-bottom: 1.25rem; line-height: 1.4;">'
    "了解 SVM 如何利用核技巧在高維空間中找到線性分隔面"
    "</p>",
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    '<div class="pill-badge">z = x² + y²（教學用）</div>',
    unsafe_allow_html=True,
)

st.sidebar.markdown('<div class="section-header">資料</div>', unsafe_allow_html=True)
dataset_label = st.sidebar.selectbox(
    "資料集",
    ["同心圓", "月牙形", "群聚"],
    label_visibility="collapsed",
)
st.sidebar.markdown(
    '<div style="font-size: 0.85rem; margin-top: 0.5rem; color: #9CA3AF;">樣本數量</div>',
    unsafe_allow_html=True,
)
n_samples = st.sidebar.slider(
    "樣本數量", 50, 500, 200, 10, label_visibility="collapsed"
)
st.sidebar.markdown(
    '<div style="font-size: 0.85rem; margin-top: 0.5rem; color: #9CA3AF;">雜訊</div>',
    unsafe_allow_html=True,
)
noise = st.sidebar.slider(
    "雜訊", 0.0, 0.2, 0.05, 0.01, label_visibility="collapsed"
)

st.sidebar.markdown(
    '<div class="section-header">模型</div>', unsafe_allow_html=True
)
st.sidebar.markdown(
    '<div style="font-size: 0.85rem; color: #9CA3AF; margin-bottom: 0.25rem;">核函數</div>',
    unsafe_allow_html=True,
)
kernel_label = st.sidebar.selectbox(
    "核函數",
    ["RBF (高斯)", "Linear (線性)", "Polynomial (多項式)"],
    label_visibility="collapsed",
)
kernel_map = {
    "RBF (高斯)": "rbf",
    "Linear (線性)": "linear",
    "Polynomial (多項式)": "poly",
}
kernel = kernel_map[kernel_label]

st.sidebar.markdown(
    '<div style="font-size: 0.85rem; color: #9CA3AF; margin-top: 0.5rem;">C (正則化)</div>',
    unsafe_allow_html=True,
)
c_options = [0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0]
C = st.sidebar.select_slider(
    "C (正則化)", options=c_options, value=1.0, label_visibility="collapsed"
)

if kernel in ["rbf", "poly"]:
    st.sidebar.markdown(
        '<div style="font-size: 0.85rem; color: #9CA3AF; margin-top: 0.5rem;">Gamma</div>',
        unsafe_allow_html=True,
    )
    gamma_options = [0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
    gamma = st.sidebar.select_slider(
        "Gamma", options=gamma_options, value=1.0, label_visibility="collapsed"
    )
else:
    gamma = "scale"

st.sidebar.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
show_sv_only = st.sidebar.toggle("僅顯示支援向量", value=False)

st.sidebar.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
if st.sidebar.button("↻ 重新產生資料"):
    st.session_state.data_seed += 1

st.sidebar.markdown(
    '<div class="section-header">視覺設定</div>', unsafe_allow_html=True
)
st.sidebar.markdown(
    '<div style="font-size: 0.85rem; color: #9CA3AF; margin-top: 0.5rem;">決策邊界解析度</div>',
    unsafe_allow_html=True,
)
resolution = st.sidebar.slider(
    "決策邊界解析度", 50, 300, 100, 50, label_visibility="collapsed"
)

st.sidebar.markdown(
    '<div style="font-size: 0.85rem; color: #9CA3AF; margin-top: 0.5rem;">2D 色彩主題</div>',
    unsafe_allow_html=True,
)
colorscale = st.sidebar.selectbox(
    "2D 色彩主題",
    ["RdBu", "Viridis", "Plasma", "Spectral"],
    label_visibility="collapsed",
)

st.sidebar.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
show_contour = st.sidebar.checkbox("顯示決策邊界等高線", value=True)

st.sidebar.markdown(
    '<div style="font-size: 0.85rem; color: #9CA3AF; margin-top: 0.5rem;">3D 曲面透明度</div>',
    unsafe_allow_html=True,
)
opacity = st.sidebar.slider(
    "3D 曲面透明度", 0.1, 0.6, 0.25, 0.05, label_visibility="collapsed"
)

st.sidebar.markdown(
    '<div class="section-header">動畫設定</div>', unsafe_allow_html=True
)
st.sidebar.toggle("▶ 播放 / ⏸ 暫停", value=True, key="animate")
anim_speed = st.sidebar.slider("動畫速度", 1, 10, 5)
anim_mode = st.sidebar.radio(
    "動畫模式",
    ["訓練過程", "決策邊界掃描", "支援向量脈衝"],
)
loop_play = st.sidebar.toggle("循環播放", value=True)

force_reset = False
if st.sidebar.button("⏮ 重置動畫"):
    st.session_state.frame_index = 0
    st.session_state.reset_clicked = True
    st.rerun()

st.sidebar.markdown(
    """
    <div style="background-color: #161922; border-left: 4px solid #2563EB; border-radius: 8px; padding: 1rem; margin-top: 1.5rem; border: 1px solid #232735; border-left: 4px solid #2563EB;">
        <div style="color: #38BDF8; font-weight: 700; font-size: 0.9rem; margin-bottom: 0.25rem; display: flex; align-items: center;">
            <span style="margin-right: 0.5rem;">ℹ️</span> 教學說明
        </div>
        <div style="color: #9CA3AF; font-size: 0.8rem; line-height: 1.4;">
            我們利用 z = x² + y²（拋物面）進行投影以建立直觀理解。真實的 RBF 核函數會將資料點映射至無限維空間。
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    """
    <div style="background-color: #161922; border-left: 4px solid #D97706; border-radius: 8px; padding: 1rem; margin-top: 1rem; border: 1px solid #232735; border-left: 4px solid #D97706;">
        <div style="color: #FBBF24; font-weight: 700; font-size: 0.9rem; margin-bottom: 0.25rem; display: flex; align-items: center;">
            <span style="margin-right: 0.5rem;">💡</span> 提示
        </div>
        <div style="color: #9CA3AF; font-size: 0.8rem; line-height: 1.4;">
            支援向量（白色空心圓）是定義分隔邊界的關鍵資料點。
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def train_model(dataset_type, n_samples, noise, kernel, C, gamma, seed):
    X, y = generate_data(
        n_samples=n_samples, noise=noise, seed=seed, dataset_type=dataset_type
    )
    svc = SVC(kernel=kernel, C=C, gamma=gamma, probability=False)
    svc.fit(X, y)
    return X, y, svc


def build_2d_figure(
    X, y, svc, resolution, colorscale, show_contour, show_sv_only
):
    x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
    y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5

    xx, yy = np.meshgrid(
        np.linspace(x_min, x_max, resolution),
        np.linspace(y_min, y_max, resolution),
    )
    grid = np.c_[xx.ravel(), yy.ravel()]
    Z_pred = svc.decision_function(grid).reshape(xx.shape)

    fig = go.Figure()

    fig.add_trace(
        go.Contour(
            x=np.linspace(x_min, x_max, resolution),
            y=np.linspace(y_min, y_max, resolution),
            z=Z_pred,
            colorscale=colorscale,
            opacity=0.3,
            showscale=False,
            contours_coloring="fill",
            line=dict(width=0),
            hoverinfo="skip",
        )
    )

    if show_contour:
        fig.add_trace(
            go.Contour(
                x=np.linspace(x_min, x_max, resolution),
                y=np.linspace(y_min, y_max, resolution),
                z=Z_pred,
                showscale=False,
                contours=dict(start=0, end=0, size=1),
                line=dict(color="white", width=2),
                contours_coloring="none",
                hoverinfo="skip",
            )
        )

    c0_mask = y == 0
    c1_mask = y == 1

    if show_sv_only:
        sv_idx = svc.support_
        sv_c0 = [i for i in sv_idx if y[i] == 0]
        sv_c1 = [i for i in sv_idx if y[i] == 1]

        fig.add_trace(
            go.Scatter(
                x=X[sv_c0, 0],
                y=X[sv_c0, 1],
                mode="markers",
                marker=dict(
                    size=8, color="#4C9BE8", line=dict(color="black", width=0.5)
                ),
                name="類別 0 (支援向量)",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=X[sv_c1, 0],
                y=X[sv_c1, 1],
                mode="markers",
                marker=dict(
                    size=8, color="#F97316", line=dict(color="black", width=0.5)
                ),
                name="類別 1 (支援向量)",
            )
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=X[c0_mask, 0],
                y=X[c0_mask, 1],
                mode="markers",
                marker=dict(
                    size=8, color="#4C9BE8", line=dict(color="black", width=0.5)
                ),
                name="類別 0",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=X[c1_mask, 0],
                y=X[c1_mask, 1],
                mode="markers",
                marker=dict(
                    size=8, color="#F97316", line=dict(color="black", width=0.5)
                ),
                name="類別 1",
            )
        )

        if len(svc.support_) > 0:
            sv_idx = svc.support_
            fig.add_trace(
                go.Scatter(
                    x=X[sv_idx, 0],
                    y=X[sv_idx, 1],
                    mode="markers",
                    marker=dict(
                        size=14,
                        color="rgba(0,0,0,0)",
                        line=dict(color="white", width=2),
                        symbol="circle-open",
                    ),
                    name="支援向量",
                )
            )

    n_sv = len(svc.support_)
    fig.add_annotation(
        text=f"支援向量數: {n_sv}",
        xref="paper",
        yref="paper",
        x=0.98,
        y=0.98,
        showarrow=False,
        font=dict(color="white", size=12),
        bgcolor="rgba(22, 25, 34, 0.8)",
        bordercolor="#232735",
        borderwidth=1,
        borderpad=6,
    )

    fig.update_layout(
        paper_bgcolor="#0F1117",
        plot_bgcolor="#0F1117",
        margin=dict(l=20, r=20, b=20, t=20),
        xaxis=dict(
            color="#9CA3AF", gridcolor="#232735", zerolinecolor="#232735"
        ),
        yaxis=dict(
            color="#9CA3AF", gridcolor="#232735", zerolinecolor="#232735"
        ),
        legend=dict(
            x=0.02,
            y=0.02,
            bgcolor="rgba(22, 25, 34, 0.8)",
            bordercolor="#232735",
            borderwidth=1,
            font=dict(color="#F3F4F6"),
        ),
        height=450,
    )
    return fig


def build_3d_figure(X, y, svc, resolution, opacity, show_sv_only):
    x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
    y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5

    xx, yy = np.meshgrid(
        np.linspace(x_min, x_max, resolution),
        np.linspace(y_min, y_max, resolution),
    )
    zz_shape = xx**2 + yy**2

    grid = np.c_[xx.ravel(), yy.ravel()]
    zz_decision = svc.decision_function(grid).reshape(xx.shape)

    fig = go.Figure()

    fig.add_trace(
        go.Surface(
            x=xx,
            y=yy,
            z=zz_shape,
            surfacecolor=zz_decision,
            colorscale="Viridis",
            opacity=opacity,
            showscale=True,
            colorbar=dict(
                orientation="h",
                y=-0.15,
                x=0.5,
                xanchor="center",
                title=dict(
                    text="決策函數 f(x)",
                    side="top",
                    font=dict(color="#9CA3AF"),
                ),
                thickness=15,
                len=0.7,
                tickfont=dict(color="#9CA3AF"),
            ),
        )
    )

    z_points = X[:, 0] ** 2 + X[:, 1] ** 2

    c0_mask = y == 0
    c1_mask = y == 1

    if show_sv_only:
        sv_idx = svc.support_
        sv_c0 = [i for i in sv_idx if y[i] == 0]
        sv_c1 = [i for i in sv_idx if y[i] == 1]

        fig.add_trace(
            go.Scatter3d(
                x=X[sv_c0, 0],
                y=X[sv_c0, 1],
                z=z_points[sv_c0],
                mode="markers",
                marker=dict(size=5, color="#4C9BE8", opacity=0.9),
                name="類別 0 (支援向量)",
            )
        )
        fig.add_trace(
            go.Scatter3d(
                x=X[sv_c1, 0],
                y=X[sv_c1, 1],
                z=z_points[sv_c1],
                mode="markers",
                marker=dict(size=5, color="#F97316", opacity=0.9),
                name="類別 1 (支援向量)",
            )
        )
    else:
        fig.add_trace(
            go.Scatter3d(
                x=X[c0_mask, 0],
                y=X[c0_mask, 1],
                z=z_points[c0_mask],
                mode="markers",
                marker=dict(size=5, color="#4C9BE8", opacity=0.9),
                name="類別 0",
            )
        )
        fig.add_trace(
            go.Scatter3d(
                x=X[c1_mask, 0],
                y=X[c1_mask, 1],
                z=z_points[c1_mask],
                mode="markers",
                marker=dict(size=5, color="#F97316", opacity=0.9),
                name="類別 1",
            )
        )

        if len(svc.support_) > 0:
            sv_idx = svc.support_
            fig.add_trace(
                go.Scatter3d(
                    x=X[sv_idx, 0],
                    y=X[sv_idx, 1],
                    z=z_points[sv_idx],
                    mode="markers",
                    marker=dict(
                        size=12,
                        color="rgba(0,0,0,0)",
                        line=dict(color="white", width=2),
                        symbol="circle-open",
                    ),
                    name="支援向量",
                )
            )

    fig.update_layout(
        margin=dict(l=0, r=0, b=0, t=0),
        scene=dict(
            xaxis=dict(
                title="X",
                color="#9CA3AF",
                gridcolor="#232735",
                backgroundcolor="#0F1117",
                showbackground=True,
            ),
            yaxis=dict(
                title="Y",
                color="#9CA3AF",
                gridcolor="#232735",
                backgroundcolor="#0F1117",
                showbackground=True,
            ),
            zaxis=dict(
                title="Z",
                color="#9CA3AF",
                gridcolor="#232735",
                backgroundcolor="#0F1117",
                showbackground=True,
            ),
            bgcolor="#0F1117",
        ),
        paper_bgcolor="#0F1117",
        plot_bgcolor="#0F1117",
        height=450,
        legend=dict(
            x=0.05,
            y=0.95,
            bgcolor="rgba(22, 25, 34, 0.8)",
            bordercolor="#232735",
            borderwidth=1,
            font=dict(color="#F3F4F6"),
        ),
    )
    return fig


def make_frame(X_sub, y_sub, Z, xx, yy, contour_opacity, sv_size, sv_idx=None, phase="A", title=""):
    points = []
    for i in range(len(X_sub)):
        cls = int(y_sub[i])
        color = "#4C9BE8" if cls == 0 else "#F97316"
        opacity = 0.9
        if sv_idx is not None:
            if i not in sv_idx:
                opacity = 0.3
        points.append({
            "x": float(X_sub[i, 0]),
            "y": float(X_sub[i, 1]),
            "color": color,
            "opacity": opacity,
            "size": 8
        })
    
    return {
        "points": points,
        "contour_z": Z.tolist(),
        "contour_x": xx[0].tolist(),
        "contour_y": yy[:, 0].tolist(),
        "contour_opacity": float(contour_opacity),
        "sv_indices": [int(idx) for idx in sv_idx] if sv_idx is not None else [],
        "sv_size": float(sv_size),
        "phase": phase,
        "title": title
    }


@st.cache_data
def build_all_frames(X, y, _svc, resolution, colorscale, mode):
    xx, yy = np.meshgrid(np.linspace(-1.5, 1.5, resolution), np.linspace(-1.5, 1.5, resolution))
    Z = _svc.decision_function(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)
    sv_idx = _svc.support_

    frames = []
    
    if mode in ["訓練過程", "Training Process"]:
        # Phase A: 20 frames — points appear cumulatively, eased
        geom = np.geomspace(1, len(X), 20, dtype=int)
        for n in geom:
            frames.append(make_frame(X[:n], y[:n], Z * 0, xx, yy, contour_opacity=0.0, sv_size=0, phase="A", title="① 原始 2D 資料"))

        # Phase B: 15 frames — contour fades in, boundary draws
        for alpha in np.linspace(0.0, 0.4, 15):
            frames.append(make_frame(X, y, Z, xx, yy, contour_opacity=alpha, sv_size=0, phase="B", title="② SVM 學習決策邊界..."))

        # Phase C: 10 frames — SV pulse using sine wave
        for t in np.linspace(0, 2 * np.pi, 10):
            sv_size = 12.0 + 5.0 * np.sin(t)
            frames.append(make_frame(X, y, Z, xx, yy, contour_opacity=0.4, sv_size=sv_size, sv_idx=sv_idx, phase="C", title="③ 支援向量決定邊界"))

    elif mode in ["決策邊界掃描", "Sweep C"]:
        # Sweep C parameter across 30 frames
        sweep_frames = 30
        c_sweep = np.logspace(-2, 2, sweep_frames)
        for c_val in c_sweep:
            sweep_svc = SVC(kernel=_svc.kernel, C=c_val, gamma=_svc.gamma, random_state=42)
            sweep_svc.fit(X, y)
            Z_sweep = sweep_svc.decision_function(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)
            sv_idx_sweep = sweep_svc.support_
            frames.append(make_frame(X, y, Z_sweep, xx, yy, contour_opacity=0.3, sv_size=14, sv_idx=sv_idx_sweep, phase="SWEEP", title=f"決策邊界掃描 (C={c_val:.2f})"))

    elif mode in ["支援向量脈衝", "Pulse SV"]:
        # Pulse SV only across 10 frames
        for t in np.linspace(0, 2 * np.pi, 10):
            sv_size = 12.0 + 5.0 * np.sin(t)
            frames.append(make_frame(X, y, Z, xx, yy, contour_opacity=0.4, sv_size=sv_size, sv_idx=sv_idx, phase="PULSE", title="支援向量脈衝"))

    return frames


def build_animation_html(frames_data: list[dict], speed_ms: int, loop: bool, colorscale: str, show_contour_line: bool, autoplay: bool, force_reset_state: bool) -> str:
    frames_json = json.dumps(frames_data)
    force_reset_js = "true" if force_reset_state else "false"
    loop_js = "true" if loop else "false"
    autoplay_js = "true" if autoplay else "false"
    show_contour_line_js = "true" if show_contour_line else "false"

    html_template = f"""
    <style>
      body {{
        background-color: #0F1117;
        margin: 0;
        padding: 0;
        overflow: hidden;
      }}
    </style>
    <div id="plot" style="width: 100%; height: 480px; margin: 0 auto;"></div>
    
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <script>
      const frames = {frames_json};
      const SPEED_MS = {speed_ms};
      const LOOP = {loop_js};
      let AUTO_PLAY = {autoplay_js};
      const FORCE_RESET = {force_reset_js};
      const COLORSCALE = "{colorscale}";
      const SHOW_CONTOUR_LINE = {show_contour_line_js};

      if (FORCE_RESET) {{
        localStorage.setItem('svm_frame_index', '0');
      }}

      let i = parseInt(localStorage.getItem('svm_frame_index') || '0');
      if (i >= frames.length) i = 0;

      const phaseLabels = {{
        'A': '① 原始 2D 資料',
        'B': '② SVM 學習決策邊界...',
        'C': '③ 支援向量決定邊界',
        'SWEEP': '決策邊界掃描',
        'PULSE': '支援向量脈衝'
      }};

      function updateParentProgress(f) {{
        try {{
          const parentDoc = window.parent.document;
          const progressEl = parentDoc.querySelector('div[data-testid="stProgress"]');
          if (progressEl) {{
            let percent = 0;
            let phaseLabel = phaseLabels[f.phase] || f.title;
            if (f.phase === 'A') percent = 33.3;
            else if (f.phase === 'B') percent = 66.6;
            else if (f.phase === 'C') percent = 100;
            else percent = 100;

            const barFill = progressEl.querySelector('div[role="progressbar"] div');
            if (barFill) barFill.style.width = percent + '%';

            let labelDiv = null;
            const divs = progressEl.getElementsByTagName('div');
            for (let d of divs) {{
              if (d.childNodes.length === 1 && d.childNodes[0].nodeType === 3) {{
                const txt = d.innerText;
                if (txt && (txt.includes('①') || txt.includes('②') || txt.includes('③') || txt.includes('決策') || txt.includes('支援'))) {{
                  labelDiv = d;
                  break;
                }}
              }}
            }}
            if (!labelDiv) {{
              labelDiv = progressEl.querySelector('div');
            }}
            if (labelDiv) labelDiv.innerText = phaseLabel;
          }}
        }} catch(e) {{
          console.error("Error updating parent progress:", e);
        }}
      }}

      function buildTraces(f) {{
        const traces = [];
        
        // 1. Contour background
        if (f.contour_opacity > 0) {{
          traces.push({{
            x: f.contour_x,
            y: f.contour_y,
            z: f.contour_z,
            type: 'contour',
            colorscale: COLORSCALE,
            opacity: f.contour_opacity,
            showscale: false,
            contours_coloring: 'fill',
            line: {{ width: 0 }},
            hoverinfo: 'skip'
          }});

          // 2. Decision boundary line
          if (SHOW_CONTOUR_LINE) {{
            traces.push({{
              x: f.contour_x,
              y: f.contour_y,
              z: f.contour_z,
              type: 'contour',
              showscale: false,
              contours: {{ start: 0, end: 0, size: 1 }},
              line: {{ color: 'white', width: 2 }},
              contours_coloring: 'none',
              hoverinfo: 'skip'
            }});
          }}
        }}

        // 3. Scatter points
        const c0_x = [], c0_y = [], c0_op = [];
        const c1_x = [], c1_y = [], c1_op = [];
        for (let p of f.points) {{
          if (p.color === "#4C9BE8") {{
            c0_x.push(p.x);
            c0_y.push(p.y);
            c0_op.push(p.opacity);
          }} else {{
            c1_x.push(p.x);
            c1_y.push(p.y);
            c1_op.push(p.opacity);
          }}
        }}

        traces.push({{
          x: c0_x,
          y: c0_y,
          mode: 'markers',
          type: 'scatter',
          marker: {{
            size: 8,
            color: '#4C9BE8',
            opacity: c0_op,
            line: {{ color: 'black', width: 0.5 }}
          }},
          name: '類別 0'
        }});

        traces.push({{
          x: c1_x,
          y: c1_y,
          mode: 'markers',
          type: 'scatter',
          marker: {{
            size: 8,
            color: '#F97316',
            opacity: c1_op,
            line: {{ color: 'black', width: 0.5 }}
          }},
          name: '類別 1'
        }});

        // 4. Support vectors
        if (f.sv_size > 0 && f.sv_indices.length > 0) {{
          const sv_x = [];
          const sv_y = [];
          for (let idx of f.sv_indices) {{
            if (idx < f.points.length) {{
              sv_x.push(f.points[idx].x);
              sv_y.push(f.points[idx].y);
            }}
          }}
          if (sv_x.length > 0) {{
            traces.push({{
              x: sv_x,
              y: sv_y,
              mode: 'markers',
              type: 'scatter',
              marker: {{
                size: f.sv_size,
                color: 'rgba(0,0,0,0)',
                line: {{ color: 'white', width: 2 }},
                symbol: 'circle-open'
              }},
              name: '支援向量'
            }});
          }}
        }}

        return traces;
      }}

      const layout = {{
        paper_bgcolor: '#0F1117',
        plot_bgcolor: '#0F1117',
        margin: {{ l: 20, r: 20, b: 20, t: 30 }},
        xaxis: {{ color: '#9CA3AF', gridcolor: '#232735', zerolinecolor: '#232735', range: [-1.8, 1.8] }},
        yaxis: {{ color: '#9CA3AF', gridcolor: '#232735', zerolinecolor: '#232735', range: [-1.8, 1.8] }},
        legend: {{
          x: 0.02,
          y: 0.02,
          bgcolor: 'rgba(22, 25, 34, 0.8)',
          bordercolor: '#232735',
          borderwidth: 1,
          font: {{ color: '#F3F4F6' }}
        }},
        title: {{
          text: frames[i].title,
          font: {{ color: '#FFFFFF', size: 14 }}
        }},
        annotations: [{{
          text: `支援向量數: ${{frames[i].sv_indices.length}}`,
          xref: 'paper',
          yref: 'paper',
          x: 0.98,
          y: 0.98,
          showarrow: false,
          font: {{ color: 'white', size: 12 }},
          bgcolor: 'rgba(22, 25, 34, 0.8)',
          bordercolor: '#232735',
          borderwidth: 1,
          borderpad: 6
        }}],
        height: 480
      }};

      const config = {{ staticPlot: false, displayModeBar: false }};

      Plotly.newPlot('plot', buildTraces(frames[i]), layout, config);
      updateParentProgress(frames[i]);

      let timer = null;

      function nextFrame() {{
        if (!AUTO_PLAY) return;
        
        i = (i + 1) % frames.length;
        if (!LOOP && i === 0) {{
          i = frames.length - 1;
          localStorage.setItem('svm_frame_index', i);
          updateParentProgress(frames[i]);
          return;
        }}

        const f = frames[i];
        localStorage.setItem('svm_frame_index', i);
        updateParentProgress(f);

        Plotly.animate('plot', {{
          data: buildTraces(f),
          layout: {{ 
            title: {{ text: f.title }},
            annotations: [{{
              text: `支援向量數: ${{f.sv_indices.length}}`,
              xref: 'paper',
              yref: 'paper',
              x: 0.98,
              y: 0.98,
              showarrow: false,
              font: {{ color: 'white', size: 12 }},
              bgcolor: 'rgba(22, 25, 34, 0.8)',
              bordercolor: '#232735',
              borderwidth: 1,
              borderpad: 6
            }}]
          }}
        }}, {{
          transition: {{ duration: SPEED_MS, easing: 'cubic-in-out' }},
          frame: {{ duration: SPEED_MS, redraw: false }}
        }});

        timer = setTimeout(nextFrame, SPEED_MS);
      }}

      if (AUTO_PLAY) {{
        timer = setTimeout(nextFrame, 500);
      }}

      window.addEventListener('message', e => {{
        if (e.data.pause) {{
          AUTO_PLAY = false;
          clearTimeout(timer);
        }}
        if (e.data.resume) {{
          AUTO_PLAY = true;
          nextFrame();
        }}
      }});
    </script>
    """
    return html_template


X, y, svc = train_model(
    dataset_label,
    n_samples,
    noise,
    kernel,
    C,
    gamma,
    st.session_state.data_seed,
)

y_pred = svc.predict(X)
acc = np.mean(y_pred == y)
n_sv = len(svc.support_)

col_center, col_right = st.columns([1, 1], gap="medium")

with col_center:
    st.markdown(
        '<h3 style="margin-bottom: 0.25rem; color: white;">1. 2D 原始資料 (z = 0) — 決策邊界</h3>',
        unsafe_allow_html=True,
    )

    m_col1, m_col2, m_col3 = st.columns(3)
    metric1 = m_col1.empty()
    metric2 = m_col2.empty()
    metric3 = m_col3.empty()

    progress_placeholder = st.empty()
    plot_2d_placeholder = st.empty()
    caption_box_placeholder = st.empty()

with col_right:
    st.markdown(
        '<h3 style="margin-bottom: 1.5rem; color: white;">3D 視圖：提升後的資料與 SVM 決策曲面</h3>',
        unsafe_allow_html=True,
    )
    plot_3d_placeholder = st.empty()
    caption_3d_placeholder = st.empty()

metric1.metric("準確率", f"{acc:.1%}")
metric2.metric("支援向量數", f"{n_sv}")
metric3.metric("訓練樣本數", f"{n_samples}")

fig_3d = build_3d_figure(X, y, svc, resolution, opacity, show_sv_only)
plot_3d_placeholder.plotly_chart(fig_3d, use_container_width=True, key="fig_3d_static")

if st.session_state.animate:
    caption_3d_placeholder.caption("動畫播放中，3D 顯示最終結果")
else:
    caption_3d_placeholder.write("")

caption_box_placeholder.markdown(
    """
    <div class="caption-box">
        <div style="color: #A5B4FC; font-size: 0.85rem; line-height: 1.4; display: flex; align-items: flex-start;">
            <span style="margin-right: 0.5rem; font-size: 1.1rem;">✨</span>
            <div><strong>您正在觀看：</strong>非線性可分的同心圓在 2D 空間中，經由 3D 提升後變得線性可分。</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<h3 style="margin-top: 1rem; margin-bottom: 0.5rem; color: white;">💡 參數解析</h3>',
    unsafe_allow_html=True,
)

col_i1, col_i2, col_i3, col_i4 = st.columns(4, gap="medium")

kernel_desc_map = {
    "rbf": "將資料映射至（虛擬的）無限維空間，使原本非線性可分的資料可以被線性分隔。RBF 具有極佳彈性，能處理複雜的非線性邊界。",
    "linear": "在原始 2D 空間中擬合一條直線分隔超平面。簡單快速，但完全無法分隔同心圓等嵌套資料集。",
    "poly": "將特徵映射到多項式組合空間，允許擬合出具備特定階數的彎曲多項式決策邊界。",
}

with col_i1:
    st.markdown(
        f"""
        <div class="insight-card" style="border: 1px solid #3B82F6;">
            <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
                <span style="font-size: 1.5rem; margin-right: 0.5rem; color: #3B82F6;">🎯</span>
                <strong style="color: white; font-size: 1rem;">核函數 ({kernel.upper()})</strong>
            </div>
            <div style="color: #9CA3AF; font-size: 0.8rem; line-height: 1.4;">
                {kernel_desc_map[kernel]}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_i2:
    if C >= 10.0:
        c_detail = "<b>目前設定為高 C 值</b>：模型對錯分點的懲罰極高，會強求將所有訓練點分類正確，導致間距變窄，<b>極易產生過擬合風險</b>。"
    elif C <= 0.1:
        c_detail = "<b>目前設定為低 C 值</b>：模型容忍較多錯分點以換取更寬的間距，<b>邊界形狀較為平滑且具一般化</b>。"
    else:
        c_detail = "<b>目前設定為中等 C 值</b>：在訓練集準確率與邊界間距寬度之間取得平衡。"

    st.markdown(
        f"""
        <div class="insight-card" style="border: 1px solid #10B981;">
            <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
                <span style="font-size: 1.5rem; margin-right: 0.5rem; color: #10B981;">⚖️</span>
                <strong style="color: white; font-size: 1rem;">C (正則化)</strong>
            </div>
            <div style="color: #9CA3AF; font-size: 0.8rem; line-height: 1.4;">
                <div style="margin-bottom: 0.5rem;">▶ 小 C &rarr; 較寬的間距，容忍較多錯分。</div>
                <div style="margin-bottom: 0.5rem;">▶ 大 C &rarr; 較窄的間距，強求分類正確。</div>
                <div style="border-top: 1px solid #232735; padding-top: 0.5rem; color: #E5E7EB;">
                    {c_detail}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_i3:
    if kernel in ["rbf", "poly"]:
        if gamma == "scale":
            gamma_val = 1.0 / (X.shape[1] * X.var())
        else:
            gamma_val = gamma

        if gamma_val >= 2.0:
            gamma_detail = "<b>目前設定為高 Gamma 值</b>：單一資料點的影響半徑非常小，邊界呈圍繞點的<b>『島嶼狀』，極易過擬合</b>。"
        elif gamma_val <= 0.1:
            gamma_detail = "<b>目前設定為低 Gamma 值</b>：資料點影響半徑極大，決策曲面<b>非常平滑且一般化</b>。"
        else:
            gamma_detail = "<b>目前設定為中等 Gamma 值</b>：資料點影響半徑均衡，曲面複雜度適中。"
    else:
        gamma_detail = "線性（Linear）核函數不使用 Gamma 參數。"

    st.markdown(
        f"""
        <div class="insight-card" style="border: 1px solid #F59E0B;">
            <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
                <span style="font-size: 1.5rem; margin-right: 0.5rem; color: #F59E0B;">〰️</span>
                <strong style="color: white; font-size: 1rem;">Gamma ({kernel.upper()})</strong>
            </div>
            <div style="color: #9CA3AF; font-size: 0.8rem; line-height: 1.4;">
                <div style="margin-bottom: 0.5rem;">▶ 小 gamma &rarr; 支援向量影響範圍大，曲面平滑。</div>
                <div style="margin-bottom: 0.5rem;">▶ 大 gamma &rarr; 支援向量影響範圍小，曲面陡峭。</div>
                <div style="border-top: 1px solid #232735; padding-top: 0.5rem; color: #E5E7EB;">
                    {gamma_detail}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_i4:
    if noise >= 0.12:
        noise_detail = "<b>目前設定為高雜訊</b>：資料分布重疊度高，導致類別混合，<b>極大增加了線性分隔難度</b>。"
    elif noise <= 0.03:
        noise_detail = "<b>目前設定為低雜訊</b>：資料邊界清晰，點的分散度低，<b>適合核函數完美切割</b>。"
    else:
        noise_detail = "<b>目前設定為中等雜訊</b>：包含適度的隨機波動與擾動。"

    st.markdown(
        f"""
        <div class="insight-card" style="border: 1px solid #8B5CF6;">
            <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
                <span style="font-size: 1.5rem; margin-right: 0.5rem; color: #8B5CF6;">░</span>
                <strong style="color: white; font-size: 1rem;">雜訊 ({noise:.2f})</strong>
            </div>
            <div style="color: #9CA3AF; font-size: 0.8rem; line-height: 1.4;">
                <div style="margin-bottom: 0.5rem;">雜訊代表資料分布的隨機擾動程度，過多雜訊會使分隔面變得複雜難學。</div>
                <div style="border-top: 1px solid #232735; padding-top: 0.5rem; color: #E5E7EB;">
                    {noise_detail}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="footer-container">
        <div>z = x² + y² 為教學簡化；真實 RBF 核映射至無限維空間</div>
        <div>基於 Streamlit、Plotly、scikit-learn 與 Manim 構建 ♡</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.animate:
    # Phase calculation for initial load
    frame_idx = st.session_state.frame_index
    if anim_mode in ["訓練過程", "Training Process"]:
        if frame_idx < 20:
            initial_text = "① 原始 2D 資料"
            initial_val = 1/3
        elif frame_idx < 35:
            initial_text = "② SVM 學習決策邊界..."
            initial_val = 2/3
        else:
            initial_text = "③ 支援向量決定邊界"
            initial_val = 3/3
    elif anim_mode == "決策邊界掃描":
        initial_text = "決策邊界掃描"
        initial_val = 1.0
    else:
        initial_text = "支援向量脈衝"
        initial_val = 1.0

    progress_placeholder.progress(initial_val, text=initial_text)

    pkg = build_all_frames(
        X,
        y,
        svc,
        resolution,
        colorscale,
        anim_mode,
    )
    transition_ms = int(300 - anim_speed * 25)
    html_code = build_animation_html(
        pkg,
        transition_ms,
        loop_play,
        colorscale,
        show_contour,
        st.session_state.animate,
        st.session_state.reset_clicked,
    )
    st.session_state.reset_clicked = False

    with plot_2d_placeholder.container():
        st.components.v1.html(html_code, height=480)
else:
    st.session_state.reset_clicked = False
    progress_placeholder.empty()
    with plot_2d_placeholder.container():
        st.markdown(
            '<div style="font-family: sans-serif; font-size: 0.85rem; color: #9CA3AF; margin-bottom: 0.5rem;">⏸ 靜態模式 — 拖動側邊欄即時更新</div>',
            unsafe_allow_html=True,
        )
        fig_2d = build_2d_figure(
            X, y, svc, resolution, colorscale, show_contour, show_sv_only
        )
        st.plotly_chart(fig_2d, use_container_width=True, key="fig_2d_paused")
