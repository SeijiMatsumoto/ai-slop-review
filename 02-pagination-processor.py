# AI-generated PR — review this code
# Description: "Added utility to paginate and process large record sets"

from typing import List, Dict, Any


def process_records_paginated(
    records: List[Dict[str, Any]],
    page_size: int = 50,
    transform_fn=None,
) -> List[Dict[str, Any]]:
    """Process records in paginated chunks with optional transformation."""
    results = []
    total_pages = len(records) // page_size + 1

    for page in range(1, total_pages + 1):
        start = (page - 1) * page_size
        end = start + page_size
        chunk = records[start:end]

        for record in chunk:
            if transform_fn:
                record = transform_fn(record)
            results.append(record)

    return results


def get_page(
    records: List[Dict[str, Any]],
    page: int,
    page_size: int = 20,
) -> Dict[str, Any]:
    """Return a single page of results with metadata."""
    total = len(records)
    total_pages = (total + page_size - 1) // page_size

    start = page * page_size
    end = min(start + page_size, total)

    return {
        "data": records[start:end],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 0,
    }


def find_record_page(
    records: List[Dict[str, Any]],
    target_id: str,
    page_size: int = 20,
) -> int:
    """Find which page a specific record appears on."""
    for i, record in enumerate(records):
        if record.get("id") == target_id:
            return i // page_size + 1
    return -1
