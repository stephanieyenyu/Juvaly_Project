# -*- coding: utf-8 -*-
"""LLM 自動標註管線（含限速處理、斷點續跑）。標前請先用 groq_validate.py 驗證準確率。"""
import os, json, time
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
from _codebook import CODEBOOK

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

INPUT_FILE = "../data/raw/competitor_BRAND_clean.csv"   # 改成目標檔
OUTPUT_FILE = "../data/labeled/BRAND_labeled.csv"

def label_one(content):
    prompt = f'{CODEBOOK}\n\n標註以下評論，只回傳 JSON：\n評論：「{content}」\n格式：{{"sentiment":"正面","pain_points":"","highlights":"輕盈好吸收"}}'
    resp = client.chat.completions.create(model=MODEL,
        messages=[{"role":"user","content":prompt}], temperature=0,
        response_format={"type":"json_object"})
    return json.loads(resp.choices[0].message.content)

def label_with_retry(content, max_retries=5):
    for attempt in range(max_retries):
        try: return label_one(content)
        except Exception as e:
            wait = 20*(attempt+1) if ("rate" in str(e).lower() or "429" in str(e)) else 5
            print(f"    等待 {wait}s 重試..."); time.sleep(wait)
    return {"sentiment":"錯誤","pain_points":"","highlights":""}

if __name__ == "__main__":
    df = pd.read_csv(INPUT_FILE)
    if os.path.exists(OUTPUT_FILE):
        done = pd.read_csv(OUTPUT_FILE)
        if "sentiment" in done.columns and len(done)==len(df):
            df = done
            todo = df.index[df["sentiment"].isin(["錯誤"])|df["sentiment"].isna()].tolist()
        else:
            todo = list(range(len(df)))
            for c in ["sentiment","pain_points","highlights"]: df[c]=None
    else:
        todo = list(range(len(df)))
        for c in ["sentiment","pain_points","highlights"]: df[c]=None
    print(f"需處理 {len(todo)} 筆")
    for n,i in enumerate(todo):
        r = label_with_retry(df.at[i,"content"])
        df.at[i,"sentiment"]=r.get("sentiment","錯誤")
        df.at[i,"pain_points"]=r.get("pain_points","")
        df.at[i,"highlights"]=r.get("highlights","")
        if (n+1)%10==0:
            print(f"  {n+1}/{len(todo)}"); df.to_csv(OUTPUT_FILE,index=False,encoding="utf-8-sig")
        time.sleep(2)
    df.to_csv(OUTPUT_FILE,index=False,encoding="utf-8-sig")
    print(df["sentiment"].value_counts().to_string())
