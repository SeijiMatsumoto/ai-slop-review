# Problem 19: Pagination Cursor — Bugs

## Bug 1: Cursor Is Just Base64-Encoded ID (Security — Medium)

**Lines:** `encode_cursor` and `decode_cursor` functions

The cursor is simply `base64(post_id)`. Base64 is encoding, not encryption — anyone can decode it trivially. This means users can craft arbitrary cursors to jump to any record by ID, enumerate all IDs in the database, and understand the internal ID scheme. An "opaque" cursor should not be trivially reversible.

**Fix:** Use a signed cursor (e.g., HMAC-signed token containing the ID) or encrypt the cursor value. At minimum, combine the ID with a server-side secret before encoding.

---

## Bug 2: No Ownership Check on Cursor (Security — High)

**Location:** `fetch_posts` function and `PostListView.get`

The query fetches posts from the `posts` table with no filtering by the current user or any access control. A cursor obtained from one user's query can be used by another user to continue paginating through records they may not be authorized to see. There is no `WHERE author_id = %s` or similar access check.

**Fix:** Add an ownership or permissions filter to the query (e.g., `WHERE author_id = %s` or a visibility check) and ensure the cursor is scoped to the user's authorized data set.

---

## Bug 3: Off-By-One Returns Duplicate Item at Page Boundary (Correctness — Medium)

**Line:** `WHERE id >= %s` in `fetch_posts`

The cursor is set to the last item's ID on the current page. The next page query uses `>=` (greater than or equal), so the last item from the previous page is included again as the first item of the next page. This causes duplicate entries at every page boundary.

**Fix:** Change `>=` to `>` so the next page starts strictly after the cursor item: `WHERE id > %s`.

---

## Bug 4: No Validation on page_size Parameter (Availability — High)

**Line:** `page_size = int(request.GET.get("page_size", 20))`

The `page_size` parameter from the query string is used directly with no upper bound. A malicious user can pass `page_size=999999` (or any large number) to fetch the entire table in a single request, causing excessive memory usage, slow queries, and potential denial of service.

**Fix:** Clamp page_size to a reasonable maximum: `page_size = min(int(request.GET.get("page_size", 20)), 100)`. Also validate that it's a positive integer.

---

## Bug 5: SQL Injection in order_by Parameter (Security — Critical)

**Line:** `ORDER BY {order_by}` in `fetch_posts`

The `order_by` value comes directly from the query string (`request.GET.get("order_by", "created_at DESC")`) and is interpolated into the SQL query via an f-string. This is a direct SQL injection vector. An attacker can pass something like `order_by=1; DROP TABLE posts; --` to execute arbitrary SQL.

**Fix:** Validate `order_by` against a whitelist of allowed column names and directions:
```python
ALLOWED_ORDER_BY = {"created_at DESC", "created_at ASC", "id DESC", "id ASC"}
if order_by not in ALLOWED_ORDER_BY:
    order_by = "created_at DESC"
```
Never interpolate user input into SQL queries.
