## AI Restaurant Recommendation Service – Project Architecture

This document describes the high-level architecture for the AI Restaurant Recommendation service for Bengaluru, broken into **five distinct phases**. Each phase lives in its own top-level folder and has clear responsibilities and data flow.

Top-level structure (planned):

- `Phase1/` – Data ingestion from Hugging Face
- `Phase2/` – Feature engineering and filtering
- `Phase3/` – Core recommendation engine
- `Phase4/` – LLM orchestration (Llama 3.1 via Groq)
- `Phase5/` – Streamlit UI and backend integration

An additional `shared/` area may be added later for cross-phase utilities (schemas, config, logging).

---

## Phase 1 – Data Ingestion (`Phase1/`)

**Responsibility**: Fetch and persist the raw Zomato dataset from Hugging Face, apply lightweight validation, and produce a cleaned-but-untransformed dataset for downstream phases.

**Main components**

- `Phase1/config.py`
  - Defines `DatasetConfig` (dataset name, split, data directories such as `raw` and `bronze`).
- `Phase1/dataset_downloader.py`
  - Downloads the `ManikaSaini/zomato-restaurant-recommendation` dataset from Hugging Face using the `datasets` library.
  - Caches the dataset under `Phase1/data/raw/`.
  - Persists the raw dataset into `zomato_raw.parquet` for reproducibility.
- `Phase1/schema_validation.py`
  - Defines the expected dataset columns.
  - Provides `validate_schema` to check for missing/extra columns.
  - Provides `filter_invalid_rows` to drop rows with missing critical fields (name, city, cuisines, rating).
- `Phase1/ingestion_pipeline.py`
  - Orchestrates Phase 1:
    - Downloads the dataset.
    - Validates the schema.
    - Filters invalid rows.
    - Writes a cleaned dataset to `Phase1/data/bronze/zomato_bronze.parquet`.
    - Returns the cleaned dataset, validation result, and output path.
- `Phase1/tests...`
  - Unit and integration tests for downloader, validation, and ingestion pipeline.

**Data flow**

1. Download dataset from Hugging Face into a local cache (`Phase1/data/raw/`).
2. Validate schema; log/report any missing columns.
3. Filter out rows with missing critical fields.
4. Persist:
   - Raw snapshot (`zomato_raw.parquet`) in `raw/`.
   - Cleaned dataset (`zomato_bronze.parquet`) in `bronze/`.

Output of Phase 1 feeds Phase 2.

---

## Phase 2 – Feature Engineering & Filtering (`Phase2/`)

**Responsibility**: Transform and filter the ingested data into a structure that is optimized for querying by user preferences (place, price range, ratings, cuisines) with a focus on Bengaluru.

**Planned components**

- `Phase2/config.py`
  - Feature flags and thresholds (e.g. minimum rating, valid price range, Bengaluru-only filter).
- `Phase2/filters.py`
  - Filter records to Bengaluru.
  - Normalize place/location values (e.g. neighborhoods, localities).
- `Phase2/feature_transformers.py`
  - Create normalized representations for price (buckets) and ratings.
  - Normalize and tokenize cuisines (e.g. converting string lists into canonical labels).
- `Phase2/index_builder.py`
  - Build efficient indices or grouped views for later recommendation queries.
  - Persist processed views to `Phase2/data/silver/` and `Phase2/data/gold/` (or reuse a shared data layout).
- `Phase2/feature_pipeline.py`
  - End-to-end feature pipeline that:
    - Consumes Phase 1 bronze data.
    - Applies filtering and transformation.
    - Writes feature-engineered outputs and indices.

**Data flow**

1. Read `zomato_bronze.parquet` from Phase 1.
2. Filter to Bengaluru restaurants.
3. Generate features (normalized prices, rating buckets, cuisine lists).
4. Build indices/groupings used by the recommendation engine.
5. Persist processed datasets to a feature store directory (e.g. `data/silver/`, `data/gold/`).

Output of Phase 2 feeds Phase 3.

---

## Phase 3 – Recommendation Engine Core (`Phase3/`)

**Responsibility**: Implement deterministic recommendation logic that turns user preferences into a ranked list of candidate restaurants (without natural-language explanations).

User preferences include:
- Place (Bengaluru locality).
- Price range.
- Minimum rating.
- Preferred cuisines.

**Planned components**

- `Phase3/config.py`
  - Scoring weights (relative importance of rating vs price vs cuisine match).
  - Default number of recommendations to return.
- `Phase3/schemas.py`
  - Data models (e.g. via Pydantic) for:
    - `UserPreferences` (place, price range, ratings, cuisines).
    - `RestaurantRecord` (fields used by the engine).
    - `Recommendation` (restaurant metadata + score).
- `Phase3/candidate_selector.py`
  - Filters the feature-engineered dataset from Phase 2 based on user preferences.
  - Restricts to restaurants in Bengaluru that match place/price/cuisines and rating thresholds.
- `Phase3/scoring_engine.py`
  - Assigns a score to each candidate restaurant.
  - Supports tuning weighting for:
    - Exact cuisine match.
    - Price range suitability.
    - Higher ratings.
- `Phase3/recommendation_service.py`
  - Public interface, e.g. `get_recommendations(preferences: UserPreferences) -> list[Recommendation]`.
  - Orchestrates reading Phase 2 data, candidate selection, scoring, and ranking.

**Data flow**

1. Load feature-engineered data and indices from Phase 2.
2. Accept `UserPreferences` from UI or other caller.
3. Filter candidates using `candidate_selector`.
4. Score and rank candidates.
5. Return a structured list of top-N `Recommendation` objects to Phase 4.

---

## Phase 4 – LLM Orchestration with Llama 3.1 (`Phase4/`)

**Responsibility**: Enrich structured recommendations from Phase 3 with concise natural-language justifications using Llama 3.1 accessed through the Groq API.

Each recommended restaurant should have a short **2-line explanation** focusing on:
- Price suitability.
- Ratings.
- Cuisines.

**LLM integration details**

- Model: **Llama 3.1**.
- Provider: **Groq** (API key from Groq dashboard, e.g. `GROQ_API_KEY` in `.env`).

**Planned components**

- `Phase4/config.py`
  - LLM configuration: model name, temperature, max tokens, timeouts.
  - Environment variable loading for `GROQ_API_KEY`.
- `Phase4/groq_client.py`
  - Encapsulates HTTP calls to Groq’s completion/chat API.
  - Responsible for authentication, retries, and error handling.
- `Phase4/prompt_templates.py`
  - Templates that describe:
    - User preferences (place, price range, rating, cuisines).
    - Candidate restaurant attributes (name, price, rating, cuisines).
    - Instructions to respond with exactly 2 lines per restaurant.
- `Phase4/llm_formatter.py`
  - Maps Phase 3 `Recommendation` objects + `UserPreferences` into an LLM prompt.
  - Parses the LLM’s response back into a structured set of explanations.
- `Phase4/llm_recommendation_service.py`
  - High-level API, e.g.:
    - `get_enriched_recommendations(preferences: UserPreferences) -> list[LLMEnrichedRecommendation]`
  - Orchestrates:
    - Calls Phase 3 `get_recommendations`.
    - Builds a batched prompt.
    - Calls `groq_client` with Llama 3.1.
    - Attaches explanations to each restaurant.

**Data flow**

1. Receive user preferences.
2. Call Phase 3 to get ranked `Recommendation` objects.
3. Build an LLM prompt summarizing:
   - User preferences.
   - Details for each recommended restaurant.
4. Call Llama 3.1 via Groq.
5. Parse 2-line explanations per restaurant.
6. Return `LLMEnrichedRecommendation` objects (metadata + explanation) to Phase 5.

---

## Phase 5 – Streamlit UI & Backend Integration (`Phase5/`)

**Responsibility**: Provide a Streamlit-based UI where users can enter their preferences and receive enriched restaurant recommendations with clear, concise justifications.

The final page must:
- Allow the user to set:
  - Place (Bengaluru locality).
  - Price range.
  - Minimum rating.
  - Preferred cuisines (multi-select).
- Display:
  - Recommended restaurants as rich cards.
  - A 2-line explanation per recommendation from the LLM.

**Planned components**

- `Phase5/config.py`
  - UI defaults (e.g. default locality, default rating threshold).
- `Phase5/state_management.py`
  - Manages Streamlit session state (inputs, last results, loading indicators).
- `Phase5/components/filters_sidebar.py`
  - Sidebar widgets:
    - Text input / dropdown for place.
    - Sliders for price range and rating.
    - Multiselect for cuisines.
- `Phase5/components/results_view.py`
  - Renders recommendation cards:
    - Restaurant name, locality, rating, price, cuisines.
    - 2-line explanation from Llama 3.1.
  - Optional pagination or sorting controls.
- `Phase5/api_gateway.py`
  - Thin adapter between UI and Phase 4:
    - Converts Streamlit form data into `UserPreferences`.
    - Calls `get_enriched_recommendations` from Phase 4.
    - Handles and surfaces errors in a user-friendly way.
- `Phase5/app.py`
  - Streamlit entrypoint (`streamlit run Phase5/app.py`).
  - Wires together sidebar filters, API gateway calls, and results view.

**Data flow**

1. User opens the Streamlit app and enters preferences.
2. UI converts those inputs into a `UserPreferences` structure.
3. UI calls the `api_gateway`, which:
   - Invokes Phase 4 LLM orchestration → which in turn calls Phase 3 → which uses Phase 2 outputs → which originate from Phase 1 ingestion.
4. UI displays enriched recommendations with explanations and allows the user to refine their filters.

---

## Tooling and Implementation Notes

- **IDE**: Cursor is used to write and maintain the codebase, leveraging AI assistance where helpful.
- **Language & libraries**:
  - Python for all phases.
  - `datasets` (Hugging Face) for data loading.
  - `pyarrow`/Parquet for on-disk dataset storage.
  - Streamlit for the UI.
  - Groq Python/HTTP client for Llama 3.1 integration.
- **Configuration**:
  - Root-level `.env` / `.env.example` for secrets (e.g. `GROQ_API_KEY`).
  - Consistent configuration objects per phase (`config.py`).
- **Testing**:
  - Each phase includes its own tests under its folder (e.g. `Phase1/test_*.py`).
  - Later phases will mock external dependencies (e.g. Groq API, filesystem) where appropriate.

