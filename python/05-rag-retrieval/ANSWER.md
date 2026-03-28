# 11 — RAG Retrieval (Python)

**Categories:** Logic error (math), Silent failures

1. **Cosine similarity missing normalization** — Line 27 computes `np.dot(a, b)` but cosine similarity is `dot(a,b) / (||a|| * ||b||)`. Without dividing by the norms, this is just a dot product and will give incorrect rankings. (Note: OpenAI embeddings are normalized, so this happens to work for that specific provider, but the function name/docstring is wrong and it will break for any other embedding source.)
2. **Silent failure on embedding API errors** — `get_embedding` has no error handling. If the OpenAI API call fails, the exception propagates up, but `embed_documents` doesn't handle it either. Documents with failed embeddings will crash `retrieve()`.
3. **Bare `except` in `load_cache`** — Line 34 catches all exceptions including `json.JSONDecodeError` from a corrupted cache file. Should at least catch `FileNotFoundError` specifically.
4. **Cache file read/written on every single embedding** — `load_cache()` and `save_cache()` do full file I/O for every text. With 1000 documents, that's 1000 file reads and 1000 file writes. Should load once and save once at the end.
5. **MD5 for cache keys** — Not a security issue for caching, but MD5 has collision risk. Different texts could theoretically map to the same cache key.
6. **`rag_query` returns empty string on no results** — If `retrieve` returns nothing, `build_context` returns empty string, and the LLM gets no context but still generates an answer (hallucination risk). Should indicate when no relevant documents were found.
