import streamlit as st
from frontend.utils.api_client import APIClient

def render_comparison():
    st.markdown("## ⚖️ Document Revision Comparison")
    st.caption("Perform automated semantic and structural diffs between two High-Level Design versions")

    docs = APIClient.get("/documents")
    if not isinstance(docs, list) or len(docs) < 2:
        st.warning("Please ensure at least two document revisions are indexed to perform revision comparison.")
        return

    doc_map = {f"{d['name']} (v{d['version']})": d['id'] for d in docs}
    labels = list(doc_map.keys())

    col1, col2 = st.columns(2)
    with col1:
        base_label = st.selectbox("Baseline Revision (e.g. v1.0)", labels, index=0)
    with col2:
        target_label = st.selectbox("Target Revision (e.g. v2.0)", labels, index=min(1, len(labels)-1))

    if st.button("🚀 Compare Document Revisions", type="primary"):
        doc1_id = doc_map[base_label]
        doc2_id = doc_map[target_label]

        if doc1_id == doc2_id:
            st.error("Please select two distinct document revisions to compare.")
            return

        with st.spinner("Analyzing architectural delta between revisions..."):
            diff_res = APIClient.post("/comparison", json_data={"doc1_id": doc1_id, "doc2_id": doc2_id})

            if "error" in diff_res:
                st.error(f"Comparison error: {diff_res['error']}")
                return

            st.session_state.last_comparison = diff_res

    # Render results if available
    diff = st.session_state.get("last_comparison")
    if diff:
        st.markdown("---")
        st.subheader("📊 Revision Comparison Summary")
        st.info(diff.get("summary", ""))

        # 3-column breakdown for Added, Removed, Changed
        c_add, c_rem, c_chg = st.columns(3)

        comps = diff.get("components_diff", {})
        ifaces = diff.get("interfaces_diff", {})
        deps = diff.get("dependencies_diff", {})

        with c_add:
            st.markdown("### 🟢 Added in Target")
            st.markdown("**Components:**")
            if comps.get("added"):
                for a in comps["added"]:
                    st.success(f"+ `{a}`")
            else:
                st.caption("None added")

            st.markdown("**Interfaces:**")
            if ifaces.get("added"):
                for a in ifaces["added"]:
                    st.success(f"+ `{a}`")
            else:
                st.caption("None added")

        with c_rem:
            st.markdown("### 🔴 Removed / Deprecated")
            st.markdown("**Components:**")
            if comps.get("removed"):
                for r in comps["removed"]:
                    st.error(f"- `{r}`")
            else:
                st.caption("None removed")

            st.markdown("**Interfaces:**")
            if ifaces.get("removed"):
                for r in ifaces["removed"]:
                    st.error(f"- `{r}`")
            else:
                st.caption("None removed")

        with c_chg:
            st.markdown("### 🟡 Modified / Changed")
            st.markdown("**Components:**")
            if comps.get("changed"):
                for chg in comps["changed"]:
                    st.warning(f"Δ `{chg['name']}` (v1 Page {chg.get('v1_page')} ➔ v2 Page {chg.get('v2_page')})")
            else:
                st.caption("None modified")

            st.markdown("**Dependencies:**")
            if deps.get("changed"):
                for chg in deps["changed"]:
                    st.warning(f"Δ `{chg['dependency']}` ({chg['v1_protocol']} ➔ {chg['v2_protocol']})")
            else:
                st.caption("None modified")

        st.markdown("---")

        # Potential Architectural Impacts
        st.subheader("🔍 Potential Architectural Impacts")
        impacts = diff.get("potential_impacts", [])
        if impacts:
            for imp in impacts:
                st.markdown(
                    f"""
                    <div style="background:#1E293B; border-left:4px solid #F59E0B; border-radius:6px; padding:14px; margin-bottom:12px; border-top:1px solid #334155; border-right:1px solid #334155; border-bottom:1px solid #334155;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <b style="color:#F8FAFC; font-size:1rem;">{imp['category']}: {imp['item']}</b>
                            <span style="background:rgba(245, 158, 11, 0.2); color:#FBBF24; padding:2px 8px; border-radius:4px; font-size:0.75rem; border:1px solid #F59E0B;">
                                {imp['review_label']}
                            </span>
                        </div>
                        <p style="color:#CBD5E1; font-size:0.88rem; margin-top:6px;">
                            {imp['finding']}
                        </p>
                        <div style="background:#0F172A; padding:8px; border-radius:4px; color:#38BDF8; font-size:0.85rem;">
                            <b>Potential Architecture Impact:</b> {imp['potential_impact']}
                        </div>
                        <div style="color:#94A3B8; font-size:0.8rem; margin-top:6px;">
                            Citations: {imp.get('sources', 'Document Pages')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No critical architectural impacts detected.")
