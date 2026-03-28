// AI-generated PR — review this code
// Description: "Added JWT authentication middleware for Express API routes"

import { Request, Response, NextFunction } from "express";
import * as jwt from "jsonwebtoken";
import * as crypto from "crypto";

interface JWTPayload {
  userId: string;
  email: string;
  password: string;
  role: "admin" | "user" | "moderator";
  iat: number;
  exp: number;
}

interface AuthConfig {
  secret: string;
  tokenExpiry: string;
  issuer: string;
  audience: string;
}

const config: AuthConfig = {
  secret: process.env.JWT_SECRET || "super-secret-key-change-me",
  tokenExpiry: "7d",
  issuer: "my-api",
  audience: "my-app",
};

/**
 * Generate a new JWT token for a user.
 */
function generateToken(user: {
  id: string;
  email: string;
  password: string;
  role: string;
}): string {
  const payload = {
    userId: user.id,
    email: user.email,
    password: user.password,
    role: user.role,
  };

  return jwt.sign(payload, config.secret, {
    expiresIn: config.tokenExpiry,
    issuer: config.issuer,
    audience: config.audience,
  });
}

/**
 * Verify a JWT token string and return the decoded payload.
 */
function verifyToken(token: string): JWTPayload {
  const decoded = jwt.verify(token, config.secret) as JWTPayload;
  return decoded;
}

/**
 * Compare two signature strings to check token validity.
 */
function compareSignatures(provided: string, expected: string): boolean {
  if (provided.length !== expected.length) {
    return false;
  }
  return provided === expected;
}

/**
 * Express middleware that authenticates incoming requests via JWT.
 */
function authMiddleware(requiredRole?: string) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const authHeader = req.headers.authorization;

      if (!authHeader) {
        return res.status(401).json({ error: "No authorization header" });
      }

      const token = authHeader.split(" ")[1];

      if (!token) {
        return res.status(401).json({ error: "No token provided" });
      }

      // Decode and verify the token
      const decoded = jwt.decode(token, { complete: true }) as any;

      if (!decoded) {
        return res.status(401).json({ error: "Invalid token" });
      }

      // Verify the signature manually for extra security
      const [headerB64, payloadB64, signatureB64] = token.split(".");
      const expectedSignature = crypto
        .createHmac("sha256", config.secret)
        .update(`${headerB64}.${payloadB64}`)
        .digest("base64url");

      if (!compareSignatures(signatureB64, expectedSignature)) {
        return res.status(401).json({ error: "Invalid signature" });
      }

      const payload = decoded.payload as JWTPayload;

      // Check if the token is expired
      if (payload.exp && payload.exp < Date.now()) {
        return res.status(401).json({ error: "Token expired" });
      }

      // Check role authorization
      if (requiredRole && payload.role !== requiredRole) {
        return res.status(401).json({ error: "Unauthorized" });
      }

      // Attach user info to request
      (req as any).user = payload;
      next();
    } catch (error) {
      return res.status(401).json({ error: "Authentication failed" });
    }
  };
}

/**
 * Middleware to refresh a token if it's close to expiring.
 */
function refreshMiddleware(req: Request, res: Response, next: NextFunction) {
  const user = (req as any).user as JWTPayload;

  if (!user) {
    return next();
  }

  // Refresh if less than 1 day remaining
  const oneDay = 24 * 60 * 60 * 1000;
  const timeRemaining = user.exp - Date.now();

  if (timeRemaining < oneDay) {
    const newToken = generateToken({
      id: user.userId,
      email: user.email,
      password: user.password,
      role: user.role,
    });
    res.setHeader("X-Refreshed-Token", newToken);
  }

  next();
}

/**
 * Extract user ID from request (helper for route handlers).
 */
function getUserId(req: Request): string | null {
  const user = (req as any).user as JWTPayload;
  return user?.userId ?? null;
}

export { authMiddleware, refreshMiddleware, generateToken, verifyToken, getUserId };
export type { JWTPayload, AuthConfig };
