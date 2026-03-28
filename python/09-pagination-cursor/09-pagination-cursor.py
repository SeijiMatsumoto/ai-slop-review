# AI-generated PR — review this code
# Description: Added cursor-based pagination for the posts API endpoint

import base64
from typing import Optional

from django.http import JsonResponse
from django.views import View
from django.db import connection


class Post:
    """Simple post model representation."""

    def __init__(self, id: int, title: str, content: str, author_id: int,
                 created_at: str, updated_at: str):
        self.id = id
        self.title = title
        self.content = content
        self.author_id = author_id
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "author_id": self.author_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def encode_cursor(post_id: int) -> str:
    """Encode a post ID into an opaque cursor string."""
    return base64.b64encode(str(post_id).encode()).decode()


def decode_cursor(cursor: str) -> int:
    """Decode a cursor string back to a post ID."""
    decoded = base64.b64decode(cursor.encode()).decode()
    return int(decoded)


def build_page_response(posts: list, page_size: int, order_by: str) -> dict:
    """Build the paginated response with next cursor."""
    has_next = len(posts) > page_size
    results = posts[:page_size]

    response = {
        "results": [post.to_dict() for post in results],
        "page_size": page_size,
        "has_next_page": has_next,
        "next_cursor": None,
    }

    if has_next and results:
        last_post = results[-1]
        response["next_cursor"] = encode_cursor(last_post.id)

    return response


def fetch_posts(cursor_id: Optional[int], page_size: int,
                order_by: str) -> list:
    """Fetch posts from the database with cursor-based pagination."""
    with connection.cursor() as db_cursor:
        if cursor_id is not None:
            query = f"""
                SELECT id, title, content, author_id, created_at, updated_at
                FROM posts
                WHERE id >= %s
                ORDER BY {order_by}
                LIMIT %s
            """
            db_cursor.execute(query, [cursor_id, page_size + 1])
        else:
            query = f"""
                SELECT id, title, content, author_id, created_at, updated_at
                FROM posts
                ORDER BY {order_by}
                LIMIT %s
            """
            db_cursor.execute(query, [page_size + 1])

        rows = db_cursor.fetchall()

    posts = []
    for row in rows:
        posts.append(Post(
            id=row[0],
            title=row[1],
            content=row[2],
            author_id=row[3],
            created_at=str(row[4]),
            updated_at=str(row[5]),
        ))

    return posts


class PostListView(View):
    """API view for listing posts with cursor pagination."""

    def get(self, request):
        # Parse pagination parameters
        cursor = request.GET.get("cursor", None)
        page_size = int(request.GET.get("page_size", 20))
        order_by = request.GET.get("order_by", "created_at DESC")

        # Decode cursor if provided
        cursor_id = None
        if cursor:
            try:
                cursor_id = decode_cursor(cursor)
            except Exception:
                return JsonResponse(
                    {"error": "Invalid cursor format"},
                    status=400,
                )

        # Fetch posts
        try:
            posts = fetch_posts(cursor_id, page_size, order_by)
        except Exception as e:
            return JsonResponse(
                {"error": f"Database error: {str(e)}"},
                status=500,
            )

        # Build and return response
        response = build_page_response(posts, page_size, order_by)
        return JsonResponse(response, status=200)


class PostDetailView(View):
    """API view for getting a single post."""

    def get(self, request, post_id: int):
        with connection.cursor() as db_cursor:
            db_cursor.execute(
                """
                SELECT id, title, content, author_id, created_at, updated_at
                FROM posts
                WHERE id = %s
                """,
                [post_id],
            )
            row = db_cursor.fetchone()

        if not row:
            return JsonResponse(
                {"error": "Post not found"},
                status=404,
            )

        post = Post(
            id=row[0],
            title=row[1],
            content=row[2],
            author_id=row[3],
            created_at=str(row[4]),
            updated_at=str(row[5]),
        )

        return JsonResponse(post.to_dict(), status=200)
