import { cronJobs } from "convex/server";
import { internal } from "./_generated/api";

const crons = cronJobs();

/**
 * Update the clock content source every minute
 */
crons.interval(
  "update clock",
  { minutes: 1 },
  internal.content.clock.generateClock
);

/**
 * Compositor: picks active source and writes to displays
 * Runs every 10 seconds — rotation transition latency is at most 10s
 */
crons.interval(
  "compose display",
  { seconds: 10 },
  internal.compositor.compose
);

export default crons;
