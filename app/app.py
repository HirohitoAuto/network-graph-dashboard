import os
import tempfile

import pandas as pd
import streamlit as st
from pyvis.network import Network

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "relationships.csv")


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
            html = f.read()
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    st.subheader("ネットワークグラフ")
    st.components.v1.html(html, height=620, scrolling=False)


if __name__ == "__main__":
    main()
