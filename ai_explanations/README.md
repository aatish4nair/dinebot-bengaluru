# AI Explanations – LLM Orchestration (Groq)

Enriches recommender output with **2-line natural-language justifications** using a Groq-hosted
chat model (see `config.py` for the current model — Groq has retired the Llama 3.1 family this
was originally built against).

## Setup

1. **API key**
   Put your Groq API key in the project root `.env`:
   ```bash
   GROQ_API_KEY=gsk_your_key_here
   ```

2. **Dependencies** (from the project root):
   ```bash
   pip install -r requirements.txt
   ```

## Confirm API key

From the project root:
```bash
python ai_explanations/verify_api_key.py
```
This loads the project root `.env`, checks that `GROQ_API_KEY` is set, and optionally makes one Groq API call.

## Usage

From the project root (so `recommender` is importable):

```python
from recommender.schemas import UserPreferences
from ai_explanations.llm_recommendation_service import get_enriched_recommendations

prefs = UserPreferences(
    place="Koramangala",
    min_rating=4.0,
    max_price_for_two=1500,
    cuisines=["North Indian", "Chinese"],
)
enriched = get_enriched_recommendations(prefs)
for e in enriched:
    print(e.restaurant.name, "-", e.explanation)
```

## Components

| File | Role |
|------|------|
| `config.py` | LLM config; loads `GROQ_API_KEY` from the project root `.env` |
| `groq_client.py` | Groq chat completion with retries and error handling |
| `prompt_templates.py` | Prompt text for user prefs + restaurant list + 2-line instruction |
| `llm_formatter.py` | Build messages and parse LLM response into per-restaurant explanations |
| `llm_recommendation_service.py` | `get_enriched_recommendations(preferences)` – main API |
| `schemas.py` | `LLMEnrichedRecommendation` (restaurant + score + explanation) |

## Tests

From the **project root**:

```bash
pip install -r requirements-dev.txt
pytest ai_explanations/ -v
```

- **Unit tests** (mocked): config, Groq client, prompt templates, formatter, recommendation service.
- **Integration tests** (`test_integration_groq.py`): run only when `GROQ_API_KEY` is set (e.g. from the project root `.env`) and the `features` gold dataset exists; they call the real Groq API and full pipeline.

All code and tests for this stage live in this folder.
