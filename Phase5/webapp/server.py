"""
Phase 5 (webapp) – FastAPI backend serving the plain HTML/CSS/JS DineBot
Bengaluru frontend.

Run from the project root:

    uvicorn Phase5.webapp.server:app --reload

Then open http://127.0.0.1:8000
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Importing Phase5.api_gateway pulls in Phase4.config, which loads
# GROQ_API_KEY from the project root .env as a side effect of import.
from Phase5.api_gateway import fetch_enriched_recommendations
from Phase5.config import get_cuisines, get_places, get_region
from Phase5.webapp.preferences import PRICE_OPTIONS, RATING_OPTIONS, form_to_preferences

_here = Path(__file__).resolve().parent

app = FastAPI(title="DineBot Bengaluru")
templates = Jinja2Templates(directory=str(_here / "templates"))
app.mount("/static", StaticFiles(directory=str(_here / "static")), name="static")


class RecommendationRequest(BaseModel):
    place: Optional[str] = None
    price: Optional[str] = None
    rating: Optional[str] = None
    cuisine: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "places": get_places(),
            "cuisines": get_cuisines(),
            "rating_options": RATING_OPTIONS,
            "price_options": PRICE_OPTIONS,
        },
    )


def _restaurant_to_card(rank: int, rec) -> dict:
    r = rec.restaurant
    return {
        "rank": rank,
        "name": r.name,
        "rating": r.aggregate_rating,
        "cost": r.average_cost_for_two,
        "place": r.locality,
        "cuisines": r.cuisines or [],
        "location": f"{get_region(r.locality)} Bengaluru",
        "explanation": rec.explanation,
    }


@app.post("/api/recommendations")
def get_recommendations(payload: RecommendationRequest):
    prefs = form_to_preferences(payload.place, payload.price, payload.rating, payload.cuisine)
    try:
        recs = fetch_enriched_recommendations(prefs)
    except ValueError as exc:
        # e.g. missing GROQ_API_KEY - a configuration problem, not a client error.
        return JSONResponse(status_code=500, content={"error": str(exc)})
    except Exception as exc:  # noqa: BLE001 - surface any backend failure to the UI
        return JSONResponse(status_code=502, content={"error": f"Recommendation service failed: {exc}"})

    cards = [_restaurant_to_card(i, rec) for i, rec in enumerate(recs, start=1)]
    return {"recommendations": cards, "error": None}
