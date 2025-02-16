import { components } from "./schema";

export type SchemaType<T extends keyof components["schemas"]> =
  components["schemas"][T];

export type Config = SchemaType<"Config">;
export type DisplayModeRef = SchemaType<"DisplayModeRef">;
export type DisplayModeList = SchemaType<"DisplayModeRef">[];
export type Dimensions = SchemaType<"Dimensions">;
export type StateObject = SchemaType<"StateObject">;
