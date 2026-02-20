import os
import tempfile

import pandas as pd
import streamlit as st
from pyvis.network import Network

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "relationships.csv")

RELATION_COLORS = {
    "友人": "#4A90D9",
    "同僚": "#7ED321",
    "家族": "#E85D5D",
}


def build_network(df: pd.DataFrame) -> Network:
    net = Network(height="600px", width="100%", bgcolor="#1a1a2e", font_color="white")
    net.barnes_hut()

    nodes = pd.unique(df[["source", "target"]].values.ravel())
    for node in nodes:
        net.add_node(node, label=node, title=node)

    for _, row in df.iterrows():
        color = RELATION_COLORS.get(row["relation"], "#aaaaaa")
        net.add_edge(
            row["source"],
            row["target"],
            title=row["relation"],
            value=int(row["weight"]),
            color=color,
        )

    return net


def main() -> None:
    st.set_page_config(page_title="人物ネットワークグラフ", layout="wide")
    st.title("人物ネットワークグラフ")

    df = pd.read_csv(DATA_PATH)

    with st.sidebar:
        st.header("フィルター")
        all_relations = sorted(df["relation"].unique().tolist())
        selected = st.multiselect("関係性", all_relations, default=all_relations)

    filtered = df[df["relation"].isin(selected)]

    if filtered.empty:
        st.warning("表示するデータがありません。フィルターを確認してください。")
        return

    st.subheader("関係データ")
    st.dataframe(filtered, use_container_width=True)

    net = build_network(filtered)

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

    legend = "　".join(
        f'<span style="color:{color}">●</span> {rel}'
        for rel, color in RELATION_COLORS.items()
    )
    st.markdown(
        f"**凡例:** {legend}　　エッジの太さは関係の強さを示します",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
