import asyncio
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError

from flipdot.display_mode import DisplayModeList, DisplayModeRef, list_display_modes
from flipdot.State import State, StateObject
from flipdot.vend.flippydot import Panel


class Heartbeat(BaseModel):
    status: Literal["ok"] = "ok"


def create_app(
    panel: Panel,
    default_mode: DisplayModeRef = DisplayModeRef(name="clock"),
    debug: bool = False,
) -> FastAPI:
    state = State(panel=panel, default_mode=default_mode, debug=debug)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        display_loop_task = asyncio.create_task(state.display_loop())
        yield
        display_loop_task.cancel()

    app = FastAPI(lifespan=lifespan)

    @app.get('/heartbeat', response_model=Heartbeat)
    async def heartbeat():
        return Heartbeat()

    @app.get('/modes', response_model=DisplayModeList)
    async def get_registered_display_modes():
        return list_display_modes()

    @app.get("/mode", response_model=DisplayModeRef)
    async def get_current_display_mode():
        return state.current_mode_ref()

    @app.patch("/mode", response_model=DisplayModeRef)
    async def set_current_display_mode(mode: DisplayModeRef):
        try:
            await state.set_mode(mode)
            return state.current_mode_ref()
        except KeyError:
            raise HTTPException(status_code=404, detail="Display mode not found")
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/state", response_model=StateObject)
    async def get_state():
        return state.to_object()

    @app.post("/state/invert", response_model=StateObject)
    async def invert_display_colors():
        state.inverted = not state.inverted
        return state.to_object()

    @app.delete("/state/errors", response_model=StateObject)
    async def clear_errors():
        state.errors.clear()
        return state.to_object()

    return app
