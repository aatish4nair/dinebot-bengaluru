# Phase 5 – Frontend & Backend Integration

Phase 5 provides the **DineBot Bengaluru** UI: a "Get Recommendation" card with four dropdowns
and a **Get recommendations** button, and a **Top recommendations** section with numbered cards
and LLM explanations.

There are two frontends. **`webapp/` is the primary one** (matches the plain HTML/CSS/JS design
exactly). `app.py` (Streamlit) is kept as a legacy alternative — still working and tested, but no
longer the one being actively designed against.

## webapp/ (primary) – plain HTML/CSS/JS + FastAPI

A hand-authored HTML/CSS/JS page (native `<select>` dropdowns, no framework) served by a small
FastAPI backend that wraps Phase 3 (recommendation engine) and Phase 4 (LLM enrichment).

### Colors

- **Background:** `#74212b`
- **Cards (filter panel & recommendation cards):** `#f7eeee`
- **Text:** `#241820`
- **Button:** background `#8d2634`, hover `#761f2c`, text `#fff`

### Run

From the **project root** (so Phase 3/4 are on the path):

```bash
pip install -r Phase5/webapp/requirements.txt
uvicorn Phase5.webapp.server:app --reload
```

Then open http://127.0.0.1:8000. Ensure the project root `.env` has `GROQ_API_KEY`.

### Structure

| File / folder                    | Purpose |
|-----------------------------------|---------|
| `webapp/server.py`                 | FastAPI app: serves the page, `POST /api/recommendations` |
| `webapp/preferences.py`            | Form values (`"3.0+"`, `"₹300 - ₹600"`, ...) → `UserPreferences` |
| `webapp/templates/index.html`      | The page (real place/cuisine options templated in server-side) |
| `webapp/test_server.py`, `webapp/test_preferences.py` | Tests |

### Tests

```bash
pytest Phase5/webapp -v
```

## app.py (legacy) – Streamlit

### Colors (from ui.webp)

- **Background:** `#71262b`
- **Cards (Get Recommendation & Top recommendations):** `#f8eeeb`
- **Text:** `#010203`
- **Get Recommendations button:** background `#71262b`, text `#f8eeeb`

### Get Recommendation card

- **Place:** 30 Bengaluru locations, alphabetical. Placeholder: "Choose a place".
- **Ratings:** 4 options — Less than 3.0, 3.0 - 4.0, 4.0 - 5.0, More than 5.0. Placeholder: "Choose a rating".
- **Price Range:** 4 options — Less than ₹300, ₹300 - ₹600, ₹600 - ₹1000, Above ₹1000. Placeholder: "Choose a price-range".
- **Cuisines:** Single select, alphabetical. Placeholder: "Choose a cuisine".
- **Get Recommendations** button: centered; on click, calls Phase 4 (LLM) and shows **Top recommendations** in card format, numbered 1., 2., … with no duplicate restaurant names.

### Run the app

From **project root** (so Phase 3 and Phase 4 are on the path):

```bash
streamlit run Phase5/app.py
```

Ensure the project root `.env` has `GROQ_API_KEY` for LLM recommendations.

### Tests

```bash
pytest Phase5/*.py Phase5/components -v
```

### Structure

| File / folder        | Purpose |
|----------------------|--------|
| `config.py`          | Colors, 30 places, 4 rating/price options, cuisines; placeholders not in options |
| `state_management.py`| Session state for inputs and results |
| `api_gateway.py`     | Form → `UserPreferences`, Phase 4 call, dedupe by name |
| `components/filters_card.py` | Get Recommendation card (4 dropdowns + button) |
| `components/results_view.py` | Top recommendations cards (numbered, LLM explanation) |
| `app.py`             | Streamlit entrypoint |
