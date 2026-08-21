# DineBot Bengaluru

An AI restaurant recommendation service for Bengaluru. Pick a locality, price range, minimum
rating, and cuisine, and get back a ranked list of restaurants — each with a short LLM-written
explanation of why it fits.

See [ARCHITECTURE.md](ARCHITECTURE.md) for how the pipeline is organized end to end
(`data_ingestion` → `features` → `recommender` → `ai_explanations` → `web`).

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

cp .env.example .env               # then add your GROQ_API_KEY

# Build the dataset once (writes data_ingestion/data and features/data)
python -m data_ingestion.ingestion_pipeline
python -m features.feature_pipeline

# Run the app
uvicorn web.server:app --reload
```

Open http://127.0.0.1:8000.

## Tests

```bash
pytest
```

## Project layout

| Folder | Responsibility |
|---|---|
| `data_ingestion/` | Download + validate the raw Zomato dataset (Hugging Face) |
| `features/` | Filter to Bengaluru, engineer features, build the query-ready dataset |
| `recommender/` | Deterministic candidate selection and scoring |
| `ai_explanations/` | LLM (Groq)-generated 2-line explanations per recommendation |
| `web/` | FastAPI backend + HTML/CSS/JS frontend |

Each folder owns its own `config.py` and `test_*.py` files. Full details in
[ARCHITECTURE.md](ARCHITECTURE.md).
