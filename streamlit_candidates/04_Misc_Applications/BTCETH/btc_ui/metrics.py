import streamlit as st
from typing import Optional

def inject_custom_css() -> None:
    """Injects custom CSS to achieve modern dark theme glassmorphism aesthetics."""
    css = """
    <style>
    /* Main Layout */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Header customizations */
    h1, h2, h3, h4, h5, h6 {
        color: #f7931a !important; /* Bitcoin Orange */
        font-weight: 700;
    }
    
    /* Glassmorphism Card Wrapper */
    .glass-card {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(247, 147, 26, 0.15);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        margin-bottom: 20px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .glass-card:hover {
        border-color: rgba(247, 147, 26, 0.35);
        transform: translateY(-2px);
    }
    
    /* Card Elements */
    .card-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    
    .card-value {
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.2;
        margin-bottom: 6px;
    }
    
    .card-subtext {
        font-size: 0.8rem;
        color: #64748b;
    }
    
    .card-delta {
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        margin-top: 4px;
    }
    
    .delta-up {
        color: #10b981; /* Emerald green */
    }
    
    .delta-down {
        color: #ef4444; /* Rose red */
    }
    
    /* Recommendations & Badges */
    .badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-green {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-yellow {
        background-color: rgba(234, 179, 8, 0.15);
        color: #eab308;
        border: 1px solid rgba(234, 179, 8, 0.3);
    }
    .badge-orange {
        background-color: rgba(249, 115, 22, 0.15);
        color: #f97316;
        border: 1px solid rgba(249, 115, 22, 0.3);
    }
    .badge-red {
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    /* Custom Sidebar adjustments */
    section[data-testid="stSidebar"] {
        background-color: #080b11;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Tables styling overrides */
    div[data-testid="stTable"] table {
        background-color: rgba(17, 24, 39, 0.5) !important;
        color: #e2e8f0 !important;
        border-radius: 8px;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def render_kpi_card(
    title: str,
    value: str,
    subtext: str,
    delta: Optional[str] = None,
    delta_positive: bool = True
) -> None:
    """Renders a styled KPI glassmorphism card.
    
    Args:
        title (str): Title/Label of the card.
        value (str): Main metric value.
        subtext (str): Subtitle or context info.
        delta (str, optional): Delta change indicator text.
        delta_positive (bool): True if change is favorable (green), False if unfavorable (red).
    """
    delta_html = ""
    if delta:
        delta_class = "delta-up" if delta_positive else "delta-down"
        arrow = "▲" if delta_positive else "▼"
        delta_html = f'<div class="card-delta {delta_class}">{arrow} {delta}</div>'
        
    card_html = f"""
    <div class="glass-card">
        <div class="card-title">{title}</div>
        <div class="card-value">{value}</div>
        <div class="card-subtext">{subtext}</div>
        {delta_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def get_risk_badge(color: str, label: str) -> str:
    """Returns styled HTML for a colored badge.
    
    Args:
        color (str): 'green', 'yellow', 'orange', or 'red'.
        label (str): Badge text content.
        
    Returns:
        str: HTML string.
    """
    color_class = f"badge-{color.lower()}"
    return f'<span class="badge {color_class}">{label}</span>'

def render_risk_panel(
    risk_score: float,
    time_rating: str,
    time_color: str,
    financial_rating: str,
    financial_color: str,
    recommendation: str
) -> None:
    """Renders a comprehensive glassmorphism risk panel.
    
    Args:
        risk_score (float): Score from 1 to 100.
        time_rating (str): Expected waiting time scale description (e.g., 'Extreme').
        time_color (str): Color of time badge ('red', 'orange', etc.).
        financial_rating (str): Financial classification (e.g., 'High Risk').
        financial_color (str): Color of financial badge.
        recommendation (str): Text recommendation.
    """
    # Color coding the risk score itself
    if risk_score < 30:
        score_color = "#10b981"
    elif risk_score < 60:
        score_color = "#eab308"
    elif risk_score < 85:
        score_color = "#f97316"
    else:
        score_color = "#ef4444"
        
    time_badge = get_risk_badge(time_color, time_rating)
    fin_badge = get_risk_badge(financial_color, financial_rating)
    
    html = f"""
    <div class="glass-card" style="border-left: 5px solid {score_color};">
        <h4 style="margin-top: 0; color: #ffffff !important;">單機挖礦風險評估</h4>
        <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center; margin-top: 15px; margin-bottom: 20px;">
            <div style="text-align: center; border-right: 1px solid rgba(255,255,255,0.1); padding-right: 25px;">
                <div style="font-size: 0.8rem; color: #94a3b8; text-transform: uppercase;">綜合風險評分</div>
                <div style="font-size: 3rem; font-weight: 800; color: {score_color};">{risk_score:.0f}<span style="font-size: 1.5rem; color:#64748b;">/100</span></div>
            </div>
            <div>
                <table style="background: transparent; border: none; border-collapse: collapse; width: auto; color:#e2e8f0;">
                    <tr style="background: transparent; border: none;">
                        <td style="padding: 4px 10px 4px 0; border: none; font-size: 0.9rem; font-weight: 600; color:#94a3b8;">預估出塊時間評級:</td>
                        <td style="padding: 4px 0; border: none;">{time_badge}</td>
                    </tr>
                    <tr style="background: transparent; border: none;">
                        <td style="padding: 4px 10px 4px 0; border: none; font-size: 0.9rem; font-weight: 600; color:#94a3b8;">財務可行性:</td>
                        <td style="padding: 4px 0; border: none;">{fin_badge}</td>
                    </tr>
                </table>
            </div>
        </div>
        <div style="border-top: 1px solid rgba(255,255,255,0.08); padding-top: 15px;">
            <strong style="color: #ffffff; display: block; margin-bottom: 5px;">投資建議:</strong>
            <p style="color: #cbd5e1; font-size: 0.95rem; margin: 0; line-height: 1.5;">{recommendation}</p>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
