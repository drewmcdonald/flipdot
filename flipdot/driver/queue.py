"""
Content queue with priority-based interruptions and timing logic.

The queue manages what content to display and when to advance frames.
Higher priority content can interrupt lower priority content.
"""

import logging
import threading
import time

from flipdot.driver.models import Content, Frame

logger = logging.getLogger(__name__)


class ContentState:
    """State for currently playing content."""

    def __init__(self, content: Content):
        self.content = content
        self.frame_index = 0
        self.loop_count = 0
        self.frame_start_time = time.time()
        self.paused = False
        self.paused_at: float | None = None
        self.time_paused: float = 0  # Total time spent paused

    @property
    def current_frame(self) -> Frame:
        """Get the current frame."""
        return self.content.frames[self.frame_index]

    @property
    def is_complete(self) -> bool:
        """Check if this content has finished playing."""
        if self.paused:
            return False

        playback = self.content.playback

        # If we're on the last frame
        if self.frame_index >= len(self.content.frames) - 1:
            # Not looping, we're done
            if not playback.loop:
                return True

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
        if self.paused:
            return False

        current_frame = self.current_frame
        duration = current_frame.duration_ms

        # If duration is None or 0, display indefinitely
        if not duration:
            return False

        elapsed_ms = (time.time() - self.frame_start_time - self.time_paused) * 1000

        if elapsed_ms >= duration:
            # Move to next frame
            self.frame_index += 1

            # Check if we need to loop
            if self.frame_index >= len(self.content.frames):
                if self.content.playback.loop:
                    self.frame_index = 0
                    self.loop_count += 1
                else:
                    # Don't advance past last frame, mark as complete
                    self.frame_index = len(self.content.frames) - 1

            self.frame_start_time = time.time()
            self.time_paused = 0
            return True

        return False

    def pause(self) -> None:
        """Pause playback (for interruptions)."""
        if not self.paused:
            self.paused = True
            self.paused_at = time.time()

    def resume(self) -> None:
        """Resume playback after interruption."""
        if self.paused and self.paused_at:
            self.time_paused += time.time() - self.paused_at
            self.paused = False
            self.paused_at = None

    def reset(self) -> None:
        """Reset to the beginning."""
        self.frame_index = 0
        self.loop_count = 0
        self.frame_start_time = time.time()
        self.time_paused = 0


class ContentQueue:
    """
    Priority-based queue for managing display content.

    Higher priority content interrupts lower priority content.
    When an interruption completes, the previous content resumes.

    Thread-safe for concurrent access from push server and main thread.
    All public methods are protected by a reentrant lock to prevent race conditions.
    Enforces memory bounds to prevent OOM from malicious/buggy servers.
    """

    # Maximum number of items to queue (prevents OOM attacks)
    MAX_QUEUED_ITEMS = 50

    # Maximum number of interrupted items to keep on stack
    MAX_INTERRUPTED_ITEMS = 10

    def __init__(self):
        self.current: ContentState | None = None
        self.queue: list[ContentState] = []  # Sorted by priority (highest first)
        self.interrupted: list[ContentState] = []  # Stack of interrupted content
        self._lock = threading.RLock()  # Reentrant lock for thread safety

    def add_content(self, content: Content) -> None:
        """
        Add new content to the queue.

        If the content has higher priority than current, it interrupts.
        Otherwise, it's added to the queue in priority order.

        Args:
            content: Content to add
        """
        with self._lock:
            new_state = ContentState(content)
            priority = content.playback.priority

            logger.info(f"Adding content {content.content_id} with priority {priority}")

            # If nothing is playing, start this immediately
            if self.current is None:
                self.current = new_state
                logger.info(f"Started playing {content.content_id} (queue was empty)")
                return

            current_priority = self.current.content.playback.priority

            # Higher priority interrupts current content
            if priority > current_priority:
                if self.current.content.playback.interruptible:
                    logger.info(
                        f"Interrupting {self.current.content.content_id} "
                        f"(priority {current_priority}) with {content.content_id} "
                        f"(priority {priority})"
                    )
                    self.current.pause()
                    self.interrupted.append(self.current)

                    # Enforce memory bound on interrupted stack
                    if len(self.interrupted) > self.MAX_INTERRUPTED_ITEMS:
                        dropped = self.interrupted.pop(0)
                        logger.warning(
                            f"Interrupted stack overflow: dropped {dropped.content.content_id}"
                        )

                    self.current = new_state
                else:
                    logger.warning(
                        f"Cannot interrupt {self.current.content.content_id} "
                        f"(marked as non-interruptible)"
                    )
                    self._add_to_queue(new_state)
            else:
                # Add to queue in priority order
                self._add_to_queue(new_state)

    def _add_to_queue(self, state: ContentState) -> None:
        """
        Add a state to the queue in priority order (highest first).

        If queue is full, drops the lowest-priority item.
        """
        priority = state.content.playback.priority

        # Find insertion point
        insert_idx = 0
        for i, queued in enumerate(self.queue):
            if priority <= queued.content.playback.priority:
                insert_idx = i + 1
            else:
                break

        self.queue.insert(insert_idx, state)

        # Enforce memory bound: drop lowest-priority item if queue is too full
        if len(self.queue) > self.MAX_QUEUED_ITEMS:
            dropped = self.queue.pop()
            logger.warning(
                f"Queue overflow: dropped {dropped.content.content_id} "
                f"(priority {dropped.content.playback.priority})"
            )

        logger.info(
            f"Added {state.content.content_id} to queue at position {insert_idx} "
            f"({len(self.queue)} items)"
        )

    def update(self) -> Frame | None:
        """
        Update the queue state and return the current frame to display.

        This should be called in the main loop. It handles:
        - Advancing frames based on timing
        - Removing completed content
        - Resuming interrupted content

        Returns:
            The current frame to display, or None if nothing to display
        """
        with self._lock:
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

                # Check if there was interrupted content to resume
                if self.interrupted:
                    self.current = self.interrupted.pop()
                    self.current.resume()
                    logger.info(
                        f"Resumed interrupted content {self.current.content.content_id}"
                    )
                # Otherwise, move to next in queue
                elif self.queue:
                    self.current = self.queue.pop(0)
                    logger.info(
                        f"Started next queued content {self.current.content.content_id}"
                    )
                else:
                    # Nothing left to display
                    self.current = None
                    logger.info("Queue is empty")
                    return None

            return self.current.current_frame if self.current else None

    def clear(self) -> None:
        """Clear all content from the queue."""
        with self._lock:
            logger.info("Clearing content queue")
            self.current = None
            self.queue.clear()
            self.interrupted.clear()

    def has_content(self) -> bool:
        """Check if there's any content to display."""
        with self._lock:
            return self.current is not None

    def get_current_content_id(self) -> str | None:
        """Get the ID of the currently playing content."""
        with self._lock:
            return self.current.content.content_id if self.current else None

    def replace_if_same_id(self, content: Content) -> bool:
        """
        Replace current content if it has the same ID (for updates).

        Args:
            content: New content

        Returns:
            True if replaced, False if not found
        """
        with self._lock:
            if self.current and self.current.content.content_id == content.content_id:
                logger.info(f"Replacing current content {content.content_id}")
                # Keep the current frame index and timing if possible
                old_frame_idx = self.current.frame_index
                self.current = ContentState(content)
                if old_frame_idx < len(content.frames):
                    self.current.frame_index = old_frame_idx
                return True

            # Check queue
            for i, state in enumerate(self.queue):
                if state.content.content_id == content.content_id:
                    logger.info(f"Replacing queued content {content.content_id}")
                    self.queue[i] = ContentState(content)
                    return True

            # Check interrupted
            for i, state in enumerate(self.interrupted):
                if state.content.content_id == content.content_id:
                    logger.info(f"Replacing interrupted content {content.content_id}")
                    self.interrupted[i] = ContentState(content)
                    return True

            return False
