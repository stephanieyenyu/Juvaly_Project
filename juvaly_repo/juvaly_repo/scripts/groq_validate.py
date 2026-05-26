# -*- coding: utf-8 -*-
"""驗證關卡：用人工標註當考題，測 LLM 情感標註準確率。達 80% 才放心大規模標註。"""
import os, time
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
from _codebook import CODEBOOK
from groq_label_batch import label_one

load_dotenv()

if __name__ == "__main__":
    df = pd.read_csv("../data/labeled/validation_set.csv")
    correct, mismatches = 0, []
    for _, row in df.iterrows():
        try: llm = label_one(row["content"]).get("sentiment","")
        except Exception: llm = "錯誤"
        if llm == row["sentiment"]: correct += 1
        else: mismatches.append((row["sentiment"], llm, str(row["content"])[:35]))
        time.sleep(0.3)
    print(f"情感準確率：{correct/len(df):.0%}（{correct}/{len(df)}）")
    print("不一致案例：")
    for h,l,c in mismatches: print(f"  人工:{h} | LLM:{l} | {c}")
