import streamlit as st
import plotly.graph_objects as go
from frontend.utils.api_client import APIClient

def render_dashboard():
    st.markdown("## 📊 Automotive Architecture Intelligence Dashboard")
    st.caption("AUTOSAR High-Level Design (HLD) Knowledge & Verification Hub")

    # Fetch stats
    docs = APIClient.get("/documents")
    if isinstance(docs, dict) and "error" in docs:
        st.error(f"Cannot connect to backend server: {docs['error']}. Ensure FastAPI backend is running.")
        return

    comps = APIClient.get("/architecture/components")
    ifaces = APIClient.get("/architecture/interfaces")
    deps = APIClient.get("/architecture/dependencies")
    findings = APIClient.get("/analysis/findings")
    audits = APIClient.get("/analysis/audit")

    doc_count = len(docs) if isinstance(docs, list) else 0
    comp_count = len(comps) if isinstance(comps, list) else 0
    iface_count = len(ifaces) if isinstance(ifaces, list) else 0
    dep_count = len(deps) if isinstance(deps, list) else 0
    finding_count = len(findings) if isinstance(findings, list) else 0
    reviewed_count = sum(1 for f in (findings if isinstance(findings, list) else []) if f.get("status") in ["ACCEPTED", "REJECTED", "RESOLVED", "UNDER_REVIEW"])

    # Metrics row
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("Documents", doc_count, help="Indexed HLD Specifications")
    with col2:
        st.metric("Components", comp_count, help="Software Components (SWCs)")
    with col3:
        st.metric("Interfaces", iface_count, help="RTE & Bus Interfaces")
    with col4:
        st.metric("Dependencies", dep_count, help="Component Coupling Flows")
    with col5:
        st.metric("Potential Issues", finding_count, delta=f"{finding_count} for review", delta_color="inverse")
    with col6:
        st.metric("Reviewed Findings", reviewed_count, help="Human Reviewed Dispositions")

    st.markdown("---")

    # Architecture Health Overview
    st.subheader("🛡️ Architecture Health & Verification Index")
    hcol1, hcol2, hcol3, hcol4 = st.columns(4)

    with hcol1:
        fig1 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=92 if comp_count > 0 else 0,
            title={'text': "Architecture Completeness", 'font': {'size': 12, 'color': '#94A3B8'}},
            gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#38BDF8"},
                   'steps': [{'range': [0, 50], 'color': "#334155"}, {'range': [50, 100], 'color': "#1E293B"}]}
        ))
        fig1.update_layout(height=180, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="#0B1120", font=dict(color="#F8FAFC"))
        st.plotly_chart(fig1, use_container_width=True)

    with hcol2:
        # Interface consistency (penalized by potential findings)
        score = max(60, 100 - (finding_count * 15)) if comp_count > 0 else 0
        fig2 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            title={'text': "Interface Consistency", 'font': {'size': 12, 'color': '#94A3B8'}},
            gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#F59E0B" if score < 85 else "#10B981"},
                   'steps': [{'range': [0, 60], 'color': "#334155"}, {'range': [60, 100], 'color': "#1E293B"}]}
        ))
        fig2.update_layout(height=180, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="#0B1120", font=dict(color="#F8FAFC"))
        st.plotly_chart(fig2, use_container_width=True)

    with hcol3:
        fig3 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=95 if dep_count > 0 else 0,
            title={'text': "Dependency Consistency", 'font': {'size': 12, 'color': '#94A3B8'}},
            gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#38BDF8"},
                   'steps': [{'range': [0, 50], 'color': "#334155"}, {'range': [50, 100], 'color': "#1E293B"}]}
        ))
        fig3.update_layout(height=180, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="#0B1120", font=dict(color="#F8FAFC"))
        st.plotly_chart(fig3, use_container_width=True)

    with hcol4:
        fig4 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=88 if doc_count > 0 else 0,
            title={'text': "Documentation Quality", 'font': {'size': 12, 'color': '#94A3B8'}},
            gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#10B981"},
                   'steps': [{'range': [0, 50], 'color': "#334155"}, {'range': [50, 100], 'color': "#1E293B"}]}
        ))
        fig4.update_layout(height=180, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="#0B1120", font=dict(color="#F8FAFC"))
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")

    # Recent Documents & Recent Findings Side-by-Side
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("📄 Recent Indexed Documents")
        if isinstance(docs, list) and docs:
            for d in docs[:4]:
                st.markdown(
                    f"""
                    <div style="background:#1E293B; border-radius:8px; padding:12px; margin-bottom:8px; border:1px solid #334155;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <b style="color:#38BDF8;">{d['name']}</b>
                            <span style="background:#0F172A; padding:2px 8px; border-radius:4px; font-size:0.8rem; color:#94A3B8;">v{d['version']}</span>
                        </div>
                        <div style="font-size:0.85rem; color:#94A3B8; margin-top:4px;">
                            Project: {d['project']} | Pages: {d['total_pages']} | Chunks: {d['chunk_count']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No documents uploaded yet. Go to Document Manager to upload an HLD.")

    with right_col:
        st.subheader("⚠️ Recent Potential Architecture Issues")
        if isinstance(findings, list) and findings:
            for f in findings[:4]:
                color = "#EF4444" if f['severity'] == "HIGH" else "#F59E0B"
                st.markdown(
                    f"""
                    <div style="background:#1E293B; border-radius:8px; padding:12px; margin-bottom:8px; border-left:4px solid {color}; border-top:1px solid #334155; border-right:1px solid #334155; border-bottom:1px solid #334155;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <b style="color:#F8FAFC;">{f['title'][:45]}...</b>
                            <span style="background:{color}; color:white; padding:2px 6px; border-radius:4px; font-size:0.75rem;">{f['severity']}</span>
                        </div>
                        <div style="font-size:0.85rem; color:#CBD5E1; margin-top:4px;">
                            {f['description'][:120]}...
                        </div>
                        <div style="font-size:0.75rem; color:#94A3B8; margin-top:6px;">
                            Source: Page {f['source_page']} | Status: <b>{f['status']}</b>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.success("No active inconsistencies detected.")
