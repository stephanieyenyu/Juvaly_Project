# -*- coding: utf-8 -*-
"""Juvaly 競品輿情儀表板 v2 — 跨品牌雷達疊加 + 亮點對照"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from collections import Counter
import glob, os

st.set_page_config(page_title="Juvaly 競品輿情儀表板", layout="wide")

# ── 品牌顏色 ─────────────────────────────────────────────────────────
BRAND_COLORS = {
    "Juvaly":               "#E8743B",
    "DR.WU":                "#4C8BE8",
    "Inna Organic 童顏有機":  "#2ECC71",
    "綠藤生機":              "#9B59B6",
    "menomeno":             "#E74C3C",
    "簡單JANDAN":            "#F39C12",
    "nomel":                "#1ABC9C",
}

def brand_color(name):
    return BRAND_COLORS.get(name, "#888888")

# ── 資料載入 ──────────────────────────────────────────────────────────
@st.cache_data
def load_data(folder="data/labeled"):
    frames = []
    for f in glob.glob(os.path.join(folder, "*_labeled.csv")):
        d = pd.read_csv(f)
        if "sentiment" in d.columns:
            frames.append(d)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df = df[~df["sentiment"].isin(["錯誤", "非評論"])].copy()
    df["pain_points"] = df["pain_points"].fillna("")
    df["highlights"]  = df["highlights"].fillna("")
    return df

df = load_data()
if df.empty:
    st.error("找不到標註資料。請確認 data/labeled/ 內有 *_labeled.csv")
    st.stop()

brands = sorted(df["brand"].unique())

# ── 雷達圖計算 ────────────────────────────────────────────────────────
RADAR_DIMS = {
    "質地黏膩": ["黏", "膩", "稠"],
    "香味問題": ["香味不佳"],
    "效果無感": ["無感", "沒感", "效果不"],
    "吸收差":   ["吸收差"],
    "價格偏高": ["價格偏高", "貴"],
    "包裝問題": ["包裝設計", "永續包裝"],
}

def radar_scores(sub):
    n = max(len(sub), 1)
    scores = {}
    for dim, kws in RADAR_DIMS.items():
        hits = sub["pain_points"].apply(
            lambda x: any(k in str(x) for k in kws)).sum()
        scores[dim] = round(hits / n * 100, 1)
    return scores

def parse_tags(series):
    """把 pain_points / highlights 欄位拆成 list，兼容逗號與分號"""
    tags = []
    for v in series:
        if isinstance(v, str) and v.strip():
            for t in v.replace(";", ",").split(","):
                t = t.strip()
                if t:
                    tags.append(t)
    return tags

# ══════════════════════════════════════════════════════════════════════
# 側邊欄
# ══════════════════════════════════════════════════════════════════════
st.sidebar.title("Juvaly 競品輿情儀表板")
st.sidebar.caption("資料來源：@cosme 公開評論｜質化探索，非統計普查")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "選擇分析頁面",
    ["📊 單品牌深探", "🔍 跨品牌痛點對照", "✨ 跨品牌亮點對照", "📋 原文瀏覽"],
)

# ══════════════════════════════════════════════════════════════════════
# 頁面 1：單品牌深探
# ══════════════════════════════════════════════════════════════════════
if page == "📊 單品牌深探":
    sel = st.sidebar.selectbox("選擇品牌", brands,
                               index=brands.index("Juvaly") if "Juvaly" in brands else 0)
    sub = df[df["brand"] == sel]
    n   = len(sub)

    st.title(f"{sel}｜品牌深探")

    # 頂部 KPI
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("有效評論數", n)
    pos_rate = (sub["sentiment"] == "正面").mean() * 100
    c2.metric("正面率", f"{pos_rate:.0f}%")
    neg_rate = (sub["sentiment"] == "負面").mean() * 100
    c3.metric("負面率", f"{neg_rate:.0f}%")
    pain_cnt = sum(1 for v in sub["pain_points"] if isinstance(v, str) and v.strip())
    c4.metric("有痛點評論數", pain_cnt)

    st.markdown("---")
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("痛點雷達圖")
        scores = radar_scores(sub)
        dims = list(scores.keys())
        vals = list(scores.values())
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=dims + [dims[0]],
            fill="toself", name=sel,
            line_color=brand_color(sel),
            fillcolor=brand_color(sel).replace("#", "rgba(").rstrip(")") + ",0.15)" if False else brand_color(sel),
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, max(vals + [10])])),
            showlegend=False, height=380,
            margin=dict(l=40, r=40, t=20, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("數值 = 該痛點被提及筆數佔比(%)，越高代表問題越突出")

    with col2:
        st.subheader("情感分布")
        sc = sub["sentiment"].value_counts().reset_index()
        sc.columns = ["情感", "筆數"]
        fig2 = go.Figure(go.Bar(
            x=sc["情感"], y=sc["筆數"],
            marker_color=[
                "#2ECC71" if s == "正面" else "#E74C3C" if s == "負面" else "#95A5A6"
                for s in sc["情感"]
            ],
            text=sc["筆數"], textposition="outside",
        ))
        fig2.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10),
                           yaxis=dict(range=[0, sc["筆數"].max() * 1.3]))
        st.plotly_chart(fig2, use_container_width=True)

        # Top 亮點
        st.subheader("Top 亮點")
        hl_cnt = Counter(parse_tags(sub["highlights"])).most_common(6)
        if hl_cnt:
            hl_df = pd.DataFrame(hl_cnt, columns=["亮點", "次數"])
            st.dataframe(hl_df, hide_index=True, use_container_width=True)
        else:
            st.info("無亮點資料")

    # 下方：痛點文本
    st.markdown("---")
    st.subheader(f"代表性負面 / 中性評論（有痛點）")
    neg = sub[sub["sentiment"].isin(["負面", "中性"])]
    neg = neg[neg["pain_points"].str.len() > 0]
    if len(neg) == 0:
        st.success("此品牌無明顯負面 / 痛點評論。")
    else:
        for _, r in neg.head(6).iterrows():
            with st.expander(f"[{r['sentiment']}] 痛點：{r['pain_points']}"):
                st.write(r["content"])

# ══════════════════════════════════════════════════════════════════════
# 頁面 2：跨品牌痛點雷達疊加
# ══════════════════════════════════════════════════════════════════════
elif page == "🔍 跨品牌痛點對照":
    st.title("跨品牌痛點對照")
    sel_brands = st.sidebar.multiselect(
        "選擇要對照的品牌（可多選）",
        brands,
        default=brands,
    )
    if not sel_brands:
        st.warning("請至少選擇一個品牌")
        st.stop()

    # 雷達圖
    st.subheader("痛點雷達圖（疊加）")
    dims = list(RADAR_DIMS.keys())
    fig = go.Figure()
    for b in sel_brands:
        sub  = df[df["brand"] == b]
        vals = [radar_scores(sub)[d] for d in dims]
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=dims + [dims[0]],
            fill="toself", name=b,
            line_color=brand_color(b),
        ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 40])),
        showlegend=True, height=500,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("數值 = 該痛點被提及筆數佔比(%)，越高代表問題越突出")

    # 痛點長條比較
    st.markdown("---")
    st.subheader("各品牌痛點筆數比較（長條圖）")
    pain_data = {}
    for b in sel_brands:
        sub = df[df["brand"] == b]
        tags = Counter(parse_tags(sub["pain_points"]))
        pain_data[b] = tags

    all_pain_keys = sorted(
        set(k for t in pain_data.values() for k in t),
        key=lambda k: -sum(t.get(k, 0) for t in pain_data.values()),
    )[:10]

    fig3 = go.Figure()
    for b in sel_brands:
        fig3.add_trace(go.Bar(
            name=b,
            x=all_pain_keys,
            y=[pain_data[b].get(k, 0) for k in all_pain_keys],
            marker_color=brand_color(b),
        ))
    fig3.update_layout(
        barmode="group", height=380,
        xaxis_tickangle=-20,
        margin=dict(l=10, r=10, t=10, b=60),
    )
    st.plotly_chart(fig3, use_container_width=True)

    # 正面率比較
    st.markdown("---")
    st.subheader("各品牌正面率比較")
    pos_data = []
    for b in sel_brands:
        sub = df[df["brand"] == b]
        pos_data.append({
            "品牌": b,
            "正面率(%)": round((sub["sentiment"] == "正面").mean() * 100, 1),
            "有效評論數": len(sub),
        })
    pos_df = pd.DataFrame(pos_data).sort_values("正面率(%)", ascending=False)
    fig4 = go.Figure(go.Bar(
        x=pos_df["品牌"], y=pos_df["正面率(%)"],
        marker_color=[brand_color(b) for b in pos_df["品牌"]],
        text=pos_df["正面率(%)"].apply(lambda x: f"{x}%"),
        textposition="outside",
    ))
    fig4.update_layout(
        height=320, yaxis=dict(range=[0, 105]),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig4, use_container_width=True)
    st.dataframe(pos_df.reset_index(drop=True), hide_index=True, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# 頁面 3：跨品牌亮點對照
# ══════════════════════════════════════════════════════════════════════
elif page == "✨ 跨品牌亮點對照":
    st.title("跨品牌亮點對照")
    sel_brands = st.sidebar.multiselect(
        "選擇要對照的品牌（可多選）",
        brands,
        default=brands,
    )
    if not sel_brands:
        st.warning("請至少選擇一個品牌")
        st.stop()

    hl_data = {}
    for b in sel_brands:
        sub = df[df["brand"] == b]
        hl_data[b] = Counter(parse_tags(sub["highlights"]))

    all_hl_keys = sorted(
        set(k for t in hl_data.values() for k in t),
        key=lambda k: -sum(t.get(k, 0) for t in hl_data.values()),
    )[:10]

    st.subheader("亮點提及次數（長條圖）")
    fig5 = go.Figure()
    for b in sel_brands:
        n = max(len(df[df["brand"] == b]), 1)
        fig5.add_trace(go.Bar(
            name=b,
            x=all_hl_keys,
            y=[round(hl_data[b].get(k, 0) / n * 100, 1) for k in all_hl_keys],
            marker_color=brand_color(b),
        ))
    fig5.update_layout(
        barmode="group", height=400,
        yaxis_title="提及率(%)",
        xaxis_tickangle=-20,
        margin=dict(l=10, r=10, t=10, b=80),
    )
    st.plotly_chart(fig5, use_container_width=True)
    st.caption("數值 = 該亮點提及筆數 / 品牌有效評論數 × 100%")

    # Heatmap
    st.markdown("---")
    st.subheader("亮點熱力圖")
    heat_rows = []
    for b in sel_brands:
        n = max(len(df[df["brand"] == b]), 1)
        heat_rows.append([round(hl_data[b].get(k, 0) / n * 100, 1) for k in all_hl_keys])
    fig6 = go.Figure(go.Heatmap(
        z=heat_rows,
        x=all_hl_keys,
        y=sel_brands,
        colorscale="YlGn",
        text=[[f"{v}%" for v in row] for row in heat_rows],
        texttemplate="%{text}",
    ))
    fig6.update_layout(height=max(250, len(sel_brands) * 55),
                       margin=dict(l=120, r=20, t=20, b=80))
    st.plotly_chart(fig6, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# 頁面 4：原文瀏覽
# ══════════════════════════════════════════════════════════════════════
elif page == "📋 原文瀏覽":
    st.title("評論原文瀏覽")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        sel_brand = st.selectbox("品牌", ["全部"] + brands)
    with col_b:
        sel_sent  = st.selectbox("情感", ["全部", "正面", "中性", "負面"])
    with col_c:
        keyword   = st.text_input("關鍵字搜尋（痛點/亮點/內容）")

    sub = df.copy()
    if sel_brand != "全部":
        sub = sub[sub["brand"] == sel_brand]
    if sel_sent != "全部":
        sub = sub[sub["sentiment"] == sel_sent]
    if keyword:
        mask = (sub["content"].str.contains(keyword, na=False) |
                sub["pain_points"].str.contains(keyword, na=False) |
                sub["highlights"].str.contains(keyword, na=False))
        sub = sub[mask]

    st.caption(f"符合條件：{len(sub)} 筆")
    for _, r in sub.head(30).iterrows():
        label = f"[{r['brand']}] [{r['sentiment']}]"
        if r["pain_points"]: label += f" 痛：{r['pain_points']}"
        if r["highlights"]:  label += f" 亮：{r['highlights']}"
        with st.expander(label):
            st.write(r["content"])