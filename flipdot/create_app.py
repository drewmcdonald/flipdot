import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Literal

import serial
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError

from flipdot.font import FontList, list_fonts
from flipdot.mode import DisplayModeConfig, DisplayModeRef, list_display_modes
from flipdot.State import State, StateObject
from flipdot.vend.flippydot import Panel

logger = logging.getLogger('uvicorn')


class Heartbeat(BaseModel):
    status: Literal["ok"] = "ok"


class Config(BaseModel):
    class Dimensions(BaseModel):
        width: int
        height: int

    fonts: FontList
    modes: list[DisplayModeConfig]
    dimensions: Dimensions


default_mode = DisplayModeRef(mode_name="clock", opts={})


def create_app(
    panel: Panel,
    serial_conn: serial.Serial | None = None,
    default_mode: DisplayModeRef = default_mode,
    dev: bool = False,
) -> FastAPI:
    state = State(
        panel=panel, serial_conn=serial_conn, default_mode=default_mode, dev=dev
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Starting lifespan")
        display_loop_task = asyncio.create_task(state.display_loop())
        yield
        await state.set_mode(DisplayModeRef(mode_name="white", opts={}))
        display_loop_task.cancel()

    app = FastAPI(lifespan=lifespan)

    @app.get('/api/heartbeat', response_model=Heartbeat)
    async def heartbeat():
        return Heartbeat()

    @app.get('/api/config', response_model=Config)
    async def get_config():
        return Config(
            fonts=list_fonts(),
            modes=list_display_modes(),
            dimensions=Config.Dimensions(
                width=state.panel.total_width,
                height=state.panel.total_height,
            ),
        )

    @app.get("/api/mode", response_model=DisplayModeRef)
    async def get_current_display_mode():
        return state.mode.to_ref()

    @app.patch("/api/mode", response_model=DisplayModeRef)
    async def set_current_display_mode(mode: DisplayModeRef):
        try:
            await state.set_mode(mode)
            return state.mode.to_ref()
        except KeyError as e:
            raise HTTPException(status_code=404, detail="Display mode not found") from e
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.get("/api/state", response_model=StateObject)
    async def get_state():
        return state.to_object()

    @app.post("/api/state/invert", response_model=StateObject)
    async def invert_display_colors():
        state.toggle_inverted()
        return state.to_object()

    @app.delete("/api/state/errors", response_model=StateObject)
    async def clear_errors():
        state.errors.clear()
        return state.to_object()

    static_dir = os.path.join(os.path.dirname(__file__), "dist")
    if os.path.exists(static_dir):
        logger.info(f"Mounting static files from {static_dir}")
        app.mount(
            "/assets",
            StaticFiles(directory=os.path.join(static_dir, "assets")),
            name="assets",
        )

        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            index_path = os.path.join(static_dir, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
            raise HTTPException(status_code=404, detail="File not found")

    return app
