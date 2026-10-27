"""Shared executive visual language for the Executive Governance Studio pages.

Named ``egs_theme`` (not ``utils``/``config``) on purpose: root ``Home.py`` purges
``utils`` / ``config`` from ``sys.modules`` between page runs, so a unique module
name avoids any collision with other portfolio apps.
"""

import streamlit as st

GOLD = "#C5A880"
GOLD_BRIGHT = "#D4AF37"
INK = "#12151A"
SLATE = "#94A3B8"
RED = "#E5484D"
AMBER = "#F5A524"
TEAL = "#2BB3A3"
BLUE = "#4FA8D1"

# Theme-neutral: no hardcoded template / font colour, so Streamlit's light or dark
# theme (applied by st.plotly_chart) keeps axis labels and text readable.
GRID = "rgba(128,128,128,0.30)"

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif"),
    margin=dict(l=20, r=20, t=50, b=20),
)

_CSS = f"""
<style>
.egs-hero {{
    border: 1px solid rgba(197,168,128,0.35);
    background: linear-gradient(135deg, rgba(197,168,128,0.10) 0%, rgba(18,21,26,0.0) 60%);
    border-radius: 14px; padding: 1.4rem 1.6rem; margin-bottom: 1.2rem;
}}
.egs-kicker {{ color:{GOLD}; letter-spacing:.18em; font-size:.75rem; text-transform:uppercase; font-weight:600; }}
.egs-title  {{ font-size:1.9rem; font-weight:800; margin:.25rem 0 .35rem 0; line-height:1.25; }}
.egs-sub    {{ color:{SLATE}; font-size:.98rem; }}
.egs-banner {{ border-radius:12px; padding:1rem 1.25rem; margin:.6rem 0 1rem 0; border-left:6px solid; }}
.egs-banner h4 {{ margin:0 0 .3rem 0; }}
.egs-banner p  {{ margin:0; color:inherit; opacity:.88; }}
.egs-section {{ color:{GOLD}; font-weight:700; letter-spacing:.06em; margin-top:1.2rem; }}
div[data-testid="stMetric"] {{
    background: rgba(128,128,128,0.06); border:1px solid rgba(128,128,128,0.22);
    border-radius:12px; padding:.8rem 1rem;
}}
</style>
"""


def inject_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def hero(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""<div class="egs-hero">
              <div class="egs-kicker">{kicker}</div>
              <div class="egs-title">{title}</div>
              <div class="egs-sub">{subtitle}</div>
            </div>""",
        unsafe_allow_html=True,
    )


def banner(title: str, body: str, color: str) -> None:
    st.markdown(
        f"""<div class="egs-banner" style="border-color:{color}; background:{color}1A;">
              <h4 style="color:{color};">{title}</h4><p>{body}</p>
            </div>""",
        unsafe_allow_html=True,
    )


def section(text: str) -> None:
    st.markdown(f'<div class="egs-section">{text}</div>', unsafe_allow_html=True)


def disclaimer(text: str) -> None:
    st.caption(f"⚖️ {text}")
