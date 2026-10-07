import streamlit as st
from frontend.utils.api_client import APIClient

def render_consistency():
    st.markdown("## ⚠️ Architecture Consistency & Inconsistency Detector")
    st.caption("Deterministic rule-based validation engine identifying potential architecture anomalies")

    # Safety Notice Banner
    st.markdown(
        """
        <div class="disclaimer-banner">
            <b>REVIEW MANDATE:</b> Items listed below represent <i>Potential Inconsistencies</i> identified by deterministic rules.
            They are NOT confirmed defects until an authorized engineering reviewer evaluates the finding.
        </div>
        """,
        unsafe_allow_html=True
    )

    # Document Selector & Trigger Check
    docs = APIClient.get("/documents")
    doc_options = {}
    if isinstance(docs, list):
        for d in docs:
            doc_options[f"{d['name']} (v{d['version']})"] = d['id']

    c1, c2 = st.columns([3, 1])
    with c1:
        sel_label = st.selectbox("Select Target Specification", list(doc_options.keys()) if doc_options else ["None"])
        sel_id = doc_options.get(sel_label)
    with c2:
        if st.button("🔄 Run Rule Engine"):
            if sel_id:
                res = APIClient.post(f"/analysis/inconsistencies?document_id={sel_id}")
                st.success("Rule checks executed.")
                st.rerun()

    # Filter Options
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        sev_filter = st.selectbox("Filter by Severity", ["All Severities", "HIGH", "MEDIUM", "LOW"])
    with f_col2:
        status_filter = st.selectbox("Filter by Review Status", ["All Statuses", "NEW", "UNDER_REVIEW", "ACCEPTED", "REJECTED", "RESOLVED"])

    # Fetch Findings
    params = {}
    if sel_id:
        params["document_id"] = sel_id
    if sev_filter != "All Severities":
        params["severity"] = sev_filter
    if status_filter != "All Statuses":
        params["status"] = status_filter

    findings = APIClient.get("/analysis/findings", params=params)

    if isinstance(findings, list) and findings:
        st.markdown(f"**Identified {len(findings)} Potential Finding(s)**")

        for f in findings:
            sev_color = "#EF4444" if f["severity"] == "HIGH" else "#F59E0B"
            with st.container():
                st.markdown(
                    f"""
                    <div class="finding-card" style="border-left: 5px solid {sev_color};">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div class="finding-title">{f['title']}</div>
                            <div>
                                <span style="background:{sev_color}; color:white; padding:3px 8px; border-radius:4px; font-size:0.75rem; font-weight:600;">
                                    {f['severity']} SEVERITY
                                </span>
                                <span style="background:#334155; color:#F8FAFC; padding:3px 8px; border-radius:4px; font-size:0.75rem; margin-left:6px;">
                                    STATUS: {f['status']}
                                </span>
                            </div>
                        </div>
                        <p style="color:#CBD5E1; font-size:0.9rem; margin-top:8px;">
                            {f['description']}
                        </p>
                        <div style="font-size:0.8rem; color:#94A3B8; margin-top:6px;">
                            <b>Rule Type:</b> {f['finding_type']} &nbsp;|&nbsp; 
                            <b>Evidence Location:</b> Page {f['source_page']} &nbsp;|&nbsp; 
                            <b>AI Confidence:</b> {int(f['confidence']*100)}%
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Human Review Panel
                with st.expander(f"📝 Human Review & Disposition (Finding #{f['id']})", expanded=(f['status'] == 'NEW')):
                    current_role = st.session_state.get("user_role", "Reviewer")
                    st.caption(f"Reviewing as role: **{current_role}**")

                    r_col1, r_col2 = st.columns([1, 2])
                    with r_col1:
                        status_choices = ["NEW", "UNDER_REVIEW", "ACCEPTED", "REJECTED", "RESOLVED"]
                        current_status = f['status'] if f['status'] in status_choices else "UNDER_REVIEW"
                        new_status = st.selectbox(
                            "Disposition Decision",
                            status_choices,
                            index=status_choices.index(current_status),
                            key=f"status_sel_{f['id']}"
                        )
                    with r_col2:
                        comment = st.text_input("Reviewer Comment / Rationale", key=f"comment_{f['id']}", placeholder="e.g. Interface definition managed in secondary chassis specification.")

                    if st.button("Submit Engineering Review", key=f"btn_review_{f['id']}", type="primary"):
                        payload = {
                            "reviewer": f"{current_role} User",
                            "status": new_status,
                            "comment": comment
                        }
                        rev_res = APIClient.post(f"/findings/{f['id']}/review", json_data=payload)
                        if "error" in rev_res:
                            st.error(f"Error submitting review: {rev_res['error']}")
                        else:
                            st.success(f"Finding #{f['id']} updated to '{new_status}'")
                            st.rerun()

                    # Show previous reviews if any
                    reviews = f.get("reviews", [])
                    if reviews:
                        st.markdown("**Review History:**")
                        for r in reviews:
                            st.caption(f"• **{r['reviewer']}** marked as `{r['status']}` on {r['timestamp'][:16].replace('T', ' ')}: *{r.get('comment') or 'No comment'}*")

                st.divider()
    else:
        st.success("No potential inconsistencies found matching the selected filters.")
