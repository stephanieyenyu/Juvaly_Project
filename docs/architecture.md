# Architecture

There is no service and no deployment target. This is a seven-stage batch pipeline plus a
Streamlit interface, run locally against two external dependencies: the @cosme Taiwan website and
the Groq API.

---

## Stages

| Stage | File | Reads | Writes |
|---|---|---|---|
| 1 Scrape | `crawler_brand.py` | @cosme brand page | `data/raw/competitor_<brand>_<id>_multipage.csv` |
| 2 Clean (shared) | `clean_reviews.py` | in-memory DataFrame | in-memory DataFrame |
| 3 Clean (brand page) | `clean_brand.py` | `data/raw/*_multipage.csv` | `data/raw/*_clean.csv` |
| 4 Validate | `groq_validate.py` | `data/labeled/validation_set.csv` | stdout + `outputs/validation_result.json` |
| 5 Label | `groq_label_batch.py` | `data/raw/*_clean.csv` | `data/labeled/<brand>_labeled.csv` |
| 6 Aggregate | `analyze.py` | `data/labeled/*.csv` | `outputs/competitor_summary_final.csv`, `.png` |
| 7 Present | `app.py` | `data/labeled/*.csv` | Streamlit UI |

Stage 2 is a library, not a step: `crawler_brand.py` imports `clean_review_df` and applies it
before writing, so raw output is already filtered for official copy, minimum length and
duplicates.

---

## Why the stages are separate files

Each stage fails in a different way and on a different timescale. Scraping is limited by the
site, which returns 503 under load and needs a ten-second backoff per attempt. Labelling is
limited by the API, which returns 429 and needs a twenty-second backoff. A full brand takes
minutes to scrape and roughly seventeen minutes to label at the two-second inter-row delay.

Writing to disk between stages means a failure in one does not discard the work of the previous
one, and the expensive stage — labelling — can resume from its own checkpoint rather than from
the beginning.

**The accepted cost is that nothing enforces ordering or freshness.** A stale intermediate file is
read exactly like a fresh one. The disagreement recorded in `known-issues.md` C-1 is what that
costs in practice: the committed summary was computed from inputs that are no longer the
committed inputs.

---

## The codebook is shared, not duplicated

`_codebook.py` exports a single string constant. Both `groq_validate.py` and
`groq_label_batch.py` import it, and `groq_validate.py` additionally imports `label_one` from
`groq_label_batch` so that validation exercises the production call path rather than a copy of
it.

This means the standard that was measured is the standard that ran. The cost is that the
repository records no codebook version, so a past accuracy figure cannot be attached to the text
it was measured against.

---

## External dependencies

**@cosme Taiwan.** Scraped with a browser User-Agent, a `Referer` header, a three-second delay
between pages, and a fifteen-second timeout. 503 responses back off at ten seconds times the
attempt number, up to four attempts; three consecutive page failures stop the run.

**Groq API.** Originally `llama-3.3-70b-versatile`; decommissioned by Groq on 2026-08-16 partway
through this project and migrated to `openai/gpt-oss-120b` — see `known-issues.md` C-6. Temperature
0, `response_format={"type": "json_object"}`.
Retries back off at twenty seconds times the attempt for rate-limit errors and five seconds
otherwise, up to five attempts, after which the row is written as 錯誤 and can be picked up on a
later run.

Both are free-tier constrained, which is what sets the pipeline's practical size.
