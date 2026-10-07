import streamlit as st
import pandas as pd
from frontend.utils.api_client import APIClient

def render_interfaces():
    st.markdown("## 🔌 Communication Interface Explorer")
    st.caption("Inspect and validate sender-receiver, client-server, and automotive bus interfaces")

    interfaces = APIClient.get("/architecture/interfaces")

    if isinstance(interfaces, list) and interfaces:
        # Filters
        c1, c2 = st.columns([2, 1])
        with c1:
            search_query = st.text_input("Filter by Interface Name or Signal", "").strip().lower()
        with c2:
            protocols = list(set(item["type"] for item in interfaces))
            selected_proto = st.selectbox("Protocol Filter", ["All Protocols"] + protocols)

        filtered = []
        for item in interfaces:
            if selected_proto != "All Protocols" and item["type"] != selected_proto:
                continue
            if search_query:
                sig_match = any(search_query in s.lower() for s in item.get("signals", []))
                if search_query not in item["name"].lower() and not sig_match:
                    continue
            filtered.append(item)

        st.markdown(f"**Displaying {len(filtered)} interface(s)**")

        # Table formatting
        df_rows = []
        for f in filtered:
            df_rows.append({
                "Interface": f["name"],
                "Provider": f["provider"],
                "Consumer": f["consumer"],
                "Protocol": f["type"],
                "Signals / Payload": ", ".join(f.get("signals", [])),
                "Source Page": f"Page {f['source_page']}",
                "Status": f["status"]
            })

        df = pd.DataFrame(df_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### 📋 Interface Specification Details")
        for f in filtered:
            with st.expander(f"Interface: {f['name']} ({f['type']})"):
                st.write(f"**Provider SWC:** `{f['provider']}`")
                st.write(f"**Consumer SWC:** `{f['consumer']}`")
                st.write(f"**Signals:** {', '.join(f.get('signals', []))}")
                st.write(f"**Verification Status:** {f['status']}")
                st.write(f"**Source Document Citation:** Page {f['source_page']}")
    else:
        st.info("No communication interfaces extracted yet.")
