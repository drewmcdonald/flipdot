/**
 * Storage abstraction layer
 * Uses Val Town blob in production, local filesystem in development
 */

import { blob } from "https://esm.town/v/std/blob?v=13";

const LOCAL_STORAGE_DIR = "./.local-storage";

/**
 * Detect if running locally (not in Val Town environment)
 */
function isLocalEnvironment(): boolean {
  // Val Town sets specific environment variables
  // If IS_VALTOWN exists, we're in Val Town
  return !Deno.env.get("IS_VALTOWN");
}

/**
 * Ensure local storage directory exists
 */
async function ensureLocalStorageDir(): Promise<void> {
  try {
    await Deno.mkdir(LOCAL_STORAGE_DIR, { recursive: true });
  } catch (error) {
    if (!(error instanceof Deno.errors.AlreadyExists)) {
      throw error;
    }
  }
}

/**
 * Get local file path for key
 */
function getLocalFilePath(key: string): string {
  // Replace colons and slashes with underscores for filesystem safety
  const safeKey = key.replace(/[/:]/g, "_");
  return `${LOCAL_STORAGE_DIR}/${safeKey}.json`;
}

/**
 * Local filesystem implementation
 */
const localStorage = {
  async getJSON(key: string): Promise<unknown> {
    try {
      const filePath = getLocalFilePath(key);
      const content = await Deno.readTextFile(filePath);
      return JSON.parse(content);
    } catch (error) {
      if (error instanceof Deno.errors.NotFound) {
        return null;
      }
      throw error;
    }
  },

  async setJSON(key: string, value: unknown): Promise<void> {
    await ensureLocalStorageDir();
    const filePath = getLocalFilePath(key);
    const content = JSON.stringify(value, null, 2);
    await Deno.writeTextFile(filePath, content);
  },

  async delete(key: string): Promise<void> {
    try {
      const filePath = getLocalFilePath(key);
      await Deno.remove(filePath);
    } catch (error) {
      if (!(error instanceof Deno.errors.NotFound)) {
        throw error;
      }
    }
  },

  async list(prefix?: string): Promise<string[]> {
    try {
      await ensureLocalStorageDir();
      const keys: string[] = [];

      for await (const entry of Deno.readDir(LOCAL_STORAGE_DIR)) {
        if (entry.isFile && entry.name.endsWith(".json")) {
          // Remove .json extension and convert underscores back to colons
          let key = entry.name.slice(0, -5);
          key = key.replace(/_/g, ":");

          if (!prefix || key.startsWith(prefix)) {
            keys.push(key);
          }
        }
      }

      return keys;
    } catch (error) {
      if (error instanceof Deno.errors.NotFound) {
        return [];
      }
      throw error;
    }
  },
};

/**
 * Storage interface matching Val Town blob API
 */
export interface Storage {
  getJSON(key: string): Promise<unknown>;
  setJSON(key: string, value: unknown): Promise<void>;
  delete(key: string): Promise<void>;
  list(prefix?: string): Promise<string[]>;
}

/**
 * Val Town blob storage adapter
 * Wraps Val Town blob to match our Storage interface
 */
const valTownStorage: Storage = {
  getJSON: (key: string) => blob.getJSON(key),
  setJSON: (key: string, value: unknown) => blob.setJSON(key, value),
  delete: (key: string) => blob.delete(key),
  list: async (prefix?: string) => {
    const results = await blob.list(prefix);
    return results.map((item) => item.key);
  },
};

/**
 * Get storage instance based on environment
 */
export function getStorage(): Storage {
  if (isLocalEnvironment()) {
    console.log("[Storage] Using local filesystem storage");
    return localStorage;
  } else {
    console.log("[Storage] Using Val Town blob storage");
    return valTownStorage;
  }
}

/**
 * Default storage export
 */
export const storage = getStorage();
