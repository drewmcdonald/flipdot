import type { MutationCtx } from "../_generated/server";

/** Throws unless the caller has an authenticated session. */
export async function requireAuth(ctx: MutationCtx): Promise<void> {
  const identity = await ctx.auth.getUserIdentity();
  if (!identity) {
    throw new Error("Not authenticated");
  }
}
