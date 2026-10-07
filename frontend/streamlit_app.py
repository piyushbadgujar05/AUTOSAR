import os
import streamlit as st
from frontend.utils.api_client import APIClient
from frontend.pages.dashboard import render_dashboard
from frontend.pages.documents import render_documents
from frontend.pages.assistant import render_assistant
from frontend.pages.architecture import render_architecture
from frontend.pages.interfaces import render_interfaces
from frontend.pages.graph import render_graph
from frontend.pages.consistency import render_consistency
from frontend.pages.comparison import render_comparison
from frontend.pages.reports import render_reports
from frontend.pages.audit import render_audit
from frontend.pages.settings_page import render_settings

# Page Configuration
st.set_page_config(
    page_title="AUTOSAR HLD Document Analysis Assistant",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS
css_path = os.path.join(os.path.dirname(__file__), "styles", "main.css")
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Session State Initialization
if "user_role" not in st.session_state:
    st.session_state.user_role = "Reviewer"

# Sidebar Navigation
with st.sidebar:
    st.markdown(
        """
        <div style="padding:10px 0 16px 0;">
            <h2 style="margin:0; color:#38BDF8; font-size:1.3rem;">🚗 AUTOSAR HLD</h2>
            <p style="margin:0; font-size:0.8rem; color:#94A3B8;">Architecture Intelligence Assistant</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Role badge
    role = st.session_state.user_role
    role_color = "#38BDF8" if role == "Engineer" else ("#F59E0B" if role == "Reviewer" else "#EF4444")
    st.markdown(
        f"""
        <div style="background:#1E293B; border-radius:6px; padding:8px 12px; margin-bottom:14px; border:1px solid #334155;">
            <div style="font-size:0.75rem; color:#94A3B8; text-transform:uppercase;">Active Role</div>
            <div style="font-weight:600; color:{role_color}; font-size:0.95rem;">{role}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    page_selection = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "📁 Documents",
            "🤖 AI Assistant",
            "🧩 Architecture",
            "🔌 Interfaces",
            "🕸️ Dependencies",
            "⚠️ Consistency",
            "⚖️ Compare Revisions",
            "📑 Reports",
            "📜 Audit Log",
            "⚙️ Settings"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    
    # Check Backend status
    health = APIClient.get("/health")
    if isinstance(health, dict) and "error" not in health:
        st.markdown("<span style='color:#10B981; font-size:0.8rem;'>● Backend: Online (Port 8000)</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:#EF4444; font-size:0.8rem;'>● Backend: Offline</span>", unsafe_allow_html=True)
    
    st.caption("v1.0.0 | ISO 26262 Assistant Tool")

# Main Page Routing
if page_selection == "📊 Dashboard":
    render_dashboard()
elif page_selection == "📁 Documents":
    render_documents()
elif page_selection == "🤖 AI Assistant":
    render_assistant()
elif page_selection == "🧩 Architecture":
    render_architecture()
elif page_selection == "🔌 Interfaces":
    render_interfaces()
elif page_selection == "🕸️ Dependencies":
    render_graph()
elif page_selection == "⚠️ Consistency":
    render_consistency()
elif page_selection == "⚖️ Compare Revisions":
    render_comparison()
elif page_selection == "📑 Reports":
    render_reports()
elif page_selection == "📜 Audit Log":
    render_audit()
elif page_selection == "⚙️ Settings":
    render_settings()
