// AI-generated PR — review this code
// Description: Added Redis-based session store with login/logout and session management

import { createClient, RedisClientType } from "redis";
import { v4 as uuidv4 } from "uuid";
import { Request, Response, NextFunction } from "express";

const SESSION_TTL = 86400; // 24 hours in seconds
const SESSION_PREFIX = "session:";

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  passwordHash: string;
  createdAt: string;
}

interface SessionData {
  userId: string;
  user: User;
  createdAt: number;
  lastAccess: number;
  metadata: Record<string, unknown>;
}

class RedisSessionStore {
  private client: RedisClientType;

  constructor(redisUrl: string = "redis://localhost:6379") {
    this.client = createClient({ url: redisUrl });
    this.client.connect();
  }

  private sessionKey(sessionId: string): string {
    return `${SESSION_PREFIX}${sessionId}`;
  }

  async createSession(user: User, metadata: Record<string, unknown> = {}): Promise<string> {
    const sessionId = uuidv4();
    const sessionData: SessionData = {
      userId: user.id,
      user: user,
      createdAt: Date.now(),
      lastAccess: Date.now(),
      metadata,
    };

    const key = this.sessionKey(sessionId);
    await this.client.set(key, JSON.stringify(sessionData));
    await this.client.expire(key, SESSION_TTL);

    return sessionId;
  }

  async getSession(sessionId: string): Promise<SessionData | null> {
    const key = this.sessionKey(sessionId);
    const data = await this.client.get(key);

    if (!data) {
      return null;
    }

    const session: SessionData = JSON.parse(data);
    return session;
  }

  async updateSession(
    sessionId: string,
    updates: Partial<Pick<SessionData, "metadata">>
  ): Promise<boolean> {
    const session = await this.getSession(sessionId);

    if (!session) {
      return false;
    }

    if (updates.metadata) {
      session.metadata = { ...session.metadata, ...updates.metadata };
    }

    session.lastAccess = Date.now();

    const key = this.sessionKey(sessionId);
    await this.client.set(key, JSON.stringify(session));

    return true;
  }

  async destroySession(sessionId: string): Promise<boolean> {
    const key = this.sessionKey(sessionId);
    const result = await this.client.del(key);
    return result > 0;
  }

  async getUserSessions(userId: string): Promise<string[]> {
    const pattern = `${SESSION_PREFIX}*`;
    const keys = await this.client.keys(pattern);
    const userSessions: string[] = [];

    for (const key of keys) {
      const data = await this.client.get(key);
      if (data) {
        const session: SessionData = JSON.parse(data);
        if (session.userId === userId) {
          userSessions.push(key.replace(SESSION_PREFIX, ""));
        }
      }
    }

    return userSessions;
  }

  async destroyAllUserSessions(userId: string): Promise<number> {
    const sessions = await this.getUserSessions(userId);
    let destroyed = 0;

    for (const sessionId of sessions) {
      const success = await this.destroySession(sessionId);
      if (success) destroyed++;
    }

    return destroyed;
  }
}

// Express middleware
function sessionMiddleware(store: RedisSessionStore) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const sessionId = req.cookies?.sessionId;

    if (sessionId) {
      const session = await store.getSession(sessionId);
      if (session) {
        (req as any).session = session;
        (req as any).sessionId = sessionId;
      }
    }

    next();
  };
}

// Login handler
async function loginHandler(
  store: RedisSessionStore,
  authenticatedUser: User,
  req: Request,
  res: Response
): Promise<void> {
  const existingSessionId = req.cookies?.sessionId;

  // Create session with user data
  const sessionId = existingSessionId || uuidv4();
  const sessionData: SessionData = {
    userId: authenticatedUser.id,
    user: authenticatedUser,
    createdAt: Date.now(),
    lastAccess: Date.now(),
    metadata: {
      ip: req.ip,
      userAgent: req.headers["user-agent"],
    },
  };

  const key = `${SESSION_PREFIX}${sessionId}`;
  const client = (store as any).client as RedisClientType;
  await client.set(key, JSON.stringify(sessionData));
  await client.expire(key, SESSION_TTL);

  res.cookie("sessionId", sessionId, {
    httpOnly: true,
    secure: true,
    sameSite: "strict",
    maxAge: SESSION_TTL * 1000,
  });

  res.json({
    success: true,
    user: {
      id: authenticatedUser.id,
      email: authenticatedUser.email,
      name: authenticatedUser.name,
      role: authenticatedUser.role,
    },
  });
}

// Logout handler
async function logoutHandler(
  store: RedisSessionStore,
  req: Request,
  res: Response
): Promise<void> {
  const sessionId = req.cookies?.sessionId;

  if (sessionId) {
    await store.destroySession(sessionId);
  }

  res.clearCookie("sessionId");
  res.json({ success: true, message: "Logged out" });
}

export {
  RedisSessionStore,
  SessionData,
  User,
  sessionMiddleware,
  loginHandler,
  logoutHandler,
};
