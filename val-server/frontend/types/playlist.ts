/**
 * Playlist item types for the playlist builder
 */

export type PlaylistItemType = "text" | "pattern" | "transition";

export interface BasePlaylistItem {
  id: string;
  type: PlaylistItemType;
  priority: number;
  ttl_ms?: number;
}

export interface TextPlaylistItem extends BasePlaylistItem {
  type: "text";
  config: {
    text: string;
    scroll?: boolean;
    frame_delay_ms?: number;
  };
}

export interface PatternPlaylistItem extends BasePlaylistItem {
  type: "pattern";
  config: {
    pattern_type: string;
    duration_ms?: number;
    frame_delay_ms?: number;
    options?: Record<string, unknown>;
  };
}

export interface TransitionPlaylistItem extends BasePlaylistItem {
  type: "transition";
  config: {
    transition_type: string;
    duration_ms?: number;
    frame_delay_ms?: number;
    direction?: string;
  };
}

export type PlaylistItem =
  | TextPlaylistItem
  | PatternPlaylistItem
  | TransitionPlaylistItem;

export interface PatternInfo {
  type: string;
  description: string;
  options?: Record<string, string>;
}

export interface TransitionInfo {
  type: string;
  description: string;
  options?: Record<string, string>;
}
