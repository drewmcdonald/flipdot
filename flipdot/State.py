import asyncio
import structlog # Import structlog

import serial
from pydantic import BaseModel

from flipdot.DotMatrix import DotMatrix
from flipdot.layout import Layout
from flipdot.mode import BaseDisplayMode, DisplayModeRef, get_display_mode
from flipdot.vend.flippydot import Panel

# Use structlog for this module
logger = structlog.get_logger(__name__)


class StateObject(BaseModel):
    """
    A Pydantic model representing a snapshot of the display state.
    This is typically used for serialization, e.g., in an API response.
    """
    mode: DisplayModeRef
    """The currently active display mode and its options."""
    errors: list[str]
    """A list of error messages that have occurred."""
    layout: Layout
    """The physical layout of the flip-dot display panels."""
    inverted: bool
    """Whether the display output is currently inverted (black/white swapped)."""
    flag: bool
    """
    A generic flag, often used to signal that the display needs an update
    or that a significant state change has occurred.
    """


class State:
    """
    Manages the overall state of the flip-dot display system.

    This class orchestrates the current display mode, handles rendering to the
    physical panel (or a simulated one), and keeps track of system status
    like errors, layout, and display inversion.
    """
    mode: BaseDisplayMode
    """The active display mode instance responsible for generating frames."""
    errors: set[str]
    """A set of unique error messages encountered during operation."""
    default_mode: DisplayModeRef
    """Reference to the default display mode to use on startup or reset."""
    dev: bool = False
    """
    Development mode flag. If True, may enable behaviors like rendering to
    the terminal instead of a physical serial connection.
    """

    def __init__(
        self,
        panel: Panel,
        serial_conn: serial.Serial | None,
        default_mode: DisplayModeRef,
        dev: bool = False,
    ):
        """
        Initializes the display state.

        Args:
            panel: The physical or virtual flip-dot panel controller.
            serial_conn: The serial connection object for communicating with the panel.
                         Can be None if in development mode or if panel is virtual.
            default_mode: A reference to the display mode to activate initially.
            dev: If True, enables development-specific behaviors (e.g., logging to console).
        """
        DefaultModeCls = get_display_mode(default_mode.mode_name)
        self.panel = panel
        """The underlying panel driver from the 'flippydot' library."""
        self.serial_conn = serial_conn
        """The serial connection to the physical display, if any."""
        self.layout = Layout.from_panel(panel)
        """The layout configuration derived from the panel."""
        self.mode = DefaultModeCls(layout=self.layout) # Initialize with default options for the mode
        """The currently active display mode."""
        self.inverted = False
        """Whether the display colors are inverted."""
        self.flag = False # General purpose flag, often indicates a need to re-render.
        """A flag that can be used to signal state changes or update requests."""
        self.errors = set()
        """A set to store any error messages encountered."""
        self.dev = dev
        """Development mode flag."""
        self.default_mode = default_mode # Store for potential resets or reference

    def to_object(self) -> StateObject:
        """
        Serializes the current state into a StateObject.

        Returns:
            A StateObject instance representing the current state.
        """
        return StateObject(
            mode=self.mode.to_ref(),
            errors=list(self.errors), # Convert set to list for JSON serialization
            layout=self.layout,
            inverted=self.inverted,
            flag=self.flag,
        )

    def toggle_inverted(self):
        """Toggles the color inversion state of the display and sets the update flag."""
        self.inverted = not self.inverted
        self.flag = True # Signal that the display needs to be updated

    async def set_mode(self, new_mode_ref: DisplayModeRef):
        """
        Changes the active display mode.

        Args:
            new_mode_ref: A DisplayModeRef object specifying the new mode
                          and its options.
        """
        ModeCls = get_display_mode(new_mode_ref.mode_name)
        # Ensure opts are provided to the mode's Options model for validation
        mode_opts = new_mode_ref.opts or {}
        validated_opts = ModeCls.Options(**mode_opts)

        display_mode = ModeCls(
            layout=self.layout,
            opts=validated_opts, # Pass validated options
        )
        display_mode.setup()  # Allow mode to perform initial setup
        self.mode = display_mode
        self.flag = True # Signal that the display mode has changed

    async def render(self):
        """
        Renders the current frame from the active display mode and sends it
        to the panel (or terminal in dev mode).
        """
        frame = self.mode.render()
        if self.inverted:
            frame = ~frame # Invert the frame if the inverted flag is set

        # Prepare data for the physical panel
        serial_data = self.panel.set_content(frame.mat)

        if self.serial_conn:
            self.serial_conn.write(serial_data)
        elif self.dev:
            # In development mode, draw to terminal instead of serial
            await self.draw_to_terminal()
        else:
            # Neither serial connection nor dev mode: log a warning
            logger.warning(
                "Render skipped: No serial connection or dev mode enabled.",
                has_serial_conn=self.serial_conn is not None,
                dev_mode=self.dev
            )

    async def draw_to_terminal(self):
        """
        Prints a representation of the current panel content to the logger.
        This is primarily used in development mode.
        """
        # Get the current content from the panel (which should match what was just set)
        # and log it as a DotMatrix string representation.
        # The string representation of DotMatrix is multi-line, so it will be a bit messy in JSON.
        # Consider logging shape or a summary if logs become too verbose.
        logger.info(
            "Current panel content (dev mode).", 
            panel_matrix_str=str(DotMatrix(self.panel.get_content()))
        )

    async def display_loop(self):
        """
        The main loop that continuously updates the display.

        It checks if the current mode needs rendering, renders it, and then
        waits for the mode's specified tick interval. It also handles
        exceptions during the loop and logs them. The loop can be broken
        by external changes to `self.flag`.
        """
        logger.info("Display loop: Starting...")
        while True:
            self.flag = False # Reset flag at the start of each major iteration
            # Inner loop: continues as long as `self.flag` is false (no major state changes)
            while not self.flag:
                try:
                    if self.mode.should_render():
                        await self.render()
                    # Wait for the time specified by the current mode's tick interval
                    await asyncio.sleep(self.mode.tick_interval)
                except asyncio.CancelledError:
                    logger.info("Display loop: Task cancelled. Exiting loop.")
                    return # Exit the loop if cancelled
                except Exception as e:
                    # Catch any exceptions during mode rendering or sleeping
                    # No need to import traceback, structlog handles exc_info=True
                    logger.error(
                        "Display loop: Error during update cycle.", 
                        exc_info=True, 
                        error_message=str(e),
                        current_mode=self.mode.to_ref().model_dump_json() if self.mode else "None"
                    )
                    self.errors.add(str(e)) # Add a concise version of the error to state
                    # Wait a bit before retrying to avoid tight error loops
                    await asyncio.sleep(1)
            # If self.flag became True, the outer loop will restart,
            # potentially with a new mode or state.
            logger.info("Display loop: Flag triggered. Re-evaluating state...")
