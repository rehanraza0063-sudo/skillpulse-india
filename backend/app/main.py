"""
SkillPulse India - FastAPI application.
Run from the backend folder:   uvicorn app.main:app --reload
Interactive API docs:          http://localhost:8000/docs
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes import router
from .config import DATA_DIR, DEMO_LABEL
from .db import Database
from .ml.taxonomy import Taxonomy
from .services.engine import Engine
from .services.ingestion import ingest_all

log = logging.getLogger("skillpulse")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pipeline: data files -> ingestion -> cleaning / normalisation -> database -> engine (forecasts, gaps)
    try:
        db = Database()
        tax = Taxonomy(DATA_DIR)
        ing_log = ingest_all(db, tax)
        app.state.db = db
        app.state.engine = Engine(db, tax, ing_log)
        log.info("SkillPulse engine ready (%s). %s", db.describe(), DEMO_LABEL)
    except FileNotFoundError as exc:
        app.state.engine = None
        log.error("Demo data missing: %s", exc)
        log.error("Generate it with:  python scripts/generate_demo_data.py")
    yield


app = FastAPI(
    title="SkillPulse India API",
    description=("Labour-market intelligence and skill-planning prototype. "
                 f"{DEMO_LABEL}. Forecasts are 'Prototype Forecast'; recommendations are 'Prototype Decision Support'."),
    version="0.1.0-prototype",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:4173"],
    allow_methods=["*"], allow_headers=["*"],
)


@app.exception_handler(KeyError)
async def key_error_handler(_: Request, exc: KeyError):
    return JSONResponse(status_code=404, content={"error": "not_found", "detail": str(exc.args[0]) if exc.args else "Not found"})


@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"error": "bad_request", "detail": str(exc)})


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": "validation_error", "detail": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_handler(_: Request, exc: Exception):
    log.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"error": "internal_error", "detail": "Unexpected server error. See the server log."})


app.include_router(router)


@app.get("/")
def root():
    return {"name": "SkillPulse India API", "mode": "DEMO MODE", "data_label": DEMO_LABEL, "docs": "/docs"}
