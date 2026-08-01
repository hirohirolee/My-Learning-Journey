import streamlit as st
import streamlit.components.v1 as components
import os

# Set page title and layout
st.set_page_config(
    page_title="十大機器學習演算法：全方位動態學習報告",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to hide Streamlit default decorations and create a seamless full-page dark layout.
injection_html = """
    <style>
        /* Force body and container backgrounds to match the slate-950 color of app.html */
        html, body, [data-testid="stAppViewContainer"], .main, .block-container {
            background-color: #020617 !important;
            padding: 1rem !important;
            width: 100% !important;
        }

        /* 3. Reset standard Streamlit component container spacing */
        div[data-testid="stVerticalBlock"] {
            gap: 0 !important;
        }
        div[data-testid="stVerticalBlock"] > div {
            padding: 0 !important;
            margin: 0 !important;
        }
        div[data-testid="element-container"], div.stHtml {
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        /* 4. Style the embedded iframe to cover container responsive width */
        iframe[srcdoc] {
            width: 100% !important;
            height: 85vh !important;
            border: none !important;
            display: block !important;
            margin: 0 !important;
            padding: 0 !important;
            background-color: #020617 !important;
        }
    </style>

    <script>
        // Parent JS Hack: Find dynamic iframe elements in the parent page and inject camera/microphone permissions
        function injectCameraPermissions() {
            const iframes = document.querySelectorAll('iframe');
            iframes.forEach(iframe => {
                const currentAllow = iframe.getAttribute('allow') || '';
                if (!currentAllow.includes('camera')) {
                    iframe.setAttribute('allow', 'camera; microphone; autoplay; clipboard-write;');
                    
                    // Re-trigger loading for src iframes if not already done
                    if (iframe.src && iframe.src !== 'about:blank' && !iframe.dataset.reloaded) {
                        iframe.dataset.reloaded = "true";
                        iframe.src = iframe.src; 
                    }
                }
            });
        }

        // Set up intervals and observers to apply changes dynamically as elements render
        setInterval(injectCameraPermissions, 800);
        const observer = new MutationObserver((mutations) => {
            injectCameraPermissions();
        });
        observer.observe(document.body, { childList: true, subtree: true });
    </script>
"""
st.markdown(injection_html, unsafe_allow_html=True)

# Cached HTML reader to boost performance and reduce file system hits
@st.cache_data
def load_html_content():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    html_path = os.path.join(dir_path, "app.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

try:
    html_content = load_html_content()
    # Embed the HTML single-page app with dynamic viewport
    components.html(html_content, height=1000, scrolling=True)
except FileNotFoundError:
    st.error("找不到 app.html 檔案，請確認與 app.py 放在同個資料夾。")


