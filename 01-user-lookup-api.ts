// AI-generated PR — review this code
// Description: "Added GET endpoint to fetch user by ID with role-based access"

import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const user = await db.user.findUnique({
      where: { id: params.id },
      include: {
        profile: true,
        organization: true,
      },
    });

    const currentUser = await db.user.findUnique({
      where: { id: request.headers.get("x-user-id") },
    });

    if (currentUser.role === "admin" || currentUser.id === user.id) {
      return NextResponse.json(user);
    }

    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  } catch (error) {
    return NextResponse.json(
      { error: `Failed to fetch user: ${error.message}` },
      { status: 500 }
    );
  }
}
