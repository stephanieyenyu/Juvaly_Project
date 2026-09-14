# Juvaly Review Analysis — Sentiment Labelling for a Cosmetics Brand and Five Competitors

A competitor review analysis built for Juvaly, a Taiwanese cosmetics brand. Reviews were
scraped from @cosme Taiwan, cleaned, labelled by a language model against a written codebook,
and aggregated into a sentiment and pain-point comparison across six brands.

Scraping the reviews is not the hard part. Three things took the work. **Deciding what counts
as a review**, because brand pages on @cosme mix real user posts with copied marketing text,
and a sentiment rate computed over both is meaningless. **Making the model label consistently**,
because an unconstrained model calls polite filler positive and reads "not greasy" as a
complaint about greasiness. **Knowing whether the labels are any good**, which is why a human-
labelled validation set gates the batch run rather than following it.

What is here is a seven-stage pipeline, a codebook, 500 labelled reviews across six brands, and a
record of which committed figures can be reproduced from the committed data. As of 2026-09-14,
all of them can, except one figure — see [Demo](#demo).

---

## Demo

![Competitor sentiment and pain-point comparison](outputs/final_competitor_analysis.png)

*Aggregate output: sentiment distribution and pain-point ranking across the six brands. This
figure was produced from an earlier data snapshot and has not been regenerated —
`scripts/analyze.py` has no plotting code path to produce it from. The underlying numbers
(`outputs/competitor_summary_final.csv`, `outputs/pain_point_ranking.csv`) are current; only this
image is stale. See [`docs/known-issues.md`](docs/known-issues.md) C-1.*

---

## What It Does


**Treats marketing copy as a labelling class rather than filtering it upstream.** The codebook
defines 非評論 (not a review) as a fourth sentiment value, so text that turns out to be official
copy is recorded as such instead of silently dropped. Across 500 labelled rows, 111 fall into
this class — 22.2% of everything scraped.

**Gates the batch run on measured agreement.** `groq_validate.py` runs the same labelling
function over a human-labelled set, prints per-case disagreements, and writes the result to
`outputs/validation_result.json`. The intended threshold was 80% before committing to the full
run. Two runs against the committed validation set scored 72.7% and 69.7%, using a replacement
model — see [Test Setup and Success Criterion](#test-setup-and-success-criterion). The threshold
was not met.

**Shares one codebook between validation and production.** `_codebook.py` is imported by both
`groq_validate.py` and `groq_label_batch.py`. The standard that was measured is therefore the
same standard that ran, rather than two prompts that drifted apart.

**Encodes the failure modes it actually hit.** The codebook carries four explicit rules, each
written against a misclassification: "not greasy" is a highlight and never a complaint about
texture; polite praise is neutral, not positive; agreeing with a brand's philosophy is not
satisfaction with its product; sponsored posts that reproduce official copy are 非評論.

**Resumes rather than restarts.** The batch labeller checkpoints every ten rows and, on a second
run, reprocesses only rows whose sentiment is missing or marked 錯誤. No row in the committed
data carries 錯誤, so the retry path either never fired or always recovered.

---

## Scope

| Component | Covers |
|---|---|

| `scripts/crawler_brand.py` | Paged scrape of one @cosme brand page, with 503 backoff |
| `scripts/clean_reviews.py` | Shared cleaner: official copy, minimum length, duplicates |
| `scripts/clean_brand.py` | Strips the author block that prefixes brand-page review text |
| `scripts/_codebook.py` | The labelling standard, shared by validation and production |
| `scripts/groq_validate.py` | Agreement check against human labels, writes result to `outputs/` |
| `scripts/groq_label_batch.py` | Batch labelling, checkpointed and rate-limit aware |
| `scripts/analyze.py` | Cross-brand aggregation, sentiment summary, and pain-point ranking |
| `app.py` | Streamlit interface over the labelled data |

8 Python files · 7 labelled datasets (6 brand + 1 validation) · 500 labelled reviews · 6 brands ·
4 sentiment classes · 15 pain-point categories · 10 highlight categories

Row counts come from `pandas.read_csv` rather than line counting, because review text contains
embedded newlines. Category counts are the enumerated options in `_codebook.py`, including 其他.

Developed 2026.

---

## Test Setup and Success Criterion

The original 500-row labelling ran against `llama-3.3-70b-versatile` through the Groq API at
temperature 0 with a JSON response format. That model was decommissioned by Groq on 2026-08-16
(see [`docs/known-issues.md`](docs/known-issues.md) C-6) and cannot be queried again — the
committed labelled data is unaffected, but it can never be re-validated against the model that
actually produced it.

The success criterion was agreement with human labels on a held-out set, at 80% or better on
sentiment before the batch run proceeded. **Evaluated, with a caveat.** Two runs against the
33-row validation set with `openai/gpt-oss-120b`, the replacement model, scored 72.7% and 69.7% —
below the threshold. This measures the replacement model's raw, uncorrected performance, not the
originally-delivered labelling, which was corrected through manual review before delivery (see

`docs/juvaly_report.pdf`). Errors cluster on neutral-sentiment reviews being confused with
non-review or positive; see C-1 in known-issues for the full breakdown.

Pain points and highlights were never validated against human labels at all. Only sentiment was.

---

## Measurement Basis

| Measurement | Value | Nature |
|---|---|---|
| Labelled reviews, all brands | 500 | Observed, committed data |
| Classed 非評論 | 111 (22.2%) | Observed |
| Classed 錯誤 | 0 | Observed |
| Valid reviews after excluding 非評論 | 389 | Derived |
| Brands | 6 | Test parameter |
| Sentiment agreement with human labels | 69.7–72.7% (two runs) | Measured, below 80% threshold, replacement model |
| Pain-point labelling accuracy | not measured | Never validated |
| Highlight labelling accuracy | not measured | Never validated |
| Reviews discarded during cleaning | not recorded | Raw data absent |
| Inter-run labelling stability | 91% (30/33) identical | Measured, two runs |

Three qualifications govern how the table should be read.

**Positive rate is not brand sentiment.** @cosme is a review platform whose posting population
skews towards users motivated enough to write. A 66% positive rate describes the reviews that
exist on that platform for that brand, not the opinion of its customers.

**Juvaly's own sample is too small to compare.** Nine valid reviews against 123 for DR.WU. Any
rate computed over nine rows moves by 11 points per row, so the client's own column in the
comparison is not on the same footing as the competitor columns.


**The 非評論 rate is a property of the brand page, not the brand.** Inna Organic's 36.2% is the
highest in the set, which says its brand page carries proportionally more copied marketing text.
It says nothing about the product.

---

## Problem Statement

A brand wants to know what reviewers complain about, in its own reviews and in its competitors'.
The obvious approach is to scrape the reviews and run sentiment analysis over them.

That fails twice. First, brand pages are not review corpora: they interleave user posts with
product descriptions and sponsored text that reproduces official copy, and any rate computed
over the mixture is a rate over an unknown denominator. Second, an off-the-shelf sentiment model
returns a polarity but not a reason, and a brand cannot act on polarity. What it can act on is
"reviewers who dislike this say it is greasy" — which requires a labelling scheme somebody has
to define, and a way to check that the labels follow it.

The problem this repository addresses is therefore: define a labelling standard for a specific
product category, and establish whether a language model applies it consistently enough to use.

---

## Shared Pipeline and Data Flow

There is no service and no deployment target. Seven scripts run in sequence, each reading the
previous one's output from disk.
