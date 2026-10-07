import streamlit as st
from frontend.utils.api_client import APIClient

def render_assistant():
    st.markdown("## 🤖 AI Engineering Assistant (RAG)")
    st.caption("Ask natural-language questions grounded strictly in uploaded HLD specifications")

    # Safety Notice Banner
    st.markdown(
        """
        <div class="disclaimer-banner">
            ⚠️ <b>ENGINEERING ASSISTANT NOTICE:</b> Answers are synthesized strictly from retrieved document evidence.
            This tool does not formally approve architecture decisions. Human engineering verification is required.
        </div>
        """,
        unsafe_allow_html=True
    )

    # Document / Project / Version selector
    docs = APIClient.get("/documents")
    doc_options = {"All Documents": None}
    projects = set(["All Projects"])
    versions = set(["All Versions"])

    if isinstance(docs, list):
        for d in docs:
            doc_options[f"{d['name']} (v{d['version']})"] = d['id']
            if d.get("project"):
                projects.add(d["project"])
            if d.get("version"):
                versions.add(d["version"])

    col_sel1, col_sel2, col_sel3 = st.columns([2, 1, 1])
    with col_sel1:
        selected_doc_label = st.selectbox("Active Specification Scope", list(doc_options.keys()))
        selected_doc_id = doc_options[selected_doc_label]
    with col_sel2:
        selected_proj = st.selectbox("Project Filter", sorted(list(projects)))
        proj_filter = None if selected_proj == "All Projects" else selected_proj
    with col_sel3:
        selected_ver = st.selectbox("Version Filter", sorted(list(versions)))
        ver_filter = None if selected_ver == "All Versions" else selected_ver

    col_t1, col_t2 = st.columns([1, 1])
    with col_t1:
        top_k = st.slider("Retrieval Top-K Chunks", min_value=2, max_value=8, value=5)
    with col_t2:
        sim_threshold = st.slider("Similarity Threshold", min_value=0.0, max_value=0.8, value=0.1, step=0.05)

    # Required clickable example questions
    st.markdown("**Suggested Engineering Questions (Click to Ask):**")
    q_col1, q_col2, q_col3 = st.columns(3)
    preset_query = None

    with q_col1:
        if st.button("🧩 1. Main Components", use_container_width=True):
            preset_query = "What are the main software components?"
        if st.button("🔌 2. ADASController Interfaces", use_container_width=True):
            preset_query = "What interfaces does ADASController use?"

    with q_col2:
        if st.button("🔗 3. Depend on SensorFusion", use_container_width=True):
            preset_query = "Which components depend on SensorFusion?"
        if st.button("⚠️ 4. Undefined Interfaces", use_container_width=True):
            preset_query = "Are there any undefined interfaces?"

    with q_col3:
        if st.button("⚖️ 5. What changed v1.0 vs v2.0", use_container_width=True):
            preset_query = "What changed between v1.0 and v2.0?"
        if st.button("🛑 6. References to BrakeController", use_container_width=True):
            preset_query = "Show me all references to BrakeController."

    # Initialize chat history with welcome message if empty
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "assistant",
                "content": "👋 **Welcome! I am your AUTOSAR Architecture Analysis Assistant.**\n\nI answer questions regarding software components, interfaces, bus topologies (CAN, Ethernet, Autosar RTE), and functional flows from your uploaded HLD documents.\n\n*Choose a suggested question above or enter an inquiry below.*",
                "confidence": "HIGH",
                "sources": [],
                "evidence": None,
                "dev_info": {}
            }
        ]

    # Render Chat History Container
    st.markdown("### 💬 Architecture Q&A History")
    for idx, msg in enumerate(st.session_state.chat_history):
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(f"**{msg['content']}**")
        else:
            with st.chat_message("assistant"):
                conf = msg.get("confidence", "MEDIUM")
                badge_class = f"badge-{conf.lower()}"
                
                # Header with Confidence
                st.markdown(
                    f"""
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="font-size:0.85rem; color:#94A3B8;">AI Architecture Synthesis</span>
                        <span class="{badge_class}">CONFIDENCE: {conf}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Answer Block
                st.markdown(msg["content"])

                # Grounded Sources Block (Requirement 9 & 10)
                sources = msg.get("sources", [])
                if sources:
                    st.markdown("---")
                    st.markdown("#### 📄 SOURCES")
                    for s_idx, s in enumerate(sources, 1):
                        st.markdown(f"**{s_idx}. {s['document']} — Page {s['page']}** (Section: *{s.get('section', 'General')}*)")

                # Explainable Evidence Block (Requirement 10)
                evidence = msg.get("evidence")
                if evidence:
                    st.markdown("#### 🔍 EVIDENCE")
                    st.markdown(
                        f"""
                        <div style="background:#0F172A; border-left:4px solid #38BDF8; padding:10px 14px; border-radius:4px; color:#E2E8F0; font-family:monospace; font-size:0.85rem; margin-top:4px;">
                            {evidence}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                # RAG Debug Panel / Retrieval Details (Requirement 18 & 23)
                dev_info = msg.get("dev_info", {})
                retrieval_details = dev_info.get("retrieval_details", [])
                if retrieval_details or dev_info:
                    with st.expander("🛠️ Show Retrieval Details (RAG Debug Panel)", expanded=False):
                        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
                        with mcol1:
                            st.metric("Retrieved Chunks", dev_info.get("retrieved_chunks", len(retrieval_details)))
                        with mcol2:
                            st.metric("Candidate Count", dev_info.get("candidate_count", len(retrieval_details)))
                        with mcol3:
                            st.metric("Query Latency", f"{dev_info.get('latency_ms', 0)} ms")
                        with mcol4:
                            st.metric("Model Engine", dev_info.get("model", "AutomotiveExpertEngine"))

                        # System & Filter Telemetry (Requirement 18)
                        st.markdown("##### 🔬 Retrieval Pipeline Configuration")
                        tcol1, tcol2 = st.columns(2)
                        with tcol1:
                            st.markdown(f"- **Collection:** `{dev_info.get('collection_name', 'project_adas_control_system')}`")
                            st.markdown(f"- **Embedding Model:** `{dev_info.get('embedding_model', 'BAAI/bge-small-en-v1.5')}`")
                            st.markdown(f"- **Project Filter:** `{dev_info.get('project_filter') or 'None'}`")
                        with tcol2:
                            st.markdown(f"- **Version Filter:** `{dev_info.get('version_filter') or 'None'}`")
                            st.markdown(f"- **Document Filter:** `{dev_info.get('document_filter') or 'All Documents'}`")
                            st.markdown(f"- **Top-K / Min Threshold:** `Top-{dev_info.get('top_k', 5)}` | `{dev_info.get('similarity_threshold_applied', 0.10)}`")

                        if retrieval_details:
                            st.markdown("##### 📑 Top Retrieved Results")
                            for r_idx, rd in enumerate(retrieval_details, 1):
                                st.markdown(
                                    f"**{r_idx}.** Score: `{rd.get('similarity_score', 0)}` | "
                                    f"Page: **{rd.get('page', '')}** | "
                                    f"Section: *{rd.get('section', 'General')}* | "
                                    f"Document: `{rd.get('document', '')}` (v{rd.get('version', '1.0')})"
                                )
                                preview = rd.get('snippet') or rd.get('text_preview') or ""
                                st.code(preview, language="text")

    # Chat Input
    user_query = st.chat_input("Enter your automotive architecture question...")
    query_to_send = preset_query or user_query

    if query_to_send:
        # Build limited conversation history for coreference resolution (Requirement 22)
        history_window = []
        for h in st.session_state.chat_history[-6:]:
            history_window.append({"role": h["role"], "content": h["content"]})

        st.session_state.chat_history.append({"role": "user", "content": query_to_send})

        with st.spinner("Searching section-aware chunks & synthesizing grounded answer..."):
            payload = {
                "query": query_to_send,
                "project": proj_filter or "ADAS Control System",
                "document_id": selected_doc_id,
                "version": ver_filter,
                "top_k": top_k,
                "similarity_threshold": sim_threshold,
                "conversation_history": history_window
            }
            resp = APIClient.post("/chat/query", json_data=payload)

            if "error" in resp:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"Error querying backend: {resp['error']}",
                    "confidence": "LOW",
                    "sources": [],
                    "evidence": None,
                    "dev_info": {}
                })
            else:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": resp.get("answer", ""),
                    "confidence": resp.get("confidence", "MEDIUM"),
                    "sources": resp.get("sources", []),
                    "evidence": resp.get("evidence"),
                    "dev_info": {
                        "latency_ms": resp.get("query_time_ms", 0),
                        "retrieved_chunks": resp.get("retrieved_chunks", 0),
                        "candidate_count": resp.get("candidate_count", 0),
                        "collection_name": resp.get("collection_name", "project_adas_control_system"),
                        "project_filter": resp.get("project_filter", proj_filter),
                        "version_filter": resp.get("version_filter", ver_filter),
                        "document_filter": resp.get("document_filter", selected_doc_id),
                        "embedding_model": resp.get("embedding_model", "BAAI/bge-small-en-v1.5"),
                        "top_k": top_k,
                        "similarity_threshold_applied": resp.get("similarity_threshold_applied", sim_threshold),
                        "model": resp.get("model_used", "AutomotiveExpertEngine"),
                        "retrieval_details": resp.get("retrieval_details", [])
                    }
                })
        st.rerun()
