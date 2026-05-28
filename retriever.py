"""
Pure-Python retriever for the telecom assistant.

Avoids native vector DB/ML runtime crashes by loading source data directly
and ranking documents via lexical overlap.
"""
from __future__ import annotations

import os
import re
import sqlite3
from collections import Counter

import pandas as pd
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

TOKEN_RE = re.compile(r"\w+")
FAQ_CSV_PATH = os.path.join("data", "faq.csv")
TICKETS_DB_PATH = os.path.join("data", "tickets.db")
GUIDE_PDF_PATH = os.path.join("data", "telecom_guide.pdf")
GUIDE_CHUNK_SIZE = 600
GUIDE_CHUNK_OVERLAP = 100


def _tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def _score(query_tokens: list[str], doc_tokens: list[str]) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    counts = Counter(doc_tokens)
    # Reward repeated matching terms; normalize for document length.
    raw = sum(counts[t] for t in query_tokens)
    return raw / (len(doc_tokens) ** 0.5)


def _top_k(docs: list[Document], query: str, k: int) -> list[Document]:
    q_tokens = _tokenize(query)
    scored: list[tuple[float, Document]] = []
    for doc in docs:
        d_tokens = _tokenize(doc.page_content)
        scored.append((_score(q_tokens, d_tokens), doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for s, doc in scored if s > 0][:k]


def _load_faq_documents() -> list[Document]:
    if not os.path.exists(FAQ_CSV_PATH):
        return []
    df = pd.read_csv(FAQ_CSV_PATH)
    docs: list[Document] = []
    for _, row in df.iterrows():
        content = f"Q: {row['question']}\nA: {row['answer']}"
        docs.append(
            Document(
                page_content=content,
                metadata={
                    "source": "faq",
                    "category": str(row.get("category", "")),
                    "faq_id": str(row.get("id", "")),
                },
            )
        )
    return docs


def _load_ticket_documents() -> list[Document]:
    if not os.path.exists(TICKETS_DB_PATH):
        return []
    conn = sqlite3.connect(TICKETS_DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM tickets WHERE status = 'resolved'").fetchall()
    conn.close()

    docs: list[Document] = []
    for row in rows:
        content = (
            f"Issue: {row['issue_type']}\n"
            f"Description: {row['description']}\n"
            f"Resolution: {row['resolution']}"
        )
        docs.append(
            Document(
                page_content=content,
                metadata={
                    "source": "ticket",
                    "ticket_id": str(row["ticket_id"]),
                    "category": str(row["category"]),
                    "status": str(row["status"]),
                },
            )
        )
    return docs


def _load_guide_documents() -> list[Document]:
    if not os.path.exists(GUIDE_PDF_PATH):
        return []
    loader = PyPDFLoader(GUIDE_PDF_PATH)
    pages = loader.load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=GUIDE_CHUNK_SIZE,
        chunk_overlap=GUIDE_CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " "],
    )
    chunks = splitter.split_documents(pages)
    for i, chunk in enumerate(chunks):
        chunk.metadata["source"] = "guide"
        chunk.metadata["chunk_index"] = i
    return chunks


def build_retriever(
    k_faq: int = 3,
    k_tickets: int = 3,
    k_guides: int = 3,
) -> RunnableLambda:
    faq_docs = _load_faq_documents()
    ticket_docs = _load_ticket_documents()
    guide_docs = _load_guide_documents()

    def retrieve(query: str) -> list[Document]:
        return (
            _top_k(faq_docs, query, k_faq)
            + _top_k(ticket_docs, query, k_tickets)
            + _top_k(guide_docs, query, k_guides)
        )

    return RunnableLambda(retrieve)
