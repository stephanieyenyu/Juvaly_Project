# Known Issues

Issues are classified by what is known about them, not by whether they were fixed. A resolved
item keeps its entry; the classification is the point. A-items were investigated and found not to
be defects. B-items are unverified. C-items are defects. D-items are documentation debt.

**Snapshot** 2026-09-13 · 500 labelled reviews across six brands

| ID | Issue | Class | Disposition |
|---|---|---|---|
| A-1 | No API key is committed | Not a defect | No action |
| A-2 | No reviewer identifiers in the labelled data | Not a defect | No action |
| B-1 | Sentiment agreement with human labels is unknown | Unverified | Open |
| B-2 | Pain-point and highlight labelling never validated | Unverified | Open |
| B-3 | Labelling stability across runs never tested | Unverified | Open |
| C-1 | Committed summary disagrees with committed data | Defect | Fix recommended |
| C-2 | `analyze.py` cannot run against the committed data | Defect | Fix recommended |
| C-3 | `normalize_pain()` is defined but never called | Defect | Fix recommended |
| C-4 | 綠藤 data is committed but not analysed | Defect | Fix recommended |
| C-5 | Input paths are module-level constants edited by hand | Design limitation | Accepted, not fixed |
| D-1 | `data/raw/` and `validation_set.csv` are referenced but absent | Documentation | Open |

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

**Symptom.** `groq_validate.py` is the quality gate for the entire pipeline, and its result is
not recorded anywhere.

**Cause.** The script reads `data/labeled/validation_set.csv`, which is not committed. It prints
accuracy to stdout and writes nothing to disk.

**Impact.** The 80% threshold described in the script's docstring cannot be shown to have been
met. Every downstream figure rests on an unverifiable claim.

**Fix direction.** Commit the validation set and have the script write its result to a file
rather than printing it.

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

**Symptom.** Temperature is 0 and the response format is JSON, which should make output stable.
No second run was performed to confirm it.

**Assessment.** Low risk, but unmeasured. A ten-row repeat would settle it.

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

### C-4　綠藤 data is committed but not analysed

**Symptom.** `data/labeled/綠藤_110_labeled.csv` holds 110 labelled reviews, 96 of them valid.
The brand appears in no output.

**Cause.** It is absent from the `FILES` dictionary in `analyze.py`.

**Impact.** The largest competitor dataset after DR.WU and Inna Organic is excluded from every
comparison.

**Fix.** Add the entry.

---

### C-5　Input paths are module-level constants edited by hand

> Accepted, not fixed. The pipeline ran six times in one session and the cost of a CLI was not
> justified at that scale.

**Symptom.** `crawler_brand.py` has `BRAND_ID` and `BRAND_NAME` at the top; `clean_brand.py` and
`groq_label_batch.py` have `INPUT`/`OUTPUT` constants with the literal placeholder `BRAND` and a
comment saying to edit them.

**Consequence.** Running a stage without editing every constant writes over the previous brand's
output under the previous brand's filename. Nothing detects this, and C-1 is consistent with it
having happened.

**Fix direction.** Take the brand as a command-line argument and derive all paths from it.

---

### D-1　`data/raw/` and `validation_set.csv` are referenced but absent

**Symptom.** Three paths are read by committed code and do not exist: `data/raw/` (crawler output,
cleaner input), `data/labeled/validation_set.csv` (validation gate), and
`data/labeled/labeled_reviews.csv` (analysis input for Juvaly).

**Impact.** The pipeline cannot be run end to end from a fresh clone. Stages four through seven
have no input.

**Fix.** Either commit the missing files or state in the README which stages are reproducible and
which are not. The README currently does the latter.
