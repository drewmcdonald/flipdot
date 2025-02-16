from pydantic import BaseModel

from flipdot.mode.BaseDisplayMode import BaseDisplayMode, DisplayModeRef
from flipdot.mode.Clock import Clock
from flipdot.mode.ScrollText import ScrollText
from flipdot.mode.solid import Black, White
from flipdot.mode.Weather import Weather

__slots__ = [
    "BaseDisplayMode",
    "DisplayModeRef",
    "register_display_mode",
    "get_display_mode",
    "list_display_modes",
]

registry: dict[str, type[BaseDisplayMode]] = {
    "black": Black,
    "white": White,
    "scroll_text": ScrollText,
    "clock": Clock,
    "weather": Weather,
}


def register_display_mode(mode: type[BaseDisplayMode]):
    name = mode.mode_name
    if name in registry:
        raise KeyError(f"Display mode {name} already registered")
    registry[name] = mode


def get_display_mode(name: str) -> type[BaseDisplayMode]:
    if name not in registry:
        raise KeyError(f"Display mode {name} not registered")
    return registry[name]


class DisplayModeList(BaseModel):
    display_modes: dict[str, DisplayModeRef]


def list_display_modes() -> list[DisplayModeRef]:
    return [
        DisplayModeRef(mode_name=name, opts=mode.Options.model_json_schema())
        for name, mode in registry.items()
    ]
