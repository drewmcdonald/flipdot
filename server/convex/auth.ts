import { v } from "convex/values";
import { convexAuth } from "@convex-dev/auth/server";
import { ConvexCredentials } from "@convex-dev/auth/providers/ConvexCredentials";
import { RateLimiter, MINUTE } from "@convex-dev/rate-limiter";
import { internalMutation } from "./_generated/server";
import { internal, components } from "./_generated/api";

// Global limit on sign-in attempts (there's no per-caller identity to key on
// pre-auth) -- caps password brute-forcing regardless of whether an attempt
// guesses right or wrong.
const rateLimiter = new RateLimiter(components.rateLimiter, {
  controlSignIn: { kind: "fixed window", rate: 10, period: 5 * MINUTE },
});

/**
 * Single shared-password auth for the control panel. There is no signup
 * flow and no user accounts -- everyone who knows CONTROL_PASSWORD signs
 * in as the same lone "control" user.
 */
export const { auth, signIn, signOut, store, isAuthenticated } = convexAuth({
  providers: [
    ConvexCredentials({
      id: "control-password",
      authorize: async (credentials, ctx) => {
        await rateLimiter.limit(ctx, "controlSignIn", {
          key: "global",
          throws: true,
        });

        const password = credentials.password;
        const expected = process.env.CONTROL_PASSWORD;
        if (!expected || typeof password !== "string" || password !== expected) {
          throw new Error("Invalid password");
        }
        const userId = await ctx.runMutation(
          internal.auth.getOrCreateControlUser,
          {}
        );
        return { userId };
      },
    }),
  ],
});

export const getOrCreateControlUser = internalMutation({
  args: {},
  returns: v.id("users"),
  handler: async (ctx) => {
    const existing = await ctx.db.query("users").first();
    if (existing) return existing._id;
    return await ctx.db.insert("users", {});
  },
});
