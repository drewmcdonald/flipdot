/**
 * Content router with priority queue
 * Manages content sources and selects highest priority content
 */

import { storage } from "../storage.ts";
import type { Content } from "../../shared/types.ts";
import type { CachedContent, ContentSource } from "./types.ts";
import { isCacheValid } from "./types.ts";

/**
 * Content router class
 */
export class ContentRouter {
  private sources: Map<string, ContentSource> = new Map();
  private lastContentId: string | null = null;

  /**
   * Register a content source
   */
  registerSource(source: ContentSource): void {
    this.sources.set(source.id, source);
  }

  /**
   * Unregister a content source
   */
  unregisterSource(sourceId: string): void {
    this.sources.delete(sourceId);
  }

  /**
   * Get all registered sources
   */
  getSources(): ContentSource[] {
    return Array.from(this.sources.values());
  }

  /**
   * Get cached content from blob storage
   */
  private async getCachedContent(
    cacheKey: string,
  ): Promise<Content | null> {
    try {
      const cached = await storage.getJSON(cacheKey) as CachedContent | null;
      if (!cached) {
        return null;
      }

      const now = Date.now();
      if (isCacheValid(cached, now)) {
        return cached.content;
      }

      // Cache expired, delete it
      await storage.delete(cacheKey);
      return null;
    } catch (error) {
      console.error(`Error reading cache key ${cacheKey}:`, error);
      return null;
    }
  }

  /**
   * Set cached content in blob storage
   */
  private async setCachedContent(
    cacheKey: string,
    content: Content,
    ttl_ms: number,
  ): Promise<void> {
    try {
      const cached: CachedContent = {
        content,
        cached_at: Date.now(),
        ttl_ms,
      };
      await storage.setJSON(cacheKey, cached);
    } catch (error) {
      console.error(`Error writing cache key ${cacheKey}:`, error);
    }
  }

  /**
   * Get content from a source (with caching)
   */
  private async getSourceContent(
    source: ContentSource,
  ): Promise<Content | null> {
    // Build cache key from source ID
    const cacheKey = `flipdot:source:${source.id}`;

    // Try to get from cache
    let content = await this.getCachedContent(cacheKey);

    // If cache miss, generate new content
    if (!content) {
      try {
        content = await source.generate();
        await this.setCachedContent(cacheKey, content, source.ttl_ms);
      } catch (error) {
        console.error(
          `Error generating content from source ${source.id}:`,
          error,
        );
        return null;
      }
    }

    return content;
  }

  /**
   * Select highest priority content from all sources
   */
  async selectContent(): Promise<Content | null> {
    const sources = this.getSources();

    if (sources.length === 0) {
      console.warn("No content sources registered");
      return null;
    }

    // Get content from all sources
    const contentPromises = sources.map(async (source) => {
      const content = await this.getSourceContent(source);
      return { source, content };
    });

    const results = await Promise.all(contentPromises);

    // Filter out null content
    const available = results.filter((r) => r.content !== null) as Array<{
      source: ContentSource;
      content: Content;
    }>;

    if (available.length === 0) {
      console.warn("No content available from any source");
      return null;
    }

    // Sort by priority (descending)
    available.sort((a, b) => b.source.priority - a.source.priority);

    // Return highest priority content
    const selected = available[0].content;

    return selected;
  }

  /**
   * Check if content has changed since last selection
   */
  hasContentChanged(content: Content | null): boolean {
    if (!content) {
      return this.lastContentId !== null;
    }
    return content.content_id !== this.lastContentId;
  }

  /**
   * Get last sent content ID
   */
  getLastContentId(): string | null {
    return this.lastContentId;
  }

  /**
   * Update last content ID (call after sending content)
   */
  updateLastContentId(contentId: string): void {
    this.lastContentId = contentId;
  }

  /**
   * Load last content ID from persistent storage
   */
  async loadLastContentId(): Promise<void> {
    try {
      const lastId = await storage.getJSON("flipdot:last_content_id") as
        | string
        | null;
      this.lastContentId = lastId;
    } catch (error) {
      console.error("Error loading last content ID:", error);
    }
  }

  /**
   * Save last content ID to persistent storage
   */
  async saveLastContentId(): Promise<void> {
    try {
      if (this.lastContentId) {
        await storage.setJSON("flipdot:last_content_id", this.lastContentId);
      }
    } catch (error) {
      console.error("Error saving last content ID:", error);
    }
  }
}
