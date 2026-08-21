# Web – Frontend & Backend Integration

The **DineBot Bengaluru** UI: a "Get Recommendation" card with four dropdowns and a **Get
recommendations** button, and a **Top recommendations** section with numbered cards and LLM
explanations.

A hand-authored HTML/CSS/JS page (native `<select>` dropdowns, no framework) served by a small
FastAPI backend that wraps `recommender` (recommendation engine) and `ai_explanations` (LLM
enrichment).

### Colors

- **Background:** `#74212b`
- **Cards (filter panel & recommendation cards):** `#f7eeee`
- **Text:** `#241820`
- **Button:** background `#8d2634`, hover `#761f2c`, text `#fff`

### Run

From the **project root** (so `recommender` and `ai_explanations` are on the path):

```bash
pip install -r requirements.txt
uvicorn web.server:app --reload
```

Then open http://127.0.0.1:8000. Ensure the project root `.env` has `GROQ_API_KEY`.

### Structure

| File / folder             | Purpose |
|----------------------------|---------|
| `server.py`                 | FastAPI app: serves the page, `POST /api/recommendations` |
| `preferences.py`            | Form values (`"3.0+"`, `"₹300 - ₹600"`, ...) → `UserPreferences` |
| `api_gateway.py`            | Calls `ai_explanations`, dedupes recommendations by name |
| `config.py`                 | Place/cuisine dropdown options, locality-to-region lookup |
| `templates/index.html`      | The page (real place/cuisine options templated in server-side) |
| `test_*.py`                 | Tests |

### Tests

From the **project root**:

```bash
pip install -r requirements-dev.txt
pytest web/ -v
```
