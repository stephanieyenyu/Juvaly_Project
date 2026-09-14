# -*- coding: utf-8 -*-
"""驗證關卡：用人工標註當考題，測 LLM 情感標註準確率。達 80% 才放心大規模標註。"""
import os, time, json
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
from _codebook import CODEBOOK
from groq_label_batch import label_one

load_dotenv()

if __name__ == "__main__":
    df = pd.read_csv("../data/labeled/validation_set.csv")
    correct, mismatches = 0, []
    for n, (_, row) in enumerate(df.iterrows()):
        try: llm = label_one(row["content"]).get("sentiment","")
        except Exception as e:
            print(f"  [{n+1}/{len(df)}] 請求失敗: {e}")
            llm = "錯誤"
        if llm == row["sentiment"]: correct += 1
        else: mismatches.append({
            "orig_post_id": int(row["orig_post_id"]),
            "human": row["sentiment"], "llm": llm,
            "excerpt": str(row["content"])[:35]
        })
        print(f"  [{n+1}/{len(df)}] 人工:{row['sentiment']} | LLM:{llm}")
        time.sleep(2)

    accuracy = correct / len(df)
    result = {
        "run_at": pd.Timestamp.now().isoformat(),
        "n": len(df), "correct": correct,
        "sentiment_accuracy": round(accuracy, 4),
        "mismatches": mismatches,
    }
    os.makedirs("../outputs", exist_ok=True)
    with open("../outputs/validation_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n情感準確率：{accuracy:.0%}（{correct}/{len(df)}）")
    print("不一致案例：")
    for m in mismatches:
        print(f"  人工:{m['human']} | LLM:{m['llm']} | {m['excerpt']}")
    print(f"\n結果已寫入 ../outputs/validation_result.json")
