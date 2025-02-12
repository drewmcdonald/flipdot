import pathlib

from pydantic import BaseModel

from flipdot.font.DotFont import DotFont, DotFontRef

FONTS_DIR = pathlib.Path(__file__).parent / "fonts"


def font_path(font_name: str) -> pathlib.Path:
    return FONTS_DIR / f"{font_name}.ttf"


registry = {
    "axion_6x7": DotFont(
        font_path("axion-6x7-dotmap"),
        7,
        space_width=3,
        width_between_chars=1,
    ),
    "cg_pixel_4x5": DotFont(
        font_path("cg-pixel-4x5"),
        5,
        space_width=2,
        width_between_chars=1,
    ),
    "hanover_6x13m": DotFont(
        font_path("hanover-6x13m-dotmap"),
        13,
        space_width=3,
        width_between_chars=1,
    ),
    "twinvision_4x6": DotFont(
        font_path("twinvision-4x6-dotmap"),
        6,
        space_width=2,
        width_between_chars=1,
    ),
}


def get_font(font_name: str) -> DotFont:
    try:
        return registry[font_name]
    except KeyError as e:
        raise ValueError(f"Font {font_name} not found") from e


def register_font(
    font_name: str,
    font_path: pathlib.Path,
    src_height: int,
    space_width: int,
    width_between_chars: int,
):
    if font_name in registry:
        raise ValueError(f"Font {font_name} already registered")
    registry[font_name] = DotFont(
        font_path,
        src_height,
        space_width,
        width_between_chars,
    )


class FontList(BaseModel):

    fonts: dict[str, DotFontRef]


def list_fonts() -> FontList:
    return FontList(fonts={name: font.to_ref() for name, font in registry.items()})
