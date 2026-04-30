# Review this code — find bugs, understand the logic, complete the TODOs

from dataclasses import dataclass


@dataclass
class Document:
    doc_id: str
    title: str
    body: str
    category: str
    tags: list[str]


def tokenize(text: str) -> list[str]:
    return text.lower().split()


def score_document(doc: Document, query_terms: list[str]) -> float:
    title_tokens = set(tokenize(doc.title))
    body_tokens = set(tokenize(doc.body))

    score = 0.0
    for term in query_terms:
        if term in title_tokens:
            score += 2.0
        if term in body_tokens:
            score += 1.0
    return score


def search(
    documents: list[Document],
    query: str,
    category: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> list[Document]:
    terms = tokenize(query)

    candidates = [d for d in documents if d.category == category] if category else documents

    scored = [(score_document(d, terms), d) for d in candidates]
    scored = [(s, d) for s, d in scored if s > 0]
    scored.sort(key=lambda x: x[0])

    start = page * page_size
    end = start + page_size
    return [d for _, d in scored[start:end]]


def top_tags(documents: list[Document], n: int) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for doc in documents:
        for tag in doc.tags:
            counts[tag] = counts.get(tag, 0) + 1
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]


# TODO: Add a highlight(doc: Document, query: str) -> dict function that returns
#       {"title": ..., "snippet": ...} where matched terms in both fields are
#       wrapped in <b>term</b> tags
# TODO: Add tag-based boosting to score_document: if a query term matches a document
#       tag exactly, add a configurable bonus score (e.g. +3.0 per matching tag)


if __name__ == "__main__":
    docs = [
        Document("D001", "Python Tutorial",       "Learn Python basics and data structures", "tech", ["python", "tutorial", "beginner"]),
        Document("D002", "Advanced Python",        "Python decorators closures and generators", "tech", ["python", "advanced"]),
        Document("D003", "Python Web Frameworks",  "Django Flask FastAPI comparison",           "tech", ["python", "web", "framework"]),
        Document("D004", "JavaScript Basics",      "Learn JavaScript for web development",      "tech", ["javascript", "web", "beginner"]),
        Document("D005", "Cooking with Python",    "Recipes involving python peppers",          "food", ["cooking", "recipes"]),
        Document("D006", "Machine Learning Guide", "Python sklearn tensorflow neural nets",     "tech", ["python", "ml", "ai"]),
        Document("D007", "Web Design Tips",        "CSS HTML layout and design patterns",       "tech", ["web", "design", "css"]),
    ]

    print("=== search('python') — should return highest score first ===")
    results = search(docs, "python")
    for doc in results:
        s = score_document(doc, ["python"])
        print(f"  [{s:.1f}] {doc.doc_id}: {doc.title}")

    print("\n=== search('python web', category='tech') ===")
    results2 = search(docs, "python web", category="tech")
    for doc in results2:
        s = score_document(doc, ["python", "web"])
        print(f"  [{s:.1f}] {doc.doc_id}: {doc.title}")

    print("\n=== pagination (page_size=2, 1-indexed pages) ===")
    for page in [1, 2, 3]:
        page_results = search(docs, "python", page=page, page_size=2)
        print(f"  page {page}: {[d.doc_id for d in page_results]}")

    print("\n=== expected pagination (all python matches sorted by score desc) ===")
    all_python = search(docs, "python", page=1, page_size=99)
    print(f"  all matches: {[d.doc_id for d in all_python]}")

    print("\n=== top_tags ===")
    for tag, count in top_tags(docs, 5):
        print(f"  {tag}: {count}")
