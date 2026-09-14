# Known Issues

Issues are classified by what is known about them, not by whether they were fixed. A resolved
item keeps its entry; the classification is the point. A-items were investigated and found not to
be defects. B-items are unverified. C-items are defects. D-items are documentation debt.

**Snapshot** 2026-09-14 · 500 labelled reviews across six brands

| ID | Issue | Class | Disposition |
|---|---|---|---|
| A-1 | No API key is committed | Not a defect | No action |
| A-2 | No reviewer identifiers in the labelled data | Not a defect | No action |
| B-1 | Sentiment agreement with human labels is unknown | Verified | Below threshold — 64–67% |
| B-2 | Pain-point and highlight labelling never validated | Unverified | Open |
| B-3 | Labelling stability across runs never tested | Verified | Mostly stable, not deterministic |
| C-1 | Committed summary disagrees with committed data | Defect | Fix recommended |
| C-2 | `analyze.py` cannot run against the committed data | Defect | Fix recommended |
| C-3 | `normalize_pain()` is defined but never called | Defect | Fix recommended |
| C-4 | 綠藤 data is committed but not analysed | Defect | Fix recommended |
| C-5 | Input paths are module-level constants edited by hand | Design limitation | Accepted, not fixed |
| C-6 | Labelling model decommissioned by Groq | Defect (external) | Fixed |
| D-1 | `data/raw/` and `labeled_reviews.csv` are referenced but absent | Documentation | Open |

---

### A-1　No API key is committed

**Verified.** `groq_label_batch.py:10` reads `os.environ.get("GROQ_API_KEY")` via `python-dotenv`.
A repository-wide search for `gsk_`, `sk-`, `api_key=` string literals, and `token` returns no
hardcoded credential.

**Check.** `grep -rniE "api[_-]?key *= *[\"']" --include="*.py" .`


---

### A-2　No reviewer identifiers in the labelled data

**Verified.** The eight columns are post_id, brand, title, content, created_at, sentiment,
pain_points, highlights. `post_id` is assigned sequentially by the crawler, not taken from the
source page.

**Observation.** `clean_brand.py` exists specifically to strip the author block — nickname, skin
type, age, review count — that @cosme prefixes to brand-page review text. That block is removed
before the data is written, so it never reaches `data/labeled/`.

---

### B-1　Sentiment agreement with human labels is unknown

**Verified: 64–67%, below the 80% threshold.**

Ran against the 33-row human-labelled validation set (`data/labeled/validation_set.csv`, now
committed) using `openai/gpt-oss-120b` — see C-6. The model actually used for the original
500-row labelling, `llama-3.3-70b-versatile`, was decommissioned by Groq on 2026-08-16 and can no
longer be queried, so it cannot be re-validated. This is raw model output with no human
correction loop, and is therefore not comparable to the "residual error rate: zero" figure in
`docs/juvaly_report.pdf`, which was reached only after iterative manual review of the original
labelling run.

Two runs: 64% (21/33) and 67% (22/33). Errors cluster on 中性 (neutral) — most often confused
with 非評論 (not-a-review) or 正面 (positive). Only one negative-label miss across both runs, and
it moved to 中性 rather than 正面; no case flipped between the two poles.

See `outputs/validation_result.json` and `outputs/validation_result_run1.json`.


**Fix direction.** None outstanding for measurement. Whether 64–67% is acceptable for this
project's purposes, and whether the codebook or prompt should be revised to reduce neutral
confusion, is an open decision, not a defect.

---

### B-2　Pain-point and highlight labelling never validated

**Symptom.** `groq_validate.py` compares only the `sentiment` field. The two multi-label columns
go to production unchecked.

**Cause.** Sentiment is a single value and comparison is a string match. Pain points are a
semicolon-separated subset of fifteen categories, so a label can be partly correct, and no
partial-credit rule was defined.

**Consequence.** The two columns the client actually asked about are the two with no accuracy
evidence.

---

### B-3　Labelling stability across runs never tested

**Verified: mostly stable, not fully deterministic.**

Same 33 rows scored twice with `temperature=0`, using `openai/gpt-oss-120b`. 30/33 predictions
(91%) identical across runs; 3 rows flipped (2 became correct, 1 became wrong), moving overall
accuracy from 64% to 67%. `temperature=0` on Groq does not guarantee identical output between
calls.

---


### C-1　Committed summary disagrees with committed data

**Symptom.** `outputs/competitor_summary_final.csv` reports valid-review counts that do not match
recomputation from `data/labeled/`.

**Observation.** Inna Organic (90) and nomel (22) agree. DR.WU reports 118 against 123, menomeno
reports 44 against 49, and Juvaly reports 33 against 9. 綠藤 does not appear at all.

**Cause.** The summary was generated from an earlier data snapshot. The Juvaly row in particular
was computed over `data/labeled/labeled_reviews.csv`, a file that is not in this repository, not
over the committed `juvaly_cosme_labeled.csv`.

**Impact.** `final_competitor_analysis.png` was produced from the same run and carries the same
discrepancy. Neither artefact can be reproduced from what is committed.

**Fix.** Rerun `analyze.py` against the committed data after C-2 and C-4 are resolved, and
regenerate both artefacts.

---

### C-2　`analyze.py` cannot run against the committed data

**Symptom.** The script fails on its first file.

**Location.** `scripts/analyze.py`, `FILES` dictionary — `'Juvaly': '../data/labeled/labeled_reviews.csv'`.

**Cause.** That filename does not exist. The committed Juvaly data is `juvaly_cosme_labeled.csv`.

**Consequence.** No partial output is produced; `pd.read_csv` raises before any brand is
processed.

**Fix.** Point the key at the committed filename.


---

### C-3　`normalize_pain()` is defined but never called

**Symptom.** The pain-point ranking described in the project report is not produced by any
committed code.

**Location.** `scripts/analyze.py`. `normalize_pain()` maps free-text pain points onto six
buckets. `main()` computes only sentiment counts and never invokes it.

**Impact.** Pain points are the client's primary question, and the aggregation for them is dead
code. Whatever produced the ranking in the report is not in this repository.

**Fix direction.** Call it from `main()`, explode the semicolon-separated column, and write a
ranked count alongside the sentiment summary.

---

### C-4　綠藤 data is committed but not
