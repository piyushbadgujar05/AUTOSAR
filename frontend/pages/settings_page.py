import streamlit as st
from frontend.utils.api_client import APIClient

def render_settings():
    st.markdown("## ⚙️ System Settings & Environment Configuration")
    st.caption("Inspect runtime parameters, active LLM abstraction, and simulate user roles")

    # Role simulation
    st.subheader("👤 User Role Simulator")
    current_role = st.session_state.get("user_role", "Reviewer")
    new_role = st.selectbox(
        "Current Active Role",
        ["Engineer", "Reviewer", "Admin"],
        index=["Engineer", "Reviewer", "Admin"].index(current_role)
    )
    if new_role != current_role:
        st.session_state.user_role = new_role
        st.success(f"Switched role to: {new_role}")

    st.markdown(
        """
        - **ENGINEER:** Upload documents, ask architecture questions, explore components, review dependencies.
        - **REVIEWER:** All Engineer privileges + submit formal review dispositions on potential inconsistencies.
        - **ADMIN:** All privileges + delete specifications and manage project collections.
        """
    )

    st.markdown("---")

    # Backend Health Check
    st.subheader("🩺 Backend Telemetry")
    health = APIClient.get("/health")
    if isinstance(health, dict) and "error" not in health:
        st.success("FastAPI Backend Status: ONLINE & HEALTHY")
        st.json(health)
    else:
        st.error(f"Backend Status: UNREACHABLE ({health.get('error', '')})")
