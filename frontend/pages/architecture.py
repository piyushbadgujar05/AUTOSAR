import streamlit as st
from frontend.utils.api_client import APIClient

def render_architecture():
    st.markdown("## 🧩 Architecture Knowledge Explorer")
    st.caption("Inspect extracted AUTOSAR Software Components (SWCs), ports, signals, and dependencies")

    search_term = st.text_input("🔍 Search Components", "").strip().lower()

    components = APIClient.get("/architecture/components")

    if isinstance(components, list) and components:
        filtered = [c for c in components if search_term in c["name"].lower() or search_term in (c.get("description") or "").lower()]
        
        st.markdown(f"**Found {len(filtered)} software component(s)**")
        
        for comp in filtered:
            with st.container():
                st.markdown(
                    f"""
                    <div style="background:#1E293B; border-radius:8px; padding:18px; margin-bottom:16px; border:1px solid #334155;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h3 style="margin:0; color:#38BDF8;">{comp['name']}</h3>
                            <span style="background:#0F172A; color:#94A3B8; padding:4px 10px; border-radius:12px; font-size:0.8rem;">
                                Pages: {', '.join(str(p) for p in comp['source_pages'])}
                            </span>
                        </div>
                        <p style="color:#CBD5E1; font-size:0.9rem; margin-top:8px;">
                            {comp['description'] or 'Component defined in architectural specification.'}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.markdown("**🔌 Interfaces:**")
                    if comp.get("interfaces"):
                        for iface in comp["interfaces"]:
                            st.markdown(f"- `{iface}`")
                    else:
                        st.caption("None documented")

                with c2:
                    st.markdown("**📥 Inputs:**")
                    if comp.get("inputs"):
                        for inp in comp["inputs"]:
                            st.markdown(f"- `{inp}`")
                    else:
                        st.caption("None documented")

                with c3:
                    st.markdown("**📤 Outputs / Transmits:**")
                    if comp.get("dependencies"):
                        for dep in comp["dependencies"]:
                            st.markdown(f"- `{dep}`")
                    else:
                        st.caption("None documented")

                with c4:
                    st.markdown("**🔗 Dependencies:**")
                    if comp.get("dependencies"):
                        for dep in comp["dependencies"]:
                            st.markdown(f"- `{dep}`")
                    else:
                        st.caption("None documented")

                st.divider()
    else:
        st.info("No architectural components extracted yet. Ingest an HLD document to populate the catalog.")
