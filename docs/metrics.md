# Metrics

Every figure below is derived from the data committed in `data/labeled/`. The purpose is to let
a reader reproduce each number, not to accept it.

**Snapshot date**  2026-09-13
**Observation window**  Single labelling run, 2026
**Raw export**  [`data/labeled/`](../data/labeled/) — six CSVs, eight columns each

---

## Sources

| Source | Contains |
|---|---|
| `data/labeled/*.csv` | post_id, brand, title, content, created_at, sentiment, pain_points, highlights |
| `outputs/competitor_summary_final.csv` | Aggregated counts from an earlier snapshot |
| `outputs/final_competitor_analysis.png` | Figure from the same earlier snapshot |
| `data/raw/` | Absent. Pre-cleaning scrape output was not committed |
| `data/labeled/validation_set.csv` | Absent. Human-labelled gate set was not committed |

---

## Scale

```python
import pandas as pd, glob
sum(len(pd.read_csv(f)) for f in glob.glob('data/labeled/*.csv'))
```

| Figure | Value | Derivation |
|---|---|---|
| Labelled reviews | 500 | Sum of `len(read_csv)` over six files |
| Brands | 6 | File count in `data/labeled/` |
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
| Rows marked 錯誤 | 0 | `value_counts()` across all six files |
| Sentiment agreement with human labels | not recorded | `validation_set.csv` absent |
| Pain-point agreement | not measured | Never validated |
| Highlight agreement | not measured | Never validated |
| Repeat-run stability | not measured | Single run |

**Zero 錯誤 rows does not mean zero failures.** `label_with_retry()` returns
`{"sentiment": "錯誤"}` only after five consecutive failures. A row that failed four times and
succeeded on the fifth is indistinguishable from one that succeeded immediately.

**Temperature 0 is not determinism.** It makes the model's output stable in principle, but no
repeat run was performed, so stability is assumed rather than observed.

---

## Reconciliation Against the Committed Summary

`outputs/competitor_summary_final.csv` was produced from a different snapshot.

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

### A 4.9% negative rate is a finding about the labelling, not the products

Nineteen negative labels across 389 valid reviews is low enough that the codebook's negative
definition, the platform's posting culture, and the model's behaviour are all plausible causes.
Distinguishing them needs the validation set that is absent.
