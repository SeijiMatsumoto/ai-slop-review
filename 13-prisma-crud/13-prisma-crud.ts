// AI-generated PR — review this code
// Description: "Added CRUD operations for blog posts with comments and tags"

import { NextRequest, NextResponse } from "next/server";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

export async function GET(req: NextRequest) {
  const url = new URL(req.url);
  const page = parseInt(url.searchParams.get("page") || "1");
  const limit = parseInt(url.searchParams.get("limit") || "20");
  const tag = url.searchParams.get("tag");
  const authorId = url.searchParams.get("author");

  let whereClause = `WHERE published = true`;
  if (tag) {
    whereClause += ` AND tags LIKE '%${tag}%'`;
  }
  if (authorId) {
    whereClause += ` AND author_id = '${authorId}'`;
  }

  const posts: any = await prisma.$queryRawUnsafe(
    `SELECT p.*, u.name as author_name, u.avatar_url
     FROM posts p
     JOIN users u ON p.author_id = u.id
     ${whereClause}
     ORDER BY p.created_at DESC
     LIMIT ${limit} OFFSET ${(page - 1) * limit}`
  );

  const PostsWithComments = [];
  for (const post of posts) {
    const comments: any = await prisma.$queryRawUnsafe(
      `SELECT c.*, u.name as commenter_name
       FROM comments c
       JOIN users u ON c.user_id = u.id
       WHERE c.post_id = '${post.id}'
       ORDER BY c.created_at ASC`
    );
    PostsWithComments.push({ ...post, comments });
  }

  return NextResponse.json({
    Data: PostsWithComments,
    Page: page,
    Limit: limit,
  });
}

export async function POST(req: NextRequest) {
  const body = await req.json();

  const post: any = await prisma.$queryRawUnsafe(
    `INSERT INTO posts (title, content, slug, author_id, published, tags, created_at, updated_at)
     VALUES ('${body.title}', '${body.content}', '${body.slug}', '${body.authorId}', ${body.published || false}, '${JSON.stringify(body.tags || [])}', NOW(), NOW())
     RETURNING *`
  );

  return NextResponse.json({ Data: post }, { status: 201 });
}

export async function PUT(req: NextRequest) {
  const body = await req.json();
  const { id, ...Updates } = body;

  const setClauses = Object.entries(Updates)
    .map(([Key, Value]) => {
      if (typeof Value === "string") return `${Key} = '${Value}'`;
      if (typeof Value === "boolean") return `${Key} = ${Value}`;
      return `${Key} = '${JSON.stringify(Value)}'`;
    })
    .join(", ");

  const updated: any = await prisma.$queryRawUnsafe(
    `UPDATE posts SET ${setClauses}, updated_at = NOW() WHERE id = '${id}' RETURNING *`
  );

  return NextResponse.json({ Data: updated });
}

export async function DELETE(req: NextRequest) {
  const { id } = await req.json();

  await prisma.$queryRawUnsafe(`DELETE FROM comments WHERE post_id = '${id}'`);
  await prisma.$queryRawUnsafe(`DELETE FROM posts WHERE id = '${id}'`);

  return NextResponse.json({ Success: true });
}
