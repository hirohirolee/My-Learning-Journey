"""Executive Governance Studio.

Board-level regulatory decision tools rendered as Streamlit pages:

- cbam_calculator.py  : EU CBAM carbon border financial exposure engine
- ai_act_scanner.py   : EU AI Act risk-tier diagnostic & compliance gap checklist
- iso27001_radar.py   : ISO/IEC 27001:2022 Annex A maturity radar

Each module is a self-contained Streamlit page script. They are mounted by the
root ``Home.py`` (via ``st.Page``) or launched standalone through ``app.py``.
"""

__all__ = ["cbam_calculator", "ai_act_scanner", "iso27001_radar", "ai_security_scanner"]
__version__ = "1.0.0"
