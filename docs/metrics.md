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
| `outputs/competitor_summary_final.csv` | Aggregated counts from an earlier snapshot — see known-issues.md C-1 |
| `outputs/final_competitor_analysis.png` | Figure from the same earlier snapshot |
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

Valid = Total − 非評論. Positive rate = 正面 ÷ Valid.


**What this figure does not claim.** Positive rate describes reviews published on @cosme Taiwan
for that brand page. It is not a customer satisfaction rate, a market share signal, or a
comparison of product quality.

**Juvaly's row is not comparable to the others.** Nine valid reviews means each row moves the
rate by 11.1 points. The 100% figure is one row away from 88.9%.

---

## Labelling Reliability

| Figure | Value | Derivation |
|---|---|---|
| Rows marked 錯誤 | 0 | `value_counts()` across all six brand files |
| Sentiment agreement with human labels | 64–67% (two runs) | `outputs/validation_result*.json`; replacement model, see known-issues.md B-1 |
| Pain-point agreement | not measured | Never validated, see known-issues.md B-2 |
| Highlight agreement | not measured | Never validated, see known-issues.md B-2 |
| Repeat-run stability | 91% (30/33 identical) | Two runs, see known-issues.md B-3 |

**Zero 錯誤 rows does not mean zero failures.** `label_with_retry()` returns
`{"sentiment": "錯誤"}` only after five consecutive failures. A row that failed four times and
succeeded on the fifth is indistinguishable from one that succeeded immediately.

**64–67% was measured on a different model than the one that produced this data.**
`llama-3.3-70b-versatile` was decommissioned by Groq on 2026-08-16, mid-project. The figure above
is `openai/gpt-oss-120b`'s raw, uncorrected agreement with human labels — see known-issues.md C-6.
It cannot be compared to the original labelling run, which is no longer queryable.

---

## Reconciliation Against the Committed Summary


`outputs/competitor_summary_final.csv` was produced from a different snapshot. Not yet fixed —
see known-issues.md C-1 through C-4.

| Brand | Summary valid | Data valid | Agrees |
|---|---|---|---|
| Inna Organic | 90 | 90 | yes |
| nomel | 22 | 22 | yes |
| DR.WU | 118 | 123 | no |
| menomeno + 簡單 | 44 | 49 | no |
| Juvaly | 33 | 9 | no |
| 綠藤 | absent | 96 | not analysed |

The Juvaly row is the largest discrepancy. `analyze.py` reads that brand from
`data/labeled/labeled_reviews.csv`, a file not present here, while the committed Juvaly data is
`juvaly_cosme_labeled.csv` with 13 rows. The two are different datasets.

---

## Interpretation

### The committed figure and the committed data are not the same study

Two of six brands reconcile. Treating the PNG or the summary CSV as evidence for the numbers in
this repository would be wrong in both directions: the summary omits 綠藤 entirely, and its
Juvaly column is computed over a dataset that is not here.

### "62% positive overall" is an average of incomparable rates

The six brands contribute 9 to 123 valid reviews each. The pooled rate is dominated by DR.WU,
Inna Organic and 綠藤, which together supply 309 of the 389 valid rows.


### A 4.9% negative rate is now partially, not fully, explained

The validation set is committed and has been run, but it contains only one 負面 case out of 33 —
too few to say whether the codebook's negative definition is too narrow or the model
under-applies it. That single case was missed (labelled 中性, not 正面). A properly stratified
validation set, sampled to include more negative cases, is needed to say more — see
known-issues.md's Open Problems.
