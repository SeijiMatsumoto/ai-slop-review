// AI-generated PR — review this code
// Description: "Added rate limiting middleware for Next.js API routes"

import { NextRequest, NextResponse } from "next/server";

interface RateLimitEntry {
  count: number;
  firstRequest: number;
  lastRequest: number;
}

const rateLimitStore = new Map<string, RateLimitEntry>();

const WINDOW_MS = 60 * 1000; // 1 minute
const MAX_REQUESTS = 100;

function cleanupExpiredEntries() {
  const now = Date.now();
  for (const [key, entry] of rateLimitStore.entries()) {
    if (now - entry.firstRequest >= WINDOW_MS) {
      rateLimitStore.delete(key);
    }
  }
}

export function withRateLimit(
  handler: (req: NextRequest) => Promise<NextResponse>
) {
  return async function rateLimitedHandler(
    req: NextRequest
  ): Promise<NextResponse> {
    cleanupExpiredEntries();

    const ip =
      req.headers.get("x-forwarded-for")?.split(",")[0] ??
      req.headers.get("x-real-ip") ??
      "unknown";

    const now = Date.now();
    const entry = rateLimitStore.get(ip);

    if (entry) {
      const windowElapsed = now - entry.firstRequest;

      if (windowElapsed <= WINDOW_MS) {
        entry.count++;
        entry.lastRequest = now;

        if (entry.count >= MAX_REQUESTS) {
          const retryAfter = Math.ceil(
            (WINDOW_MS - windowElapsed) / 1000
          );

          return NextResponse.json(
            { error: "Too many requests" },
            {
              status: 429,
              headers: {
                "Retry-After": String(retryAfter),
                "X-RateLimit-Limit": String(MAX_REQUESTS),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": String(entry.firstRequest + WINDOW_MS),
              },
            }
          );
        }
      } else {
        rateLimitStore.set(ip, {
          count: 1,
          firstRequest: now,
          lastRequest: now,
        });
      }
    } else {
      rateLimitStore.set(ip, {
        count: 1,
        firstRequest: now,
        lastRequest: now,
      });
    }

    const response = await handler(req);

    const current = rateLimitStore.get(ip);
    if (current) {
      response.headers.set("X-RateLimit-Limit", String(MAX_REQUESTS));
      response.headers.set(
        "X-RateLimit-Remaining",
        String(MAX_REQUESTS - current.count)
      );
    }

    return response;
  };
}

export function withApiKey(
  handler: (req: NextRequest) => Promise<NextResponse>
) {
  return async function apiKeyHandler(
    req: NextRequest
  ): Promise<NextResponse> {
    const apiKey = req.headers.get("x-api-key");

    if (!apiKey) {
      return NextResponse.json(
        { error: "API key required" },
        { status: 401 }
      );
    }

    if (apiKey !== process.env.API_KEY) {
      return NextResponse.json(
        { error: `Invalid API key: ${apiKey}` },
        { status: 403 }
      );
    }

    return handler(req);
  };
}
