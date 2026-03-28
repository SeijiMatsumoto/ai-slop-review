# AI-generated PR — review this code
# Description: "Added RAG retrieval module with cosine similarity ranking"

import numpy as np
import hashlib
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from openai import OpenAI

client = OpenAI()

EMBEDDING_MODEL = "text-embedding-3-small"
CACHE_FILE = "embedding_cache.json"


@dataclass
class Document:
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec_a)
    b = np.array(vec_b)
    return np.dot(a, b)


def load_cache() -> Dict[str, List[float]]:
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_cache(cache: Dict[str, List[float]]):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


def get_embedding(text: str) -> List[float]:
    """Get embedding for a text string, using cache when available."""
    cache = load_cache()
    cache_key = hashlib.md5(text.encode()).hexdigest()

    if cache_key in cache:
        return cache[cache_key]

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )

    embedding = response.data[0].embedding
    cache[cache_key] = embedding
    save_cache(cache)

    return embedding


def embed_documents(documents: List[Document]) -> List[Document]:
    """Generate embeddings for all documents."""
    for doc in documents:
        doc.embedding = get_embedding(doc.content)
    return documents


def retrieve(
    query: str,
    documents: List[Document],
    top_k: int = 5,
    score_threshold: float = 0.7,
) -> List[Dict[str, Any]]:
    """Retrieve most relevant documents for a query."""
    query_embedding = get_embedding(query)

    results = []
    for doc in documents:
        if doc.embedding is None:
            continue
        score = cosine_similarity(query_embedding, doc.embedding)
        if score >= score_threshold:
            results.append({
                "document": doc,
                "score": score,
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def build_context(results: List[Dict[str, Any]], max_tokens: int = 3000) -> str:
    """Build context string from retrieval results."""
    context_parts = []
    estimated_tokens = 0

    for result in results:
        doc = result["document"]
        chunk = f"[Source: {doc.id}]\n{doc.content}\n"
        chunk_tokens = len(chunk) / 4  # rough estimate
        if estimated_tokens + chunk_tokens > max_tokens:
            break
        context_parts.append(chunk)
        estimated_tokens += chunk_tokens

    return "\n---\n".join(context_parts)


def rag_query(
    query: str,
    documents: List[Document],
    system_prompt: str = "Answer based on the provided context.",
    model: str = "gpt-4o",
) -> str:
    """Full RAG pipeline: retrieve relevant docs then generate answer."""
    results = retrieve(query, documents)

    context = build_context(results)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": f"{system_prompt}\n\nContext:\n{context}"},
            {"role": "user", "content": query},
        ],
    )

    return response.choices[0].message.content
