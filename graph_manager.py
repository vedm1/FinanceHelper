"""
Graph Manager for Document Metadata using Neo4j

This module handles:
- Neo4j connection management
- Document node creation with metadata
- Graph queries for filtering documents before vector search
"""

import os
from pathlib import Path
from typing import Optional
import yaml
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv(override=True)


class GraphManager:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password123")
        self.driver = None
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load document metadata configuration from YAML."""
        config_path = Path(__file__).parent / "document_config.yaml"
        if config_path.exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        return {"defaults": {}, "documents": {}}

    def connect(self):
        """Establish connection to Neo4j."""
        if not self.driver:
            self.driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
        return self

    def close(self):
        """Close the Neo4j connection."""
        if self.driver:
            self.driver.close()
            self.driver = None

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def clear_graph(self):
        """Remove all nodes and relationships from the graph."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def create_indexes(self):
        """Create indexes for efficient querying."""
        with self.driver.session() as session:
            # Create indexes for common query patterns
            session.run("CREATE INDEX IF NOT EXISTS FOR (d:Document) ON (d.source)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (o:Owner) ON (o.name)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (c:Company) ON (c.name)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (cat:Category) ON (cat.name)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (y:Year) ON (y.value)")

    def get_document_metadata(self, filename: str) -> dict:
        """Get metadata for a document from config, with defaults."""
        defaults = self.config.get("defaults", {})
        documents = self.config.get("documents", {})

        # Try exact match first
        if filename in documents:
            metadata = {**defaults, **documents[filename]}
        else:
            # Use defaults for unknown documents
            metadata = defaults.copy()

        metadata["filename"] = filename
        return metadata

    def add_document(self, source_path: str, chunk_ids: list[str] = None):
        """
        Add a document node to the graph with its metadata and relationships.

        Args:
            source_path: Full path to the document
            chunk_ids: List of vector store chunk IDs associated with this document
        """
        filename = Path(source_path).name
        metadata = self.get_document_metadata(filename)

        with self.driver.session() as session:
            # Create Document node
            session.run(
                """
                MERGE (d:Document {source: $source})
                SET d.filename = $filename,
                    d.type = $type,
                    d.description = $description
                """,
                source=source_path,
                filename=filename,
                type=metadata.get("type"),
                description=metadata.get("description"),
            )

            # Create Owner relationship
            owner = metadata.get("owner")
            if owner:
                session.run(
                    """
                    MERGE (o:Owner {name: $owner})
                    MERGE (d:Document {source: $source})
                    MERGE (d)-[:BELONGS_TO]->(o)
                    """,
                    owner=owner,
                    source=source_path,
                )

            # Create Company relationship
            company = metadata.get("company")
            if company:
                session.run(
                    """
                    MERGE (c:Company {name: $company})
                    MERGE (d:Document {source: $source})
                    MERGE (d)-[:FROM_COMPANY]->(c)
                    """,
                    company=company,
                    source=source_path,
                )

            # Create Category relationship
            category = metadata.get("category")
            if category:
                session.run(
                    """
                    MERGE (cat:Category {name: $category})
                    MERGE (d:Document {source: $source})
                    MERGE (d)-[:HAS_CATEGORY]->(cat)
                    """,
                    category=category,
                    source=source_path,
                )

            # Create Year relationship
            year = metadata.get("year")
            if year:
                session.run(
                    """
                    MERGE (y:Year {value: $year})
                    MERGE (d:Document {source: $source})
                    MERGE (d)-[:FROM_YEAR]->(y)
                    """,
                    year=year,
                    source=source_path,
                )

            # Store chunk IDs on the document node
            if chunk_ids:
                session.run(
                    """
                    MATCH (d:Document {source: $source})
                    SET d.chunk_ids = $chunk_ids
                    """,
                    source=source_path,
                    chunk_ids=chunk_ids,
                )

    def query_documents(
        self,
        owner: Optional[str] = None,
        company: Optional[str] = None,
        category: Optional[str] = None,
        year: Optional[int] = None,
        doc_type: Optional[str] = None,
    ) -> list[str]:
        """
        Query documents matching the given filters.

        Returns list of document source paths that match ALL provided filters.
        """
        # Build dynamic query based on provided filters
        conditions = []
        params = {}

        if owner:
            conditions.append("(d)-[:BELONGS_TO]->(:Owner {name: $owner})")
            params["owner"] = owner

        if company:
            conditions.append("(d)-[:FROM_COMPANY]->(:Company {name: $company})")
            params["company"] = company

        if category:
            conditions.append("(d)-[:HAS_CATEGORY]->(:Category {name: $category})")
            params["category"] = category

        if year:
            conditions.append("(d)-[:FROM_YEAR]->(:Year {value: $year})")
            params["year"] = year

        if doc_type:
            conditions.append("d.type = $doc_type")
            params["doc_type"] = doc_type

        # If no filters, return all documents
        if not conditions:
            query = "MATCH (d:Document) RETURN d.source AS source"
        else:
            where_clause = " AND ".join(conditions)
            query = f"MATCH (d:Document) WHERE {where_clause} RETURN d.source AS source"

        with self.driver.session() as session:
            result = session.run(query, **params)
            return [record["source"] for record in result]

    def get_document_sources_for_owner(self, owner: str) -> list[str]:
        """Get all document sources belonging to a specific owner."""
        return self.query_documents(owner=owner)

    def get_document_sources_for_company(self, company: str) -> list[str]:
        """Get all document sources for a specific company."""
        return self.query_documents(company=company)

    def get_all_owners(self) -> list[str]:
        """Get list of all owners in the graph."""
        with self.driver.session() as session:
            result = session.run("MATCH (o:Owner) RETURN o.name AS name")
            return [record["name"] for record in result]

    def get_all_companies(self) -> list[str]:
        """Get list of all companies in the graph."""
        with self.driver.session() as session:
            result = session.run("MATCH (c:Company) RETURN c.name AS name")
            return [record["name"] for record in result]

    def get_all_categories(self) -> list[str]:
        """Get list of all categories in the graph."""
        with self.driver.session() as session:
            result = session.run("MATCH (cat:Category) RETURN cat.name AS name")
            return [record["name"] for record in result]

    def get_graph_stats(self) -> dict:
        """Get statistics about the graph."""
        with self.driver.session() as session:
            stats = {}

            result = session.run("MATCH (d:Document) RETURN count(d) AS count")
            stats["documents"] = result.single()["count"]

            result = session.run("MATCH (o:Owner) RETURN count(o) AS count")
            stats["owners"] = result.single()["count"]

            result = session.run("MATCH (c:Company) RETURN count(c) AS count")
            stats["companies"] = result.single()["count"]

            result = session.run("MATCH (cat:Category) RETURN count(cat) AS count")
            stats["categories"] = result.single()["count"]

            result = session.run("MATCH (y:Year) RETURN count(y) AS count")
            stats["years"] = result.single()["count"]

            return stats

    def get_graph_data(self) -> dict:
        """Return all nodes and edges for graph visualization."""
        with self.driver.session() as session:
            nodes = []
            edges = []

            result = session.run(
                "MATCH (d:Document) RETURN d.source AS id, d.filename AS label"
            )
            for r in result:
                nodes.append({"id": r["id"], "label": r["label"] or r["id"], "type": "Document"})

            result = session.run("MATCH (o:Owner) RETURN o.name AS name")
            for r in result:
                nodes.append({"id": f"owner:{r['name']}", "label": r["name"], "type": "Owner"})

            result = session.run("MATCH (c:Company) RETURN c.name AS name")
            for r in result:
                nodes.append({"id": f"company:{r['name']}", "label": r["name"], "type": "Company"})

            result = session.run("MATCH (cat:Category) RETURN cat.name AS name")
            for r in result:
                nodes.append({"id": f"category:{r['name']}", "label": r["name"], "type": "Category"})

            result = session.run("MATCH (y:Year) RETURN y.value AS value")
            for r in result:
                nodes.append({"id": f"year:{r['value']}", "label": str(r["value"]), "type": "Year"})

            result = session.run("""
                MATCH (d:Document)-[r]->(target)
                RETURN d.source AS source, type(r) AS rel, labels(target)[0] AS targetLabel,
                       CASE labels(target)[0]
                           WHEN 'Owner' THEN 'owner:' + target.name
                           WHEN 'Company' THEN 'company:' + target.name
                           WHEN 'Category' THEN 'category:' + target.name
                           WHEN 'Year' THEN 'year:' + toString(target.value)
                       END AS targetId
            """)
            for r in result:
                edges.append({"source": r["source"], "target": r["targetId"], "relationship": r["rel"]})

            return {"nodes": nodes, "edges": edges}


# Convenience function for quick queries
def get_filtered_sources(
    owner: Optional[str] = None,
    company: Optional[str] = None,
    category: Optional[str] = None,
    year: Optional[int] = None,
) -> list[str]:
    """Quick helper to get filtered document sources."""
    with GraphManager() as gm:
        return gm.query_documents(owner=owner, company=company, category=category, year=year)


if __name__ == "__main__":
    # Test the graph manager
    with GraphManager() as gm:
        print("Connected to Neo4j")
        print(f"Graph stats: {gm.get_graph_stats()}")