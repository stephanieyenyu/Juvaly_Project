# -*- coding: utf-8 -*-
"""痛點／亮點驗證關卡：把人工標註當考題，測這兩個多標籤欄位的準確率。

和 groq_validate.py 的差別有兩點。第一，這支不呼叫模型：批次標註的結果已經在
data/labeled/*_labeled.csv 裡，驗證集的人工答案也已經 commit,所以兩邊對起來就是
一次離線測量,不需要 API key,任何人 clone 下來都能重跑。第二,多標籤不能用字串相等
判對錯——一筆可以對一半——所以這裡同時報兩個數字:

  exact set match  整筆標籤集合完全相同的比例。直覺,但兩邊都空白也算對,
                   在一個模型很少輸出痛點的資料上會嚴重高估。
  tag-level P/R/F1 把每個標籤當一次判斷。這才是這兩欄實際的表現。

用法:cd scripts && python validate_tags.py
"""
import glob, json, datetime
import pandas as pd

LABELED_GLOB = "../data/labeled/*_labeled.csv"
VALIDATION    = "../data/labeled/validation_set.csv"
OUT           = "../outputs/validation_result_tags.json"
FIELDS        = ["pain_points", "highlights"]


def tags(cell):
    """把 `痛點A;痛點B` 或 `痛點A,痛點B` 拆成集合。空值回傳空集合。"""
    if not isinstance(cell, str) or not cell.strip():
        return set()
    return {t.strip() for t in cell.replace(";", ",").split(",") if t.strip()}


def main():
    human = pd.read_csv(VALIDATION)
    machine = pd.concat(
        [pd.read_csv(f) for f in glob.glob(LABELED_GLOB) if "validation_set" not in f],
        ignore_index=True,
    )
    m = human.merge(
        machine,
        left_on=["brand", "orig_post_id"], right_on=["brand", "post_id"],
        suffixes=("_h", "_m"),
    )
    if len(m) != len(human):
        print(f"警告:驗證集 {len(human)} 筆,只對上 {len(m)} 筆")

    result = {"run_at": datetime.datetime.now().isoformat(), "n": len(m)}

    for field in FIELDS:
        tp = fp = fn = exact = both_empty = 0
        disagreements = []
        for _, r in m.iterrows():
            H, M = tags(r[field + "_h"]), tags(r[field + "_m"])
            tp += len(H & M); fp += len(M - H); fn += len(H - M)
            if H == M:
                exact += 1
                both_empty += not H
            else:
                disagreements.append({
                    "post_id": int(r["orig_post_id"]), "brand": r["brand"],
                    "human": sorted(H), "llm": sorted(M),
                    "missed": sorted(H - M), "invented": sorted(M - H),
                })
        P = tp / (tp + fp) if tp + fp else 0.0
        R = tp / (tp + fn) if tp + fn else 0.0
        F = 2 * P * R / (P + R) if P + R else 0.0
        result[field] = {
            "exact_set_match": round(exact / len(m), 3),
            "exact_match_n": f"{exact}/{len(m)}",
            "of_which_both_empty": both_empty,
            "tag_precision": round(P, 3), "tag_recall": round(R, 3), "tag_f1": round(F, 3),
            "tp": tp, "fp": fp, "fn": fn,
            "disagreements": disagreements,
        }
        print(f"--- {field} ---")
        print(f"  exact set match {exact}/{len(m)} = {exact/len(m):.1%}"
              f"  (其中兩邊都空白 {both_empty} 筆)")
        print(f"  tag-level  P={P:.3f}  R={R:.3f}  F1={F:.3f}   tp={tp} fp={fp} fn={fn}")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n寫出 {OUT}")


if __name__ == "__main__":
    main()
