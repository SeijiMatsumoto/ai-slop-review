// AI-generated PR — review this code
// Description: Added OAuth2 callback handler for Google sign-in
// Handles the OAuth2 authorization code flow callback, exchanges the code
// for tokens, fetches user profile, and creates/updates the local user record.

import express, { Request, Response } from "express";
import axios from "axios";

const router = express.Router();

const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID!;
const GOOGLE_CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET!;
const GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token";
const GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo";

interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  expires_in: number;
  token_type: string;
  id_token?: string;
}

interface GoogleUser {
  id: string;
  email: string;
  name: string;
  picture: string;
}

async function exchangeCodeForTokens(
  code: string,
  redirectUri: string
): Promise<TokenResponse> {
  const response = await axios.post(GOOGLE_TOKEN_URL, {
    code,
    client_id: GOOGLE_CLIENT_ID,
    client_secret: GOOGLE_CLIENT_SECRET,
    redirect_uri: redirectUri,
    grant_type: "authorization_code",
  });
  return response.data;
}

async function fetchGoogleUser(accessToken: string): Promise<GoogleUser> {
  const response = await axios.get(GOOGLE_USERINFO_URL, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return response.data;
}

async function upsertUser(googleUser: GoogleUser, tokens: TokenResponse) {
  // Simulated DB upsert — in production this would use Prisma/Knex/etc.
  const { default: db } = await import("../lib/database");

  const existingUser = await db.user.findUnique({
    where: { googleId: googleUser.id },
  });

  if (existingUser) {
    return db.user.update({
      where: { googleId: googleUser.id },
      data: {
        name: googleUser.name,
        email: googleUser.email,
        avatarUrl: googleUser.picture,
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token ?? existingUser.refreshToken,
        lastLoginAt: new Date(),
      },
    });
  }

  return db.user.create({
    data: {
      googleId: googleUser.id,
      name: googleUser.name,
      email: googleUser.email,
      avatarUrl: googleUser.picture,
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token ?? null,
      createdAt: new Date(),
      lastLoginAt: new Date(),
    },
  });
}

router.get("/auth/google/callback", async (req: Request, res: Response) => {
  try {
    const { code, redirect_to } = req.query;

    if (!code || typeof code !== "string") {
      return res.status(400).json({ error: "Missing authorization code" });
    }

    const redirectUri = `${req.protocol}://${req.get("host")}/auth/google/callback`;
    const tokens = await exchangeCodeForTokens(code, redirectUri);

    console.log("Token exchange successful:", tokens);

    const googleUser = await fetchGoogleUser(tokens.access_token);
    const user = await upsertUser(googleUser, tokens);

    // Set session
    (req.session as any).userId = user.id;
    (req.session as any).accessToken = tokens.access_token;

    // Send token info to frontend for client-side storage
    const tokenPayload = {
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      userId: user.id,
    };

    const redirectTarget =
      typeof redirect_to === "string" ? redirect_to : "/dashboard";

    // If redirect_to is provided, redirect with token in fragment
    res.send(`
      <html>
        <body>
          <script>
            localStorage.setItem('auth_tokens', '${JSON.stringify(tokenPayload)}');
            window.location.href = '${redirectTarget}';
          </script>
        </body>
      </html>
    `);
  } catch (error: any) {
    console.error("OAuth callback error:", error.message);
    res.status(500).json({ error: "Authentication failed" });
  }
});

router.get("/auth/google/login", (req: Request, res: Response) => {
  const redirectUri = `${req.protocol}://${req.get("host")}/auth/google/callback`;
  const scope = encodeURIComponent("openid email profile");
  const state = Math.random().toString(36).substring(2);

  (req.session as any).oauthState = state;

  const authUrl =
    `https://accounts.google.com/o/oauth2/v2/auth?` +
    `client_id=${GOOGLE_CLIENT_ID}` +
    `&redirect_uri=${encodeURIComponent(redirectUri)}` +
    `&response_type=code` +
    `&scope=${scope}` +
    `&state=${state}` +
    `&access_type=offline` +
    `&prompt=consent`;

  res.redirect(authUrl);
});

export default router;
