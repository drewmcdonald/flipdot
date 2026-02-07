/* eslint-disable */
/**
 * Generated `api` utility.
 *
 * THIS CODE IS AUTOMATICALLY GENERATED.
 *
 * To regenerate, run `npx convex dev`.
 * @module
 */

import type * as content_clock from "../content/clock.js";
import type * as crons from "../crons.js";
import type * as displays from "../displays.js";
import type * as fonts_axion_6x7 from "../fonts/axion_6x7.js";
import type * as fonts_cg_pixel_4x5 from "../fonts/cg_pixel_4x5.js";
import type * as rendering_bits from "../rendering/bits.js";
import type * as rendering_fontLoader from "../rendering/fontLoader.js";
import type * as rendering_frame from "../rendering/frame.js";
import type * as types from "../types.js";

import type {
  ApiFromModules,
  FilterApi,
  FunctionReference,
} from "convex/server";

declare const fullApi: ApiFromModules<{
  "content/clock": typeof content_clock;
  crons: typeof crons;
  displays: typeof displays;
  "fonts/axion_6x7": typeof fonts_axion_6x7;
  "fonts/cg_pixel_4x5": typeof fonts_cg_pixel_4x5;
  "rendering/bits": typeof rendering_bits;
  "rendering/fontLoader": typeof rendering_fontLoader;
  "rendering/frame": typeof rendering_frame;
  types: typeof types;
}>;

/**
 * A utility for referencing Convex functions in your app's public API.
 *
 * Usage:
 * ```js
 * const myFunctionReference = api.myModule.myFunction;
 * ```
 */
export declare const api: FilterApi<
  typeof fullApi,
  FunctionReference<any, "public">
>;

/**
 * A utility for referencing Convex functions in your app's internal API.
 *
 * Usage:
 * ```js
 * const myFunctionReference = internal.myModule.myFunction;
 * ```
 */
export declare const internal: FilterApi<
  typeof fullApi,
  FunctionReference<any, "internal">
>;

export declare const components: {};
