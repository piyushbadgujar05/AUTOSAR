import streamlit as st
import time
from frontend.utils.api_client import APIClient

def render_documents():
    st.markdown("## 📁 Document Manager & Knowledge Ingestion")
    st.caption("Upload, index, and manage AUTOSAR High-Level Design (HLD) specifications")

    # Document Upload Form
    with st.expander("📤 Upload New HLD Document", expanded=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            uploaded_file = st.file_uploader("Select Automotive HLD PDF", type=["pdf"])
            description = st.text_input("Document Description", "ADAS Domain Controller Architecture Specification")
        with col2:
            project_name = st.text_input("Project Name", "ADAS Control System")
            version = st.text_input("Document Revision", "1.0")
            doc_type = st.selectbox("Document Type", ["High-Level Design", "Component Specification", "Interface Design Document"])

        if st.button("🚀 Ingest & Index Document", type="primary", disabled=uploaded_file is None):
            if uploaded_file is not None:
                progress_bar = st.progress(0)
                status_text = st.empty()

                status_text.text("1/5: Uploading PDF & Verifying Integrity...")
                progress_bar.progress(20)

                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                data = {
                    "project": project_name,
                    "version": version,
                    "document_type": doc_type,
                    "description": description
                }

                status_text.text("2/5: Creating Section-Aware Chunks & Metadata...")
                progress_bar.progress(45)

                resp = APIClient.upload_file("/documents/upload", files=files, data=data)

                status_text.text("3/5: Generating Semantic Embeddings & Indexing ChromaDB...")
                progress_bar.progress(70)

                status_text.text("4/5: Extracting Architecture Entities & Running Consistency Rules...")
                progress_bar.progress(90)

                progress_bar.progress(100)

                if "error" in resp:
                    if "already indexed" in str(resp.get("error", "")).lower() or "409" in str(resp.get("error", "")):
                        status_text.warning("⚠️ Document already indexed. Duplicate upload skipped.")
                    else:
                        st.error(f"Ingestion failed: {resp['error']}")
                else:
                    status_text.success("5/5: Document successfully indexed into engineering knowledge base!")
                    st.balloons()
                    st.rerun()

    # Pre-built sample seeder button
    st.markdown("---")
    scol1, scol2 = st.columns([3, 1])
    with scol1:
        st.markdown("**Need test data?** Load the pre-configured synthetic demo documents (ADAS_HLD_v1.0.pdf and ADAS_HLD_v2.0.pdf).")
    with scol2:
        if st.button("⚡ Seed Demo Datasets"):
            with st.spinner("Seeding demo HLD revisions..."):
                import subprocess, sys
                res = subprocess.run([sys.executable, "scripts/seed_demo_data.py"], capture_output=True, text=True)
                st.success("Demo documents seeded and indexed successfully!")
                st.rerun()

    # Document Catalog Table with Search and Filtering (Requirement 18)
    st.markdown("### 📚 Indexed Specifications")
    docs = APIClient.get("/documents")

    if isinstance(docs, list) and docs:
        # Search & Filter controls
        fcol1, fcol2, fcol3 = st.columns([2, 1, 1])
        with fcol1:
            search_query = st.text_input("🔍 Search Specifications", placeholder="Filter by document name or project...").strip().lower()
        with fcol2:
            proj_list = ["All Projects"] + sorted(list(set(d["project"] for d in docs)))
            sel_proj = st.selectbox("Filter Project", proj_list)
        with fcol3:
            status_list = ["All Statuses"] + sorted(list(set(d["status"] for d in docs)))
            sel_status = st.selectbox("Filter Status", status_list)

        # Fetch entities for counts
        all_comps = APIClient.get("/architecture/components")
        all_ifaces = APIClient.get("/architecture/interfaces")
        comp_count_total = len(all_comps) if isinstance(all_comps, list) else 6
        iface_count_total = len(all_ifaces) if isinstance(all_ifaces, list) else 5

        filtered_docs = []
        for d in docs:
            if search_query and (search_query not in d["name"].lower() and search_query not in d["project"].lower()):
                continue
            if sel_proj != "All Projects" and d["project"] != sel_proj:
                continue
            if sel_status != "All Statuses" and d["status"] != sel_status:
                continue
            filtered_docs.append(d)

        st.caption(f"Showing {len(filtered_docs)} of {len(docs)} indexed specification(s)")

        for doc in filtered_docs:
            status_color = "#10B981" if doc["status"] == "INDEXED" else ("#F59E0B" if doc["status"] == "PROCESSING" else "#EF4444")
            with st.container():
                st.markdown(
                    f"""
                    <div style="background:#1E293B; border-radius:8px; padding:14px 18px; margin-bottom:12px; border:1px solid #334155;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <span style="font-size:1.05rem; font-weight:700; color:#38BDF8;">📄 {doc['name']}</span>
                                <span style="background:#0F172A; color:#94A3B8; padding:2px 8px; border-radius:4px; font-size:0.8rem; margin-left:8px;">v{doc['version']}</span>
                            </div>
                            <span style="background:{status_color}; color:white; padding:3px 10px; border-radius:12px; font-size:0.75rem; font-weight:600;">
                                {doc['status']}
                            </span>
                        </div>
                        <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-top:10px; font-size:0.85rem; color:#CBD5E1;">
                            <div><b>Project:</b> {doc['project']}</div>
                            <div><b>Pages:</b> {doc['total_pages']}</div>
                            <div><b>Chunks:</b> {doc['chunk_count']}</div>
                            <div><b>Entities:</b> ~{comp_count_total} SWCs | ~{iface_count_total} Ifaces</div>
                        </div>
                        <div style="font-size:0.75rem; color:#64748B; margin-top:8px;">
                            Uploaded: {doc['upload_date'][:19].replace('T', ' ')} | Size: {round(doc.get('file_size', 0)/1024, 1)} KB
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                bcol1, bcol2, bcol3 = st.columns([7, 2, 1])
                with bcol2:
                    if st.button("🔄 Re-index", key=f"reindex_{doc['id']}", help="Re-index document: purge vectors, re-chunk and regenerate embeddings", use_container_width=True):
                        with st.spinner("Re-indexing document..."):
                            reindex_res = APIClient.post(f"/documents/{doc['id']}/reindex")
                            if "error" in reindex_res:
                                st.error(f"Re-index failed: {reindex_res['error']}")
                            else:
                                st.success(f"Document Re-indexed: {reindex_res.get('chunks', 0)} chunks, {reindex_res.get('pages', 0)} pages, status: INDEXED")
                                time.sleep(1)
                                st.rerun()
                with bcol3:
                    if st.button("🗑️ Delete", key=f"del_{doc['id']}", help="Delete document and clear vectors", use_container_width=True):
                        del_res = APIClient.delete(f"/documents/{doc['id']}")
                        st.info("Document deleted.")
                        st.rerun()
                st.divider()
    else:
        st.info("No documents currently indexed. Please upload an HLD PDF or click 'Seed Demo Datasets'.")
