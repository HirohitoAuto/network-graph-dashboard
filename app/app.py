import json
import os
import tempfile

import pandas as pd
import streamlit as st
from pyvis.network import Network

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "relationships.csv")
PROPERTY_PATH = os.path.join(os.path.dirname(__file__), "data", "property.csv")
HCO_PATH = os.path.join(os.path.dirname(__file__), "data", "hco.csv")


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
        raise ValueError(
            f"Injection marker '{_INJECT_MARKER}' not found in generated HTML."
        )
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

    # ノードラベル（人物名）を明示的に表示するためフォントサイズを設定
    opts = json.loads(net.options.to_json())
    opts.setdefault("nodes", {}).setdefault("font", {}).update(
        {"size": 16, "color": "white"}
    )
    net.set_options(json.dumps(opts))

    return net, pd.unique(df[["source", "target"]].values.ravel())


def get_network_nodes_info(nodes: list, hco_df: pd.DataFrame) -> pd.DataFrame:
    """ネットワークに表示されるノードの医療従事者と医療機関情報を取得"""
    # nodes内の医療従事者に対応するhco_nameを取得
    node_info = hco_df[hco_df["hcp_name"].isin(nodes)].copy()
    return node_info.sort_values("hcp_name")


def main() -> None:
    st.set_page_config(page_title="人物ネットワークグラフ", layout="wide")
    st.title("医療従事者の関係図ダッシュボード")

    df = pd.read_csv(DATA_PATH)
    prop_df = pd.read_csv(PROPERTY_PATH)
    hco_df = pd.read_csv(HCO_PATH)

    if df.empty:
        st.warning("表示するデータがありません。")
        return

    # サイドバーにタグフィルターを追加
    all_tags = sorted(prop_df["tag"].dropna().unique().tolist())
    selected_tags = st.sidebar.multiselect("専門分野", options=all_tags)

    # 選択されたタグに基づいてノードを絞り込む
    if selected_tags:
        filtered_names = prop_df[prop_df["tag"].isin(selected_tags)]["name"].unique()
        df = df[df["source"].isin(filtered_names) & df["target"].isin(filtered_names)]

    if df.empty:
        st.warning("選択したフィルターに一致するデータがありません。")
        return

    net, nodes = build_network(df)

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

    st.subheader("関係図")
    st.components.v1.html(html, height=620, scrolling=False)

    st.subheader("医療従事者情報")
    node_info = get_network_nodes_info(nodes, hco_df)
    if not node_info.empty:
        st.dataframe(node_info, use_container_width=True, hide_index=True)
    else:
        st.info("ネットワークに表示されるノードの情報がありません。")


if __name__ == "__main__":
    main()
