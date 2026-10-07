import streamlit as st
import pandas as pd
from frontend.utils.api_client import APIClient

def render_audit():
    st.markdown("## 📜 Engineering Audit & Traceability Log")
    st.caption("Immutable chronological record of document ingestions, AI queries, and human review decisions")

    audits = APIClient.get("/analysis/audit?limit=100")

    if isinstance(audits, list) and audits:
        st.markdown(f"**Total Records: {len(audits)}**")

        records = []
        for a in audits:
            records.append({
                "Timestamp": a["timestamp"][:19].replace("T", " "),
                "User / Role": a["user"],
                "Action": a["action"],
                "Technical Details": a.get("details", "")
            })

        df = pd.DataFrame(records)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No audit entries recorded yet.")
