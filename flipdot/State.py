import asyncio
import logging

import serial
from pydantic import BaseModel

from flipdot.display_mode import BaseDisplayMode, DisplayModeRef, get_display_mode
from flipdot.layout import Layout
from flipdot.util import prettify_dot_matrix
from flipdot.vend.flippydot import Panel

logger = logging.getLogger('uvicorn')


class StateObject(BaseModel):
    mode: DisplayModeRef
    errors: list[str]
    layout: Layout
    inverted: bool
    flag: bool


class State:
    mode: BaseDisplayMode
    errors: set[str]
    default_mode: DisplayModeRef
    debug: bool = False

    def __init__(
        self,
        panel: Panel,
        serial_conn: serial.Serial | None,
        default_mode: DisplayModeRef,
        debug: bool = False,
    ):
        DefaultMode = get_display_mode(default_mode.name)
        self.panel = panel
        self.serial_conn = serial_conn
        self.layout = Layout.from_panel(panel)
        self.mode = DefaultMode(
            layout=self.layout,
            opts=DefaultMode.Options(**default_mode.opts or {}),
        )
        self.inverted = False
        self.flag = False
        self.errors = set()
        self.debug = debug

    def to_object(self) -> StateObject:
        return StateObject(
            mode=self.current_mode_ref(),
            errors=list(self.errors),
            layout=self.layout,
            inverted=self.inverted,
            flag=self.flag,
        )

    def toggle_inverted(self):
        self.inverted = not self.inverted
        self.flag = True

    async def set_mode(self, new_mode: DisplayModeRef):
        ModeCls = get_display_mode(new_mode.name)
        opts = new_mode.opts or {}
        display_mode = ModeCls(
            layout=self.layout,
            opts=ModeCls.Options(**opts),
        )
        display_mode.setup()
        self.mode = display_mode
        self.flag = True

    async def render(self):
        frame = self.mode.render()
        if self.inverted:
            frame = 1 - frame
        serial_data = self.panel.set_content(frame)
        if self.serial_conn:
            self.serial_conn.write(serial_data)
        elif self.debug:
            await self.draw_to_terminal()
        else:
            logger.warning("No connection or debug mode, skipping render")

    async def draw_to_terminal(self):
        content = self.panel.get_content()
        logger.info(prettify_dot_matrix(content))

    def current_mode_ref(self) -> DisplayModeRef:
        return DisplayModeRef(
            name=self.mode.mode_name,
            opts=self.mode.opts.model_dump(),
        )

    async def display_loop(self):
        logger.info("Starting display loop")
        while True:
            self.flag = False
            while not self.flag:
                try:
                    if self.mode.should_render():
                        await self.render()
                    await asyncio.sleep(self.mode.tick_interval)
                except Exception as e:
                    logger.error(f"Error in display loop: {e}")
                    self.errors.add(str(e))
                    await asyncio.sleep(1)
