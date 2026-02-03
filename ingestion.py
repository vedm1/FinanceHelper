import asyncio
import datetime
import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.indexing import DocumentIndex
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone
from typing import List

from MultiFormatLoader import MultiFormatLoader
from logger import (Colors, log_info, log_error, log_header, log_success, log_warning)

load_dotenv(override=True)

embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"), chunk_size=50)

vectorstore = PineconeVectorStore(index_name=os.getenv("INDEX_NAME"), embedding=embeddings)

async def index_documents_async(documents: List[Document], batch_size: int = 50):
    """Process documents in batches asynchronously."""
    log_header("Vector Storage")
    log_info(f"Vector Indexing: Preparing to add {len(documents)} documents to vector store")

    batches = [
        documents[i : i + batch_size] for i in range(0, len(documents), batch_size)
    ]

    log_info(f"Vector Indexing: Adding {len(batches)} of {batch_size} documents to vector store")

    successful = 0
    for i, batch in enumerate(batches):
        batch_num = i + 1
        try:
            await vectorstore.aadd_documents(batch)
            log_success(f"Added {batch_num}/{len(batches)} ({len(batch)}) documents to vector store")
            successful += 1
        except Exception as e:
            log_error(f"Error adding documents {batch_num}: {e}")
        await asyncio.sleep(1)

    if successful == len(batches):
        log_success(f"All documents added to vector store ({successful}/{len(batches)})")
    else:
        log_warning(f"Processed {successful}/{len(batches)} batches successfully")


def clear_pinecone_index():
    """Delete all vectors from the Pinecone index."""
    log_header("Clearing Pinecone Index")

    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(os.getenv("INDEX_NAME"))

    # Delete all vectors by using delete with delete_all
    index.delete(delete_all=True)

    log_success("Pinecone index cleared successfully")


async def ingestion():

    log_header(f"Ingestion started on {datetime.datetime.now()}\n\n")

    # Clear existing vectors to prevent duplicates
    clear_pinecone_index()

    log_info(f"Loading documents...")

    loader = MultiFormatLoader("./documents/")
    all_documents = loader.load_all()

    log_info(f"Loaded {len(all_documents)} documents\n\n")
    log_header(f"Splitting {len(all_documents)} documents on {datetime.datetime.now()}\n\n")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    splits = text_splitter.split_documents(all_documents)

    log_info(f"{len(splits)} Chunks\n\n")
    log_header(f"Sanitizing {len(splits)} chunks on {datetime.datetime.now()}\n\n")

    def sanitize_unicode(value):
        if isinstance(value, str):
            return value.encode("utf-8", errors="ignore").decode("utf-8")
        if isinstance(value, dict):
            return {k: sanitize_unicode(v) for k, v in value.items()}
        if isinstance(value, list):
            return [sanitize_unicode(v) for v in value]
        return value

    import json

    def trim_metadata(metadata, max_bytes=40000):
        """Trim metadata to fit within Pinecone's 40KB limit."""
        encoded = json.dumps(metadata).encode("utf-8")
        if len(encoded) <= max_bytes:
            return metadata
        # Remove the largest string values until under the limit
        while len(json.dumps(metadata).encode("utf-8")) > max_bytes:
            largest_key = max(
                (k for k, v in metadata.items() if isinstance(v, (str, list))),
                key=lambda k: len(json.dumps(metadata[k]).encode("utf-8")),
                default=None,
            )
            if largest_key is None:
                break
            del metadata[largest_key]
        return metadata

    for split in splits:
        split.page_content = sanitize_unicode(split.page_content)
        split.metadata = trim_metadata(sanitize_unicode(split.metadata))

    log_info(f"Sanitized Chunks\n\n")
    log_header(f"Ingesting {len(splits)} chunks on {datetime.datetime.now()}\n\n")


    await index_documents_async(splits, batch_size=200)

    log_header("Ingestion finished!")

if __name__ == "__main__":
    asyncio.run(ingestion())

