/* eslint-disable */
/**
 * Generated `api` utility.
 *
 * THIS CODE IS AUTOMATICALLY GENERATED.
 *
 * To regenerate, run `npx convex dev`.
 * @module
 */

import type * as compositor from "../compositor.js";
import type * as content_adhoc from "../content/adhoc.js";
import type * as content_clock from "../content/clock.js";
import type * as content_sources from "../content_sources.js";
import type * as crons from "../crons.js";
import type * as display_config from "../display_config.js";
import type * as displays from "../displays.js";
import type * as fonts_axion_6x7 from "../fonts/axion_6x7.js";
import type * as fonts_cg_pixel_4x5 from "../fonts/cg_pixel_4x5.js";
import type * as lib_rotation from "../lib/rotation.js";
import type * as rendering_bits from "../rendering/bits.js";
import type * as rendering_compose from "../rendering/compose.js";
import type * as rendering_fontLoader from "../rendering/fontLoader.js";
import type * as rendering_frame from "../rendering/frame.js";
import type * as types from "../types.js";

import type {
  ApiFromModules,
  FilterApi,
  FunctionReference,
} from "convex/server";

declare const fullApi: ApiFromModules<{
  compositor: typeof compositor;
  "content/adhoc": typeof content_adhoc;
  "content/clock": typeof content_clock;
  content_sources: typeof content_sources;
  crons: typeof crons;
  display_config: typeof display_config;
  displays: typeof displays;
  "fonts/axion_6x7": typeof fonts_axion_6x7;
  "fonts/cg_pixel_4x5": typeof fonts_cg_pixel_4x5;
  "lib/rotation": typeof lib_rotation;
  "rendering/bits": typeof rendering_bits;
  "rendering/compose": typeof rendering_compose;
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
