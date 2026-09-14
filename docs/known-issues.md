# Known Issues

Issues are classified by what is known about them, not by whether they were fixed. A resolved
item keeps its entry; the classification is the point. A-items were investigated and found not to
be defects. B-items are unverified. C-items are defects. D-items are documentation debt.

**Snapshot** 2026-09-14 · 500 labelled reviews across six brands

| ID | Issue | Class | Disposition |
|---|---|---|---|
| A-1 | No API key is committed | Not a defect | No action |
| A-2 | No reviewer identifiers in the labelled data | Not a defect | No action |
| B-1 | Sentiment agreement with human labels is unknown | Verified | Below threshold — 69.7–72.7% |
| B-2 | Pain-point and highlight labelling never validated | Unverified | Open |
| B-3 | Labelling stability across runs never tested | Verified | Mostly stable, not deterministic |
| C-1 | Committed summary disagreed with committed data | Defect | Fixed |
| C-2 | `analyze.py` could not run against the committed data | Defect | Fixed |
| C-3 | `normalize_pain()` was defined but never called | Defect | Fixed |
| C-4 | 綠藤 data was committed but not analysed | Defect | Fixed |
| C-5 | Input paths are module-level constants edited by hand | Design limitation | Accepted, not fixed |
| C-6 | Labelling model decommissioned by Groq | Defect (external) | Fixed |
| D-1 | `data/raw/` is referenced but absent | Documentation | Open |

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

**Verified: 69.7–72.7%, below the 80% threshold.**

Ran against the 33-row human-labelled validation set (`data/labeled/validation_set.csv`) using
`openai/gpt-oss-120b` — see C-6. The model actually used for the original 500-row labelling,
`llama-3.3-70b-versatile`, was decommissioned by Groq on 2026-08-16 and can no longer be queried,
so it cannot be re-validated. This is raw model output with no human correction loop, and is
therefore not comparable to the "residual error rate: zero" figure in `docs/juvaly_report.pdf`,
which was reached only after iterative manual review of the original labelling run.

Two runs: 72.7% (24/33) and 69.7% (23/33). Errors cluster on 中性 (neutral) — confused with
非評論 (not-a-review), 正面, and in one case 負面. The validation set contains exactly one 負面
row; both runs missed it, assigning 中性 rather than 正面 — a negative case is never mistaken for
a positive one in either run, but the sample is too small (n=1) to say anything general about
negative recall.

See `outputs/validation_result.json` (69.7%) and `outputs/validation_result_run1.json` (72.7%).

**Fix direction.** None outstanding for measurement. Whether 70% is acceptable for this project's
purposes, and whether the codebook or prompt should be revised to reduce neutral confusion, is an
open decision, not a defect.

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
(91%) identical across runs; 3 rows flipped — one moved from wrong to right, two moved from right
to wrong — netting 24 correct in one run against 23 in the other. `temperature=0` on Groq does
not guarantee identical output between calls. One row failed outright (`錯誤`) in one run and
succeeded on the other, consistent with an ordinary transient API failure rather than a labelling
disagreement.

---

### C-1　Committed summary disagreed with committed data

**Fixed.**

**Symptom.** `outputs/competitor_summary_final.csv` reported valid-review counts that did not
match recomputation from `data/labeled/`.

**Cause.** The summary was generated from an earlier data snapshot — the Juvaly row in particular
was computed over `data/labeled/labeled_reviews.csv`, a file never in this repository, instead of
the committed `juvaly_cosme_labeled.csv` (C-2), and 綠藤 was never included (C-4).

**Fix.** Resolved as a byproduct of C-2 and C-4. `analyze.py` rerun against the committed data;
`outputs/competitor_summary_final.csv` now reads 123 / 90 / 96 / 49 / 22 / 9 valid reviews for
DR.WU / Inna Organic / 綠藤 / menomeno+簡單 / nomel / Juvaly, matching independent recomputation
in `docs/metrics.md`.

**Not fixed by this.** `outputs/final_competitor_analysis.png` was produced from the old snapshot
and was not regenerated — `analyze.py` has no plotting code in `main()` to regenerate it from.
The demo image should still be treated as stale.

---

### C-2　`analyze.py` could not run against the committed data

**Fixed.**

**Symptom.** The script failed on its first file.

**Cause.** `FILES['Juvaly']` pointed at `../data/labeled/labeled_reviews.csv`, which does not
exist. The committed Juvaly data is `juvaly_cosme_labeled.csv`.

**Fix.** `FILES['Juvaly']` now points at the committed filename. Verified: the script runs end to
end against all six committed CSVs.

---

### C-3　`normalize_pain()` was defined but never called

**Fixed.**

**Symptom.** The pain-point ranking described in the project report was not produced by any
committed code.

**Fix.** `main()` now explodes the semicolon-separated `pain_points` column, maps each token
through `normalize_pain()`, and writes a ranked count to `outputs/pain_point_ranking.csv`. Result:
質地黏膩 37 mentions (5 brands) · 效果無感 14 · 吸收慢 13 · 價格偏高 12 (including Juvaly, 1
mention) · 包裝設計 11 · 香味問題 9.

**Consequence that remains.** These numbers do not match the pain-point ranking in
`docs/juvaly_report.pdf` (28 / 8 / 8 / 8 / 5 / 5), which was tallied by hand under different
matching rules before this code existed. The report has not been revised to match. The two
documents now disagree on a figure both present as authoritative, and only one is reproducible
from committed code.

---

### C-4　綠藤 data was committed but not analysed

**Fixed.**

**Symptom.** `data/labeled/綠藤_110_labeled.csv` held 110 labelled reviews, 96 of them valid. The
brand appeared in no output.

**Fix.** Added to `FILES` in `analyze.py`. 綠藤 now appears in `competitor_summary_final.csv`
(96 valid, 64% positive) and in `pain_point_ranking.csv`.

---

### C-5　Input paths are module-level constants edited by hand

> Accepted, not fixed. The pipeline ran six times in one session and the cost of a CLI was not
> justified at that scale.

**Symptom.** `crawler_brand.py` has `BRAND_ID` and `BRAND_NAME` at the top; `clean_brand.py` and
`groq_label_batch.py` have `INPUT`/`OUTPUT` constants with the literal placeholder `BRAND` and a
comment saying to edit them.

**Consequence.** Running a stage without editing every constant writes over the previous brand's
output under the previous brand's filename. Nothing detects this — this is how C-1 happened.

**Fix direction.** Take the brand as a command-line argument and derive all paths from it.

---

### C-6　Labelling model decommissioned by Groq

**Fixed.**

**Symptom.** `groq_label_batch.py` and, by extension, `groq_validate.py` (which imports its
`label_one()`) began returning `404 model_not_found` on every call.

**Cause.** `llama-3.3-70b-versatile` — the model that produced every committed
`data/labeled/*.csv` file — was decommissioned by Groq on 2026-08-16.

**Fix.** `MODEL` in `groq_label_batch.py` migrated to `openai/gpt-oss-120b`, one of Groq's two
recommended replacements. Confirmed working; see B-1.

**Consequence that is not fixed and cannot be.** The committed labelled data itself is
unaffected — it was produced while the old model was live, and does not need to be redone. But it
can never be re-validated against the model that actually produced it. B-1 and B-3 measure the
replacement model, not the original — this is a permanent gap, not a temporary one. Any future
re-labelling (new brands, new reviews) will run on the replacement model, which performs
differently (see B-1) and does not clear this project's own 80% bar out of the box.

---

### D-1　`data/raw/` is referenced but absent

**Symptom.** `data/raw/` (crawler output, cleaner input) is read by committed code and does not
exist. `data/labeled/validation_set.csv` and `data/labeled/labeled_reviews.csv` were previously in
this list; the former is now committed (B-1) and the latter is resolved by C-2, not by committing
a new file.

**Impact.** The pipeline cannot be run end to end from a fresh clone. The crawl-through-clean
stages have no input.

**Fix.** Either commit `data/raw/` or state in the README which stages are reproducible and which
are not. The README currently does the latter.
