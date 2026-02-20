import os

import pandas as pd
import streamlit as st
from pyvis.network import Network

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
GROUP_COLORS = {
    "family": "#e74c3c",
    "friend": "#2ecc71",
    "colleague": "#3498db",
}

st.set_page_config(page_title="人物ネットワーク図", layout="wide")
st.title("人物ネットワーク図")

nodes_df = pd.read_csv(os.path.join(DATA_DIR, "nodes.csv"), dtype={"id": int})
edges_df = pd.read_csv(os.path.join(DATA_DIR, "edges.csv"), dtype={"source": int, "target": int})

net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")
net.barnes_hut()

for _, row in nodes_df.iterrows():
    color = GROUP_COLORS.get(row["group"], "#95a5a6")
    net.add_node(row["id"], label=row["name"], color=color, title=f"{row['name']} ({row['group']})")

for _, row in edges_df.iterrows():
    net.add_edge(row["source"], row["target"], label=row["label"])

html = net.generate_html()

st.components.v1.html(html, height=620, scrolling=False)

st.subheader("凡例")
cols = st.columns(len(GROUP_COLORS))
for col, (group, color) in zip(cols, GROUP_COLORS.items()):
    col.markdown(f"<span style='color:{color}'>■</span> {group}", unsafe_allow_html=True)
