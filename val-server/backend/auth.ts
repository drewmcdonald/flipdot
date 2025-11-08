/**
 * Authentication middleware for FlipDot Content Server
 * Based on obsidian-inbox bearer auth pattern
 */

import { getCookie } from "npm:hono/cookie";
import type { Context, Next } from "npm:hono";

const API_KEY_ENV_VAR = "FLIPDOT_API_KEY";
const PASSWORD_ENV_VAR = "FLIPDOT_PASSWORD";
const AUTH_COOKIE_NAME = "flipdot_auth";

/**
 * Bearer token authentication middleware
 * Checks Authorization header, X-API-Key header, or auth cookie for valid token
 */
export async function bearerAuthMiddleware(
  c: Context,
  next: Next,
) {
  const expectedToken = getApiKey();

  if (!expectedToken) {
    return c.json({ error: "Server configuration error" }, 500);
  }

  // Check Authorization: Bearer <token> header
  const authHeader = c.req.header("Authorization");
  if (authHeader && authHeader.startsWith("Bearer ")) {
    const token = authHeader.substring(7);
    if (token === expectedToken) {
      await next();
      return;
    }
  }

  // Check X-API-Key header
  const apiKeyHeader = c.req.header("X-API-Key");
  if (apiKeyHeader === expectedToken) {
    await next();
    return;
  }

  // Check auth cookie
  const cookieToken = getCookie(c, AUTH_COOKIE_NAME);
  if (cookieToken === expectedToken) {
    await next();
    return;
  }

  // No valid auth found
  return c.json({ error: "Unauthorized" }, 401);
}

/**
 * Get API key from environment
 */
function getApiKey(): string | undefined {
  return Deno.env.get(API_KEY_ENV_VAR);
}

/**
 * Get password from environment
 */
function getPassword(): string | undefined {
  return Deno.env.get(PASSWORD_ENV_VAR);
}

/**
 * Create authentication cookie string
 */
export function createAuthCookie(apiKey: string): string {
  return `${AUTH_COOKIE_NAME}=${apiKey}; HttpOnly; Secure; SameSite=Strict; Max-Age=86400; Path=/`;
}

/**
 * Create logout cookie string (clears the auth cookie)
 */
export function createLogoutCookie(): string {
  return `${AUTH_COOKIE_NAME}=; HttpOnly; Secure; SameSite=Strict; Max-Age=0; Path=/`;
}

/**
 * Optional authentication middleware
 * Sets authenticated flag if valid auth is provided
 */
export async function optionalAuthMiddleware(c: Context, next: Next) {
  const expectedToken = getApiKey();
  if (!expectedToken) {
    await next();
    return;
  }

  // Check all auth methods
  const authHeader = c.req.header("Authorization");
  const apiKeyHeader = c.req.header("X-API-Key");
  const cookieToken = getCookie(c, AUTH_COOKIE_NAME);

  const token = authHeader?.startsWith("Bearer ")
    ? authHeader.substring(7)
    : (apiKeyHeader || cookieToken);

  if (token === expectedToken) {
    c.set("authenticated", true);
  }

  await next();
}

/**
 * Authentication handlers for frontend login/logout
 */
export const authHandlers = {
  /**
   * Handle user login with password validation
   * Sets authentication cookie on successful login
   */
  async login(c: Context) {
    const { password } = await c.req.json();
    const expectedPassword = getPassword();
    const apiKey = getApiKey();

    if (!expectedPassword || !apiKey) {
      return c.json({ error: "Server configuration error" }, 500);
    }

    if (password === expectedPassword) {
      const response = c.json({ success: true, message: "Login successful" });
      response.headers.set("Set-Cookie", createAuthCookie(apiKey));
      return response;
    }

    return c.json({ error: "Invalid password" }, 401);
  },

  /**
   * Handle user logout
   * Clears the authentication cookie
   */
  logout(c: Context) {
    const response = c.json({
      success: true,
      message: "Logged out successfully",
    });

    response.headers.set("Set-Cookie", createLogoutCookie());
    return response;
  },
};
