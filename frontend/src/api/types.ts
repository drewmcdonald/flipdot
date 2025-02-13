import { components } from "./schema";

export type SchemaType<T extends keyof components["schemas"]> =
  components["schemas"][T];

export type Config = SchemaType<"Config">;
