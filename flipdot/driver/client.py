"""
HTTP client for fetching content from the remote server.

Handles polling for updates and authentication.
"""

import json
import logging
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flipdot.driver.models import AuthConfig, ContentResponse, ErrorFallback

logger = logging.getLogger(__name__)


class ContentClient:
    """Client for fetching content from a remote server."""

    def __init__(
        self,
        endpoint: str,
        auth: AuthConfig,
        timeout: int = 10,
    ):
        """
        Initialize the content client.

        Args:
            endpoint: URL to poll for content
            auth: Authentication configuration
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint
        self.auth = auth
        self.timeout = timeout
        self.last_poll_time: float | None = None
        self.poll_interval_ms = 30000  # Default, can be updated by server
        self.consecutive_errors = 0

        # Exponential backoff for network failures
        self.max_backoff_ms = 300000  # 5 minutes max backoff
        self.backoff_multiplier = 2.0
        self.initial_backoff_ms = 1000  # 1 second initial backoff

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers including authentication."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "FlipDot-Driver/2.0",
        }

        if self.auth.type == "bearer" and self.auth.token:
            headers["Authorization"] = f"Bearer {self.auth.token}"
        elif self.auth.type == "api_key" and self.auth.key:
            headers[self.auth.header_name] = self.auth.key

        return headers

    def fetch_content(self) -> ContentResponse | None:
        """
        Fetch content from the server.

        Returns:
            ContentResponse if successful, None if error occurred
        """
        try:
            headers = self._build_headers()
            request = Request(self.endpoint, headers=headers)

            logger.debug(f"Fetching content from {self.endpoint}")
            start_time = time.time()

            with urlopen(request, timeout=self.timeout) as response:
                elapsed = time.time() - start_time
                data = response.read().decode("utf-8")
                content_response = ContentResponse.model_validate_json(data)

                # Update poll interval if server specified
                self.poll_interval_ms = content_response.poll_interval_ms
                self.last_poll_time = time.time()
                self.consecutive_errors = 0

                logger.info(
                    f"Fetched content (status={content_response.status}) "
                    f"in {elapsed:.2f}s, next poll in {self.poll_interval_ms}ms"
                )

                return content_response

        except HTTPError as e:
            self.consecutive_errors += 1
            if e.code == 401 or e.code == 403:
                logger.error(f"Authentication failed: {e}")
            elif e.code == 404:
                logger.error(f"Endpoint not found: {self.endpoint}")
            else:
                logger.error(f"HTTP error {e.code}: {e.reason}")
            return None

        except URLError as e:
            self.consecutive_errors += 1
            logger.error(f"Network error: {e.reason}")
            return None

        except json.JSONDecodeError as e:
            self.consecutive_errors += 1
            logger.error(f"Invalid JSON response: {e}")
            return None

        except Exception as e:
            self.consecutive_errors += 1
            logger.error(f"Unexpected error fetching content: {e}")
            return None

    def _get_effective_poll_interval(self) -> float:
        """
        Calculate effective poll interval with exponential backoff on errors.

        Returns:
            Poll interval in milliseconds, including backoff
        """
        if self.consecutive_errors == 0:
            return self.poll_interval_ms

        # Exponential backoff: 1s, 2s, 4s, 8s, ... up to max_backoff_ms
        backoff = self.initial_backoff_ms * (
            self.backoff_multiplier ** (self.consecutive_errors - 1)
        )
        backoff = min(backoff, self.max_backoff_ms)

        return max(self.poll_interval_ms, backoff)

    def should_poll(self) -> bool:
        """
        Check if enough time has elapsed for the next poll.

        Returns:
            True if it's time to poll again
        """
        if self.last_poll_time is None:
            return True

        elapsed_ms = (time.time() - self.last_poll_time) * 1000
        effective_interval = self._get_effective_poll_interval()
        return elapsed_ms >= effective_interval

    def get_next_poll_delay_ms(self) -> float:
        """
        Get the time until the next poll should occur.

        Accounts for exponential backoff on errors.

        Returns:
            Milliseconds to wait before next poll (0 if should poll now)
        """
        if self.last_poll_time is None:
            return 0

        elapsed_ms = (time.time() - self.last_poll_time) * 1000
        effective_interval = self._get_effective_poll_interval()
        remaining = effective_interval - elapsed_ms
        return max(0, remaining)

    def reset_poll_timer(self) -> None:
        """Reset the poll timer (e.g., after receiving a push notification)."""
        self.last_poll_time = time.time()


class ErrorHandler:
    """Handles error scenarios based on fallback configuration."""

    def __init__(self, fallback: ErrorFallback):
        """
        Initialize error handler.

        Args:
            fallback: Fallback behavior configuration
        """
        self.fallback = fallback
        self.last_successful_content: ContentResponse | None = None

    def set_last_successful(self, response: ContentResponse) -> None:
        """Record the last successful content fetch."""
        if response.content:
            self.last_successful_content = response

    def get_fallback_response(self) -> ContentResponse | None:
        """
        Get the appropriate fallback response based on configuration.

        Returns:
            ContentResponse to use as fallback, or None
        """
        if self.fallback == ErrorFallback.KEEP_LAST:
            if self.last_successful_content:
                logger.info("Using last successful content as fallback")
                return self.last_successful_content
            else:
                logger.warning("No previous content available for fallback")
                return None

        elif self.fallback == ErrorFallback.BLANK:
            logger.info("Fallback: clearing display")
            from flipdot.driver.models import ResponseStatus

            return ContentResponse(
                status=ResponseStatus.CLEAR,
                poll_interval_ms=30000,
            )

        elif self.fallback == ErrorFallback.ERROR_MESSAGE:
            # For now, just clear. In the future, could generate an error message frame
            logger.info("Fallback: showing error state")
            from flipdot.driver.models import ResponseStatus

            return ContentResponse(
                status=ResponseStatus.CLEAR,
                poll_interval_ms=10000,  # Poll more frequently to recover
            )

        return None
