import streamlit as st
import plotly.graph_objects as go
import networkx as nx
from frontend.utils.api_client import APIClient

def render_graph():
    st.markdown("## 🕸️ Architectural Dependency & Flow Graph")
    st.caption("Visual representation of component couplings, data flows, and bus topologies")

    graph_data = APIClient.get("/architecture/graph")

    if not isinstance(graph_data, dict) or not graph_data.get("nodes"):
        st.info("No graph data available. Please ingest an HLD document first.")
        return

    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    # Build NetworkX graph for layout
    G = nx.DiGraph()
    for n in nodes:
        G.add_node(n["id"], label=n["label"], type=n.get("type", "COMPONENT"))
    for e in edges:
        G.add_edge(e["source"], e["target"], label=e.get("label", ""), protocol=e.get("protocol", "CAN"))

    # Compute layout
    pos = nx.spring_layout(G, k=1.2, seed=42)

    # Edge traces
    edge_x = []
    edge_y = []
    edge_text = []

    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_text.append(f"{edge[0]} ➔ {edge[1]} ({edge[2].get('protocol', 'CAN')})")

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=2, color='#475569'),
        hoverinfo='none',
        mode='lines'
    )

    # Node traces
    node_x = []
    node_y = []
    node_text = []
    node_color = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        deg = G.degree(node)
        node_text.append(f"<b>{node}</b><br>Connections: {deg}")
        # Color coding
        if "Controller" in node:
            node_color.append("#38BDF8")  # Cyan for controllers
        elif "Manager" in node or "Processor" in node:
            node_color.append("#F59E0B")  # Amber for perception
        else:
            node_color.append("#10B981")  # Green for others

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=[n for n in G.nodes()],
        textposition="top center",
        hovertext=node_text,
        marker=dict(
            showscale=False,
            color=node_color,
            size=30,
            line_width=2,
            line_color='#F8FAFC'
        )
    )

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=10, r=10, t=20),
                        paper_bgcolor="#0B1120",
                        plot_bgcolor="#0B1120",
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        height=520
                    ))

    st.plotly_chart(fig, use_container_width=True)

    # Node Details Inspector
    st.markdown("### 🔍 Node Inspector")
    selected_node = st.selectbox("Select Component to Inspect", list(G.nodes()))

    if selected_node:
        node_meta = {}
        for n in nodes:
            if n["id"] == selected_node:
                node_meta = n.get("metadata", {})
                break

        in_edges = list(G.in_edges(selected_node, data=True))
        out_edges = list(G.out_edges(selected_node, data=True))

        desc = node_meta.get("description", f"Software component: {selected_node}")
        ev_pages = node_meta.get("evidence_pages", [node_meta.get("page", 1)])
        interfaces_list = node_meta.get("interfaces", [])
        deps_list = node_meta.get("dependencies", [v for u, v, d in out_edges])
        related_list = node_meta.get("related_components", list(set([u for u, v, d in in_edges] + [v for u, v, d in out_edges])))

        st.markdown(
            f"""
            <div style="background:#1E293B; border-radius:8px; padding:14px; border:1px solid #334155; margin-bottom:12px;">
                <h4 style="margin:0; color:#38BDF8;">{selected_node}</h4>
                <p style="color:#CBD5E1; font-size:0.9rem; margin-top:6px;">{desc}</p>
                <div style="font-size:0.8rem; color:#94A3B8;">
                    <b>Evidence Document Pages:</b> {', '.join(str(p) for p in ev_pages)}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"**🔌 Interfaces ({len(interfaces_list)}):**")
            if interfaces_list:
                for iface in interfaces_list:
                    st.write(f"- `{iface}`")
            else:
                st.caption("No direct bus/RTE interfaces mapped.")

        with c2:
            st.markdown(f"**🔗 Dependencies ({len(deps_list)}):**")
            if deps_list:
                for d in deps_list:
                    st.write(f"- `{d}`")
            else:
                st.caption("No outgoing dependencies.")

        with c3:
            st.markdown(f"**🧩 Related Components ({len(related_list)}):**")
            if related_list:
                for rc in related_list:
                    st.write(f"- `{rc}`")
            else:
                st.caption("No coupled components.")
