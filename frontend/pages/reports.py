import streamlit as st
import json
import os
from frontend.utils.api_client import APIClient, BACKEND_URL

def render_reports():
    st.markdown("## 📑 Engineering Report Generator")
    st.caption("Export structured architecture intelligence summaries in formal PDF or JSON formats")

    docs = APIClient.get("/documents")
    if not isinstance(docs, list) or not docs:
        st.warning("Please index an HLD document to generate an architecture report.")
        return

    doc_options = {f"{d['name']} (v{d['version']})": d['id'] for d in docs}

    col1, col2 = st.columns(2)
    with col1:
        selected_label = st.selectbox("Select Target Specification", list(doc_options.keys()))
        selected_doc_id = doc_options[selected_label]
    with col2:
        report_format = st.radio("Export Format", ["PDF", "JSON"], horizontal=True)

    if st.button("📄 Generate Architecture Report", type="primary"):
        with st.spinner(f"Generating formal {report_format} report..."):
            payload = {
                "document_id": selected_doc_id,
                "report_format": report_format.lower()
            }
            resp = APIClient.post("/reports/generate", json_data=payload)

            if "error" in resp:
                st.error(f"Report generation error: {resp['error']}")
            else:
                st.success(f"{report_format} Report generated successfully!")
                st.session_state.current_report = resp

    rep = st.session_state.get("current_report")
    if rep:
        st.markdown("---")
        st.subheader("📥 Report Download & Inspection")

        download_link = f"{BACKEND_URL.replace('/api', '')}{rep['file_path']}"
        
        st.markdown(
            f"""
            <div style="background:#1E293B; border-radius:8px; padding:16px; border:1px solid #334155; margin-bottom:16px;">
                <p><b>Report Identifier:</b> <code>{rep['report_id']}</code></p>
                <p><b>Format:</b> {rep['report_type']}</p>
                <p><b>Download URL:</b> <a href="{download_link}" target="_blank" style="color:#38BDF8;">{download_link}</a></p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Show JSON preview if applicable
        if rep.get("data"):
            with st.expander("👁️ View JSON Architecture Report Data", expanded=True):
                st.json(rep["data"])
