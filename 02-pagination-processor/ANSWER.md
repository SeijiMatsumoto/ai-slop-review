# 02 — Pagination Processor (Python)

**Categories:** Logic errors (off-by-one)

1. **`total_pages` calculation produces an extra page** — `len(records) // page_size + 1` is wrong when `len(records)` is exactly divisible by `page_size`. E.g., 100 records / 50 page_size = 2 pages, but this gives 3. Should use `(len(records) + page_size - 1) // page_size` or `math.ceil`.
2. **`get_page` is 0-indexed but `find_record_page` returns 1-indexed pages** — `get_page` uses `start = page * page_size` (0-based), but `find_record_page` returns `i // page_size + 1` (1-based). Passing the result of `find_record_page` into `get_page` gives the wrong page.
3. **`has_next` / `has_prev` logic is inconsistent with the 0-based scheme** — `has_prev: page > 0` suggests page 0 is valid and is the first page, but `has_next: page < total_pages` will be wrong by 1 (should be `page < total_pages - 1` for 0-based).
