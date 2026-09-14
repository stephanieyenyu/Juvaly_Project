# Metrics

Every figure below is derived from the data committed in `data/labeled/`. The purpose is to let
a reader reproduce each number, not to accept it.

**Snapshot date**  2026-09-14
**Observation window**  Single labelling run, 2026
**Raw export**  [`data/labeled/`](../data/labeled/) — six brand CSVs (eight columns each) plus a
33-row validation set (six columns)

---

## Sources

| Source | Contains |
|---|---|
| `data/labeled/*_labeled.csv` | post_id, brand, title, content, created_at, sentiment, pain_points, highlights |
| `data/labeled/validation_set.csv` | 33 rows, human-labelled: brand, orig_post_id, sentiment, pain_points, highlights, content |
| `outputs/competitor_summary_final.csv` | Aggregated counts, regenerated from committed data — see known-issues.md C-1 |
| `outputs/pain_point_ranking.csv` | Cross-brand pain-point ranking, regenerated from committed data — see known-issues.md C-3 |
| `outputs/final_competitor_analysis.png` | Figure from an earlier snapshot — not regenerated, see known-issues.md C-1 |
| `outputs/validation_result.json`, `validation_result_run1.json` | Two runs of the validation gate — see known-issues.md B-1, B-3 |
| `data/raw/` | Absent. Pre-cleaning scrape output was not committed |

---

## Scale

```python
import pandas as pd, glob
sum(len(pd.read_csv(f)) for f in glob.glob('data/labeled/*_labeled.csv'))
```

| Figure | Value | Derivation |
|---|---|---|
| Labelled reviews | 500 | Sum of `len(read_csv)` over six brand files |
| Brands | 6 | File count in `data/labeled/` matching `*_labeled.csv` |
| Python files | 8 | 7 in `scripts/` plus `app.py` |
| Sentiment classes | 4 | Enumerated in `_codebook.py` |
| Pain-point categories | 15 | Enumerated in `_codebook.py`, including 其他 |
| Highlight categories | 10 | Enumerated in `_codebook.py`, including 其他 |

**Row counts use pandas, not line counts.** Review text contains embedded newlines, so `wc -l`
overstates every file. `DR_WU_147_labeled.csv` has 148 lines and 147 rows; `綠藤_110_labeled.csv`
has 111 lines and 110 rows.

---

## Sentiment Distribution

```python
pd.read_csv(f)['sentiment'].value_counts()
```

| Brand | Total | 正面 | 中性 | 負面 | 非評論 | Valid | Positive rate |
|---|---|---|---|---|---|---|---|
| DR.WU | 147 | 81 | 39 | 3 | 24 | 123 | 65.9% |
| Inna Organic | 141 | 62 | 23 | 5 | 51 | 90 | 68.9% |
| 綠藤 | 110 | 61 | 29 | 6 | 14 | 96 | 63.5% |
| menomeno + 簡單 | 58 | 18 | 27 | 4 | 9 | 49 | 36.7% |
| nomel | 31 | 10 | 11 | 1 | 9 | 22 | 45.5% |
| Juvaly | 13 | 9 | 0 | 0 | 4 | 9 | 100% |
| **All** | **500** | **241** | **129** | **19** | **111** | **389** | **62.0%** |

Valid = Total − 非評論. Positive rate = 正面 ÷ Valid. This table now matches
`outputs/competitor_summary_final.csv` exactly — see known-issues.md C-1.

**What this figure does not claim.** Positive rate describes reviews published on @cosme Taiwan
for that brand page. It is not a customer satisfaction rate, a market share signal, or a
comparison of product quality.

**Juvaly's row is not comparable to the others.** Nine valid reviews means each row moves the
rate by 11.1 points. The 100% figure is one row away from 88.9%.

---

## Pain-Point Ranking

```python
# scripts/analyze.py, main() — pain_points exploded on ';', mapped through normalize_pain()
```

| Rank | Pain point | Mentions | Brands affected |
|---|---|---|---|
| 1 | 質地黏膩 | 37 | DR.WU, Inna Organic, menomeno+簡單, nomel, 綠藤 |
| 2 | 效果無感 | 14 | DR.WU, menomeno+簡單, nomel, 綠藤 |
| 3 | 吸收慢 | 13 | DR.WU, Inna Organic, menomeno+簡單, nomel, 綠藤 |
| 4 | 價格偏高 | 12 | DR.WU, **Juvaly**, menomeno+簡單, nomel, 綠藤 |
| 5 | 包裝設計 | 11 | DR.WU, Inna Organic, menomeno+簡單, 綠藤 |
| 6 | 香味問題 | 9 | DR.WU, Inna Organic, menomeno+簡單, 綠藤 |

**Juvaly's only pain-point mention is 價格偏高 (1 of 9 valid reviews), and it never appears under
質地黏膩** — the market's single largest shared complaint. This is now reproducible from committed
code, not the hand-tallied figure in `docs/juvaly_report.pdf`, which reports different counts
(28 / 8 / 8 / 8 / 5 / 5) under a looser, undocumented matching rule. The two documents disagree;
this table is the one that can be rerun.

---

## Labelling Reliability

| Figure | Value | Derivation |
|---|---|---|
| Rows marked 錯誤 | 0 | `value_counts()` across all six brand files |
| Sentiment agreement with human labels | 69.7–72.7% (two runs) | `outputs/validation_result*.json`; replacement model, see known-issues.md B-1 |
| Pain-point agreement | not measured | Never validated, see known-issues.md B-2 |
| Highlight agreement | not measured | Never validated, see known-issues.md B-2 |
| Repeat-run stability | 91% (30/33 identical) | Two runs, see known-issues.md B-3 |

**Zero 錯誤 rows in the production data does not mean zero failures.** `label_with_retry()`
returns `{"sentiment": "錯誤"}` only after five consecutive failures. A row that failed four times
and succeeded on the fifth is indistinguishable from one that succeeded immediately. (One
transient `錯誤` did appear in a validation run — see B-3 — consistent with this being a live
risk, not a hypothetical one.)

**69.7–72.7% was measured on a different model than the one that produced this data.**
`llama-3.3-70b-versatile` was decommissioned by Groq on 2026-08-16, mid-project. The figure above
is `openai/gpt-oss-120b`'s raw, uncorrected agreement with human labels — see known-issues.md C-6.
It cannot be compared to the original labelling run, which is no longer queryable.

---

## Reconciliation Against the Committed Summary

`outputs/competitor_summary_final.csv` was regenerated on 2026-09-14 after fixing known-issues.md
C-1 through C-4. All six brands now reconcile.

| Brand | Summary valid | Data valid | Agrees |
|---|---|---|---|
| DR.WU | 123 | 123 | yes |
| Inna Organic | 90 | 90 | yes |
| 綠藤 | 96 | 96 | yes |
| menomeno + 簡單 | 49 | 49 | yes |
| nomel | 22 | 22 | yes |
| Juvaly | 9 | 9 | yes |

---

## Interpretation

### The committed figure and the committed data are now the same study

As of 2026-09-14 this is no longer a caveat: `competitor_summary_final.csv` and
`pain_point_ranking.csv` are both direct output of `analyze.py` run against the committed
`data/labeled/*.csv`. The one artefact that remains stale is `final_competitor_analysis.png`,
which `analyze.py` has no code path to regenerate.

### "62% positive overall" is an average of incomparable rates

The six brands contribute 9 to 123 valid reviews each. The pooled rate is dominated by DR.WU,
Inna Organic and 綠藤, which together supply 309 of the 389 valid rows.

### A 4.9% negative rate is now partially, not fully, explained

The validation set is committed and has been run twice. It contains only one 負面 case out of
33 — too few to say whether the codebook's negative definition is too narrow or the model
under-applies it. That single case was missed in both runs (labelled 中性, not 正面). A properly
stratified validation set, sampled to include more negative cases, is needed to say more — see
known-issues.md's Open Problems.

### Two authoritative documents now disagree on the pain-point ranking

`docs/juvaly_report.pdf` and `outputs/pain_point_ranking.csv` both claim to rank the market's
shared complaints, and give different numbers. Only the latter is reproducible from committed
code. This is not resolved by this pass — it is a new, explicit disagreement raised by fixing C-3.
