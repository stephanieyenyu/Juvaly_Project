# -*- coding: utf-8 -*-
"""清理品牌頁資料：移除開頭作者資訊（暱稱・膚質・年齡・心得數）"""
import pandas as pd
import re

INPUT = "../data/raw/competitor_BRAND_multipage.csv"   # 改成目標檔
OUTPUT = "../data/raw/competitor_BRAND_clean.csv"

def strip_author_info(text):
    text = str(text)
    m = re.search(r'篇心得\d*', text)
    return text[m.end():].strip() if m else text.strip()

if __name__ == "__main__":
    df = pd.read_csv(INPUT)
    print(f"原始 {len(df)} 則")
    df["content"] = df["content"].apply(strip_author_info)
    df = df[df["content"].astype(str).str.len() >= 50]
    df = df.drop_duplicates(subset="content").reset_index(drop=True)
    df["post_id"] = range(1, len(df)+1)
    df = df[["post_id","brand","title","content","created_at"]]
    print(f"清理後 {len(df)} 則")
    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
