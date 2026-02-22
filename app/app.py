import os
import tempfile

import pandas as pd
import streamlit as st
from pyvis.network import Network

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "relationships.csv")


HIGHLIGHT_COLOR = "#ff6b35"

_CLICK_HANDLER_JS_TEMPLATE = """
                  // クリックアクション: ノード選択時のハイライトと絞り込み表示
                  var selectedNode = null;
                  network.on("click", function(params) {{
                      if (params.nodes.length > 0) {{
                          selectedNode = params.nodes[0];
                          var connectedNodeSet = new Set(network.getConnectedNodes(selectedNode));
                          var connectedEdgeSet = new Set(network.getConnectedEdges(selectedNode));

                          var updateNodes = [];
                          nodes.forEach(function(node) {{
                              if (node.id === selectedNode) {{
                                  updateNodes.push({{id: node.id, color: {{background: "{color}", border: "{color}", highlight: {{background: "{color}", border: "{color}"}}}}, hidden: false}});
                              }} else if (connectedNodeSet.has(node.id)) {{
                                  updateNodes.push({{id: node.id, color: nodeColors[node.id], hidden: false}});
                              }} else {{
                                  updateNodes.push({{id: node.id, hidden: true}});
                              }}
                          }});
                          nodes.update(updateNodes);

                          var updateEdges = [];
                          edges.forEach(function(edge) {{
                              updateEdges.push({{id: edge.id, hidden: !connectedEdgeSet.has(edge.id)}});
                          }});
                          edges.update(updateEdges);
                      }} else {{
                          selectedNode = null;
                          var resetNodes = [];
                          nodes.forEach(function(node) {{
                              resetNodes.push({{id: node.id, color: nodeColors[node.id], hidden: false}});
                          }});
                          nodes.update(resetNodes);

                          var resetEdges = [];
                          edges.forEach(function(edge) {{
                              resetEdges.push({{id: edge.id, hidden: false}});
                          }});
                          edges.update(resetEdges);
                      }}
                  }});
"""

_INJECT_MARKER = "return network;"


def inject_click_handler(html: str) -> str:
    if _INJECT_MARKER not in html:
        raise ValueError(f"Injection marker '{_INJECT_MARKER}' not found in generated HTML.")
    js = _CLICK_HANDLER_JS_TEMPLATE.format(color=HIGHLIGHT_COLOR)
    return html.replace(_INJECT_MARKER, js + _INJECT_MARKER, 1)


def build_network(df: pd.DataFrame) -> Network:
    net = Network(height="600px", width="100%", bgcolor="#1a1a2e", font_color="white")
    net.barnes_hut()

    nodes = pd.unique(df[["source", "target"]].values.ravel())

    # 各ノードの接続数を計算
    node_degrees = {}
    for node in nodes:
        node_degrees[node] = len(df[(df["source"] == node) | (df["target"] == node)])

    # ノードのサイズを接続数に応じて設定
    for node in nodes:
        size = 20 + node_degrees[node] * 5  # 基本サイズ + 接続数にスケール
        net.add_node(node, label=node, title=node, size=size)

    for _, row in df.iterrows():
        net.add_edge(row["source"], row["target"])

    return net


def main() -> None:
    st.set_page_config(page_title="人物ネットワークグラフ", layout="wide")
    st.title("人物ネットワークグラフ")

    df = pd.read_csv(DATA_PATH)

    if df.empty:
        st.warning("表示するデータがありません。")
        return

    st.subheader("関係データ")
    st.dataframe(df, use_container_width=True)

    net = build_network(df)

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            tmp_path = tmp.name
        net.save_graph(tmp_path)
        with open(tmp_path, "r", encoding="utf-8") as f:
            html = inject_click_handler(f.read())
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    st.subheader("ネットワークグラフ")
    st.components.v1.html(html, height=620, scrolling=False)


if __name__ == "__main__":
    main()
