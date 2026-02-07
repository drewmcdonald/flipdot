import { cronJobs } from "convex/server";
import { internal } from "./_generated/api";

const crons = cronJobs();

/**
 * Update the clock display every minute
 * Runs at the start of each minute
 */
crons.interval(
  "update clock",
  { minutes: 1 },
  internal.content.clock.generateClock
);

export default crons;
