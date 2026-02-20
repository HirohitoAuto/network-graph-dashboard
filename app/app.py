import os

import pandas as pd
import streamlit as st
from pyvis.network import Network

st.set_page_config(page_title="人物ネットワークグラフ", layout="wide")
st.title("人物ネットワークグラフ")

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "relationships.csv")

df = pd.read_csv(DATA_PATH)

RELATION_COLORS = {
    "同僚": "#4A90D9",
    "上司": "#E94E4E",
    "友人": "#50B86C",
}

net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="#333333")
net.barnes_hut()

persons = set(df["source"].tolist() + df["target"].tolist())
for person in persons:
    net.add_node(person, label=person, title=person, size=20)

for _, row in df.iterrows():
    color = RELATION_COLORS.get(row["relation"], "#888888")
    net.add_edge(
        row["source"],
        row["target"],
        title=row["relation"],
        label=row["relation"],
        color=color,
    )

html_content = net.generate_html()

st.markdown("### 凡例")
cols = st.columns(len(RELATION_COLORS))
for col, (label, color) in zip(cols, RELATION_COLORS.items()):
    col.markdown(
        f'<span style="display:inline-block;width:16px;height:16px;background:{color};'
        f'border-radius:50%;margin-right:6px;vertical-align:middle;"></span>{label}',
        unsafe_allow_html=True,
    )

st.components.v1.html(html_content, height=620, scrolling=False)

with st.expander("データを表示"):
    st.dataframe(df, use_container_width=True)

