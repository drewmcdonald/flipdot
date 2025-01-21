from dataclasses import dataclass
import pathlib
from .DotFont import DotFont

FONTS_DIR = pathlib.Path(__file__).parent / "fonts"


def font_path(font_name: str) -> pathlib.Path:
    return FONTS_DIR / f"{font_name}.ttf"


@dataclass(frozen=True)
class _Fonts:
    axion_6x7: DotFont
    hanover_6x13m: DotFont

    @staticmethod
    def load() -> '_Fonts':
        return _Fonts(
            axion_6x7=DotFont(
                font_path("axion-6x7-dotmap"),
                7,
                space_width=3,
                width_between_chars=1,
            ),
            hanover_6x13m=DotFont(
                font_path("hanover-6x13m-dotmap"),
                13,
                space_width=3,
                width_between_chars=1,
            ),
        )


# Instantiate the immutable Fonts object
fonts = _Fonts.load()

__slots__ = ["fonts", "DotFont"]
