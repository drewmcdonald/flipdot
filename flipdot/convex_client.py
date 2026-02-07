"""Convex real-time content client."""

from __future__ import annotations

import logging
from threading import Event, Lock, Thread
from typing import Any, final

from convex import ConvexClient

from .models import Content, ContentResponse, ResponseStatus

logger = logging.getLogger(__name__)


@final
class ConvexContentClient:
    """
    Real-time content subscription via Convex.

    Runs a background thread that subscribes to display updates.
    Main loop calls wait_for_update() which blocks until content changes.
    """

    def __init__(self, convex_url: str, display_name: str):
        self._client: ConvexClient = ConvexClient(convex_url)
        self._display_name: str = display_name
        self._lock: Lock = Lock()
        self._content_changed: Event = Event()
        self._latest: Content | None = None
        self._last_seen_id: str | None = None
        self._running: bool = False
        self._thread: Thread | None = None

    def start(self) -> None:
        """Start background subscription thread."""
        self._running = True
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"Convex subscription started for display '{self._display_name}'")

    def _run(self) -> None:
        """Background: subscribe and store latest content."""
        try:
            for result in self._client.subscribe(
                "displays:getCurrentDisplay",
                {"name": self._display_name},
            ):
                if not self._running:
                    break
                with self._lock:
                    # result can be various types from Convex, we expect a dict
                    if isinstance(result, dict):
                        content: Any = result.get("content")
                        if content is not None:
                            self._latest = Content.model_validate(content)
                        else:
                            self._latest = None
                    else:
                        self._latest = None
                # Signal that content may have changed
                self._content_changed.set()
        except Exception as e:
            logger.error(f"Convex subscription error: {e}")

    def wait_for_update(self, timeout: float) -> ContentResponse | None:
        """
        Block until content changes or timeout expires.

        Args:
            timeout: Maximum seconds to wait

        Returns:
            ContentResponse if content changed, None if timeout or no change
        """
        # Wait for signal from subscription thread
        _ = self._content_changed.wait(timeout)
        self._content_changed.clear()

        with self._lock:
            if self._latest is None:
                # Content cleared
                if self._last_seen_id is not None:
                    self._last_seen_id = None
                    return ContentResponse(status=ResponseStatus.CLEAR, playlist=[])
                return None

            # No change
            if self._latest.content_id == self._last_seen_id:
                return None

            # New content
            self._last_seen_id = self._latest.content_id
            return ContentResponse(
                status=ResponseStatus.UPDATED,
                playlist=[self._latest],
            )

    def close(self) -> None:
        """Stop subscription."""
        self._running = False
        # Wake up any waiting thread so it can exit
        self._content_changed.set()
        logger.info("Convex subscription stopped")
