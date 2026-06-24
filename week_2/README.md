# Resume Skill Gap Analyser

## Project Overview

Analyses a resume against real job listings to identify missing technical skills.

---

## Setup Instructions

**Prerequisites**
- Python 3.14+
- `uv` package manager
- Gemini API key

**Steps**

```bash
git clone https://github.com/alvinkodes/kyouth-data-ai.git
cd kyouth-data-ai/week_2
```

Create a `.env` file in the `week_2` directory:

```
GEMINI_API_KEY=your_api_key_here
```

Install dependencies:

```bash
uv sync
```

---

## Usage

**Step 1 — Tag job descriptions (one-time setup)**

Extracts tech stacks from job descriptions and writes them to the `tech_stack` column in the DB. Skip if `tech_stack` is already populated.

```bash
uv run tag_data.py
```

**Step 2 — Analyse resume**

```bash
uv run find_skill_gaps.py
```

Expected output:

```
gaps=['docker', 'fastapi', 'kubernetes', ...]
```

---

## API / Function Reference

### `tag_data(db_url: str)` — `tag_data.py`

Tags untagged job listings in the DB with their required tech stacks using Gemini LLM.

- **Input:** `db_url` — path to the SQLite3 database
- **Output:** `None` (updates `tech_stack` column in-place, batches of 40)

### `find_skill_gaps(input_file_dir: str, db_url: str) -> SkillGapResult` — `find_skill_gaps.py`

Analyses a resume and returns skills present in matching job listings but missing from the resume.

- **Input:**
  - `input_file_dir` — path to a plain-text resume file
  - `db_url` — path to the SQLite3 database
- **Output:** `SkillGapResult(gaps: List[str])` — sorted list of missing skill names (lowercase)

### `prompt_model(model: str, prompt: str) -> str` — `prompt_model.py`

Give raw text response based on the provided model and prompt.

- **Input:** `model` — Gemini model ID; `prompt` — plain text prompt
- **Output:** Raw text response from the model


---

## Data / Assumptions

**Database schema** (`data/3_gold/jobs.db`):

| Column | Type | Description |
|--------|------|-------------|
| `source_id` | TEXT | Unique job listing ID |
| `job_title` | TEXT | Job title |
| `company` | TEXT | Company name |
| `description` | TEXT | Full job description |
| `tech_stack` | TEXT | Comma-separated tech skills (populated by `tag_data`) |

**Input format:** Resume must be a plain `.txt` file.

**Key assumptions:**
- Job title matching uses cosine similarity on embeddings; threshold is **≥ 0.8** (hardcoded).
- Skill gap comparison is case-insensitive but not synonym-aware (e.g. `Postgres` ≠ `PostgreSQL` if not normalised).

---

## Testing

**Manual testing** was done using a synthetic resume (`resources/resume_d3.txt`) against the SQLite3 DB (`data/3_gold/jobs.db`).

**To reproduce:**

```bash
uv run find_skill_gaps.py
```

**Validation approach:**
- Resume skills were manually verified against the LLM extraction output.
- Matched job titles were inspected to confirm cosine similarity threshold was sensible.
- `tag_data` output was checked against raw job descriptions for accuracy.

---

## Limitations & Architecture Reflection

**Limitations:**
- Rate limit errors are handled with exponential backoff (max 5 retries, cap 10s).
- Skill gap comparison is not synonym-aware (e.g. `Postgres` ≠ `PostgreSQL` if not normalised).
- Job title matching is based on a hardcoded cosine similarity threshold (≥ 0.8).

**Architecture Reflection:**
- I decide to use cosine similarity for job title matching is due to its scalability and maintainability. The other alternatives considered were creating a ROLE_MAP that maps job_titles to specific keywords. However, as the database grows, maintaining this map becomes cumbersome.
- I prioritize scalability and maintainability over simplicity in the architecture.
- I would use better models.