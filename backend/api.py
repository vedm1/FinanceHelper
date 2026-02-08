import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core import run_langgraph
from backend.schemas import (
    QueryRequest,
    QueryResponse,
    SourceDoc,
    GraphStatsResponse,
    GraphDataResponse,
)
from graph_manager import GraphManager

gm: GraphManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global gm
    gm = GraphManager()
    gm.connect()
    yield
    gm.close()


app = FastAPI(title="KnowledgeBot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    try:
        result = run_langgraph(
            query=req.query,
            owner=req.owner,
            company=req.company,
            category=req.category,
            year=req.year,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    answer = str(result.get("answer", "")).strip() or "(No answer received)"

    # Extract unique sources from the flat document list
    seen = set()
    sources = []
    for doc in result.get("context", []):
        source = getattr(doc, "metadata", {}).get("source", "Unknown")
        if source not in seen:
            seen.add(source)
            sources.append(SourceDoc(
                source=source,
                content=getattr(doc, "page_content", "")[:500],
            ))

    return QueryResponse(answer=answer, sources=sources)


@app.get("/api/metadata/owners")
async def get_owners() -> list[str]:
    return gm.get_all_owners()


@app.get("/api/metadata/companies")
async def get_companies() -> list[str]:
    return gm.get_all_companies()


@app.get("/api/metadata/categories")
async def get_categories() -> list[str]:
    return gm.get_all_categories()


@app.get("/api/metadata/stats", response_model=GraphStatsResponse)
async def get_stats():
    return gm.get_graph_stats()


@app.get("/api/graph/data", response_model=GraphDataResponse)
async def get_graph_data():
    return gm.get_graph_data()