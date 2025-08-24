import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from pydantic import ValidationError

import config
from models.aggregator import Aggregator
from models.read import Read
from models.revisions import Revisions
from models.splitter import Splitter
from models.validator import Validator

if "USER" not in os.environ:
    os.environ["USER"] = "tools.sparql-rc2-backend"

logging.basicConfig(level=config.LOGLEVEL)
logger = logging.getLogger(__name__)


# noinspection PyShadowingNames,PyUnusedLocal
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup code
    FastAPICache.init(InMemoryBackend())
    yield
    # shutdown code (if needed)


app = FastAPI(title="sparql-rc2-backend", lifespan=lifespan, version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or list of allowed origins
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
api_router = APIRouter(prefix="/api/v1")


def sanitize_errors(errors: Any) -> list[Any]:
    sanitized_errors_ = []
    for error in errors.errors():
        sanitized_errors_.append(
            {
                "loc": list(error["loc"]),  # tuples to lists
                "msg": error["msg"],
                "type": error["type"],
            }
        )
    return sanitized_errors_


@cache(expire=60)
@api_router.get("/revisions", response_model=list[Revisions])
def get_revisions(
    entities: str = Query(
        ..., description="Comma-separated list of entity IDs, e.g. Q42,L1"
    ),
    start_date: str = Query(
        default=(datetime.now(timezone.utc) - timedelta(days=7)).strftime(
            "%Y%m%d%H%M%S"
        ),
        description='Start of the revision date range in "YYYYMMDDHHMMSS" or "YYYYMMDD" format. Defaults to 7 days before the current UTC time.',
    ),
    end_date: str = Query(
        default=datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
        description='Start of the revision date range in "YYYYMMDDHHMMSS" or "YYYYMMDD" format. Defaults to 7 days before the current UTC time.',
    ),
    no_bots: bool = Query(
        default=False,
        description="If True, revisions made by bot accounts are excluded. Defaults to False.",
    ),
    only_unpatrolled: bool = Query(
        default=False, description="Only return unpatrolled edits"
    ),
    exclude_users: str = Query(
        default="",
        description="Comma-separated list of usernames to exclude, e.g. User1,User2",
    ),
):
    """
    Retrieve and aggregate revision data for one or more entities within a specified date range.

    This endpoint accepts a comma-separated list of entity IDs (e.g., Wikidata Q-IDs) and fetches
    all revisions made to those entities between the given start and end dates. It can optionally
    exclude revisions made by bot accounts or a list of users.

    The process includes:
    1. Parsing the entity list.
    2. Validating input parameters.
    3. Querying the revision data source.
    4. Aggregating the results for a summarized response.

    Args:
    * entities (str): Comma-separated list of entity IDs to query revisions for (e.g., "Q42,L1").
    * start_date (str, optional): Start of the revision date range in "YYYYMMDDHHMMSS" or "YYYYMMDD" format.
            Defaults to 7 days before the current UTC time.
    * end_date (str, optional): End of the revision date range in "YYYYMMDDHHMMSS" or "YYYYMMDD" format.
            Defaults to the current UTC time.
    * no_bots (bool, optional): If True, revisions made by bot accounts are excluded. Defaults to False.
    * only_unpatrolled (bool, optional): If True, revisions that are patrolled are excluded. Defaults to False.
    * exclude_users (str, optional): Comma-separated list of usernames to exclude
                    (e.g., "User1,User2"). Defaults to an empty string (no exclusions).

    Returns:
    * list[Revisions]: A list of aggregated revision objects matching the query parameters.

    Raises:
    * Error: If input parameters are invalid (e.g., date format, entity IDs, not unique input).

    Examples:
    * GET /api/v1/revisions?entities=Q42,L1&start_date=20250701000000&end_date=20250707235959&no_bots=true&exclude_users=So9q -> 200
    * GET /api/v1/revisions?entities=Q42;L1&start_date=20250701000000&end_date=20250707235959&no_bots=true -> 422

    Caching: This endpoint is using an in-memory cached with a
    timeout of 60s because the underlying data is not changing very often.
    """
    # Step 1: split entities string → list
    try:
        entity_splitter = Splitter(string=entities)
        entity_splitter.split_comma_separated_string()
        user_splitter = Splitter(string=exclude_users)
        user_splitter.split_comma_separated_string()
    except ValidationError as e:
        # Forward the error to the user with status 422
        raise HTTPException(status_code=422, detail=sanitize_errors(e)) from e
    # Step 2: validate all input (entities already split)
    try:
        params = Validator(
            entities=entity_splitter.list_,
            start_date=start_date,
            end_date=end_date,
            no_bots=no_bots,
            only_unpatrolled=only_unpatrolled,
            exclude_users=user_splitter.list_,
        )
    except ValidationError as e:
        # Forward the error to the user with status 422
        raise HTTPException(status_code=422, detail=sanitize_errors(e)) from e

    # Step 3: instantiate Read with params (assuming you changed Read to accept params)
    read = Read(params=params)
    try:
        revisions = read.fetch_revisions()
    finally:
        read.close()

    # Debug
    # pprint(revisions[0])

    # Step 4: aggregate and return
    try:
        aggregator = Aggregator(revisions=revisions)
    except ValidationError as e:
        # Forward the error to the user with status 422
        raise HTTPException(status_code=422, detail=sanitize_errors(e)) from e
    return aggregator.aggregate()


@app.get("/", include_in_schema=False)  # root redirect remains at /
def root_redirect():
    return RedirectResponse(url="/docs")


app.include_router(api_router)
