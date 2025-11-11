"""
Simple playlist-based content queue.

The server sends a complete playlist, and the client just plays it in order.
No priorities, no interruptions, no complex state management.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from typing import TYPE_CHECKING

from flipdot.models import Content, Frame

if TYPE_CHECKING:
    from flipdot.config import DriverLimits

logger = logging.getLogger(__name__)


class ContentState:
    """State for currently playing content."""

    def __init__(self, content: Content):
        self.content: Content = content
        self.frame_index: int = 0
        self.loop_count: int = 0
        self.frame_start_time: float = time.time()

    @property
    def current_frame(self) -> Frame:
        """Get the current frame."""
        return self.content.frames[self.frame_index]

    @property
    def is_complete(self) -> bool:
        """Check if this content has finished playing."""
        playback = self.content.playback

        # If we're on the last frame
        if self.frame_index >= len(self.content.frames) - 1:
            # Not looping
            if not playback.loop:
                # If the frame has a duration, check if it has elapsed
                current_frame = self.current_frame
                if current_frame.duration_ms:
                    elapsed_ms = (time.time() - self.frame_start_time) * 1000
                    if elapsed_ms >= current_frame.duration_ms:
                        return True
                    return False
                # If duration is None/0, display indefinitely (not complete)
                return False

            # Looping with a count limit
            if (
                playback.loop_count is not None
                and self.loop_count >= playback.loop_count
            ):
                return True

        return False

    def advance_frame(self) -> bool:
        """
        Advance to the next frame if enough time has elapsed.

        Returns:
            True if frame was advanced, False otherwise
        """
        current_frame = self.current_frame
        duration = current_frame.duration_ms

        # If duration is None or 0, display indefinitely
        if not duration:
            return False

        elapsed_ms = (time.time() - self.frame_start_time) * 1000

        if elapsed_ms >= duration:
            # Move to next frame
            self.frame_index += 1

            # Check if we need to loop
            if self.frame_index >= len(self.content.frames):
                if self.content.playback.loop:
                    self.frame_index = 0
                    self.loop_count += 1
                    # Reset timer for the loop
                    self.frame_start_time = time.time()
                else:
                    # Don't advance past last frame
                    # Don't reset timer - let is_complete detect the end
                    self.frame_index = len(self.content.frames) - 1
            else:
                # Moving to a new frame, reset timer
                self.frame_start_time = time.time()

            return True

        return False


class ContentQueue:
    """
    Simple FIFO playlist for managing display content.

    Server sends complete playlist. Client just plays it in order.
    No merge logic, no priorities, no interruptions.
    """

    def __init__(self, limits: DriverLimits | None = None):
        """
        Initialize the content queue.

        Args:
            limits: Driver limits configuration (uses DEFAULT_LIMITS if None)
        """
        from flipdot.config import DEFAULT_LIMITS

        self.limits: DriverLimits = limits if limits is not None else DEFAULT_LIMITS
        self.current: ContentState | None = None
        self.queue: deque[ContentState] = deque()

    def set_playlist(self, playlist: list[Content]) -> None:
        """
        Replace entire queue with new playlist from server.

        First item becomes current (preserving frame timing if same ID).
        Rest go into queue in order.

        Args:
            playlist: Complete ordered playlist from server
        """
        if not playlist:
            logger.info("Received empty playlist, clearing")
            self.clear()
            return

        # Check if first item is same as current (preserve timing)
        new_current = playlist[0]
        old_current_state = self.current

        if (
            old_current_state
            and old_current_state.content.content_id == new_current.content_id
        ):
            logger.debug(f"Preserving playback state for {new_current.content_id}")
            # Keep existing state for smooth continuation
            new_current_state = old_current_state
            # But update the content object (in case frames changed)
            new_current_state.content = new_current
            # Validate frame index is still valid
            if new_current_state.frame_index >= len(new_current.frames):
                new_current_state.frame_index = 0
                new_current_state.loop_count = 0
                new_current_state.frame_start_time = time.time()
        else:
            # New content, start fresh
            logger.info(f"Starting new content: {new_current.content_id}")
            new_current_state = ContentState(new_current)

        self.current = new_current_state

        # Replace queue with rest of playlist
        self.queue.clear()
        for content in playlist[1:]:
            self.queue.append(ContentState(content))

        logger.info(
            f"Playlist updated: current={new_current.content_id}, "
            f"queue={len(self.queue)} items"
        )

    def update(self) -> Frame | None:
        """
        Update the queue state and return the current frame to display.

        This should be called in the main loop. It handles:
        - Advancing frames based on timing
        - Moving to next content when current completes

        Returns:
            The current frame to display, or None if nothing to display
        """
        if self.current is None:
            return None

        # Try to advance the frame
        if self.current.advance_frame():
            logger.debug(
                f"Advanced to frame {self.current.frame_index} "
                f"of {self.current.content.content_id}"
            )

        # Check if current content is complete
        if self.current.is_complete:
            logger.info(f"Content {self.current.content.content_id} completed")

            # Move to next in queue
            if self.queue:
                self.current = self.queue.popleft()
                logger.info(
                    f"Started next content: {self.current.content.content_id} "
                    f"({len(self.queue)} remaining in queue)"
                )
            else:
                # Nothing left to display
                self.current = None
                logger.info("Playlist complete, nothing to display")
                return None

        return self.current.current_frame if self.current else None

    def clear(self) -> None:
        """Clear all content from the queue."""
        logger.info("Clearing content queue")
        self.current = None
        self.queue.clear()

    def has_content(self) -> bool:
        """Check if there's any content to display."""
        return self.current is not None

    def get_current_content_id(self) -> str | None:
        """Get the ID of the currently playing content."""
        return self.current.content.content_id if self.current else None
