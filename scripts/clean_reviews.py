# -*- coding: utf-8 -*-
"""通用評論清洗函式：去官方文案、去過短、去重複"""
import pandas as pd

def is_official_text(content):
    content = str(content)
    ad_signals = ["商品說明", "升級上市", "了解更多化", "成為你保養中有意義的選修"]
    if content.startswith("商品說明"):
        return True
    return sum(1 for w in ad_signals if w in content) >= 2

def clean_review_df(df, min_length=100):
    before = len(df)
    df = df[~df["content"].apply(is_official_text)]
    df = df[df["content"].astype(str).str.len() >= min_length]
    df = df.drop_duplicates(subset="content").reset_index(drop=True)
    print(f"清洗：{before} 筆 → {len(df)} 筆（移除 {before - len(df)} 筆雜質）")
    return df
