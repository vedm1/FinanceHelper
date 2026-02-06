from pydantic import BaseModel
from typing import Optional


class QueryRequest(BaseModel):
    query: str
    owner: Optional[str] = None
    company: Optional[str] = None
    category: Optional[str] = None
    year: Optional[int] = None


class SourceDoc(BaseModel):
    source: str
    content: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceDoc]


class GraphStatsResponse(BaseModel):
    documents: int
    owners: int
    companies: int
    categories: int
    years: int


class GraphNode(BaseModel):
    id: str
    label: str
    type: str


class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str


class GraphDataResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]