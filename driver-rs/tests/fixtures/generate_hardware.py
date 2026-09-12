"""
Regenerate byte-for-byte hardware output fixtures.

Run from repo root:
    PYTHONPATH=. poetry run python driver-rs/tests/fixtures/generate_hardware.py

These fixtures lock in the exact bytes the Python driver sends over serial
for a set of known matrix inputs. The Rust port must produce identical
bytes for the same inputs.
"""

from __future__ import annotations

import json
from pathlib import Path

from flipdot.hardware import Panel, pack_bits_little_endian

FIXTURES = Path(__file__).parent


def write(name: str, payload: object) -> None:
    path = FIXTURES / name
    path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {path.relative_to(FIXTURES.parent.parent.parent)}")


def blank(h: int, w: int) -> list[list[int]]:
    return [[0] * w for _ in range(h)]


def all_on(h: int, w: int) -> list[list[int]]:
    return [[1] * w for _ in range(h)]


def checker(h: int, w: int) -> list[list[int]]:
    return [[(r + c) & 1 for c in range(w)] for r in range(h)]


def corners_only(h: int, w: int) -> list[list[int]]:
    m = blank(h, w)
    m[0][0] = 1
    m[0][w - 1] = 1
    m[h - 1][0] = 1
    m[h - 1][w - 1] = 1
    return m


def gen_panel_cases() -> list[dict[str, object]]:
    cases: list[dict[str, object]] = []
    # Standard 28x14 layout (two stacked modules, addresses 1 and 2)
    layout = [[1], [2]]
    for name, matrix in [
        ("blank_28x14", blank(14, 28)),
        ("all_on_28x14", all_on(14, 28)),
        ("checker_28x14", checker(14, 28)),
        ("corners_only_28x14", corners_only(14, 28)),
    ]:
        panel = Panel(layout=layout, module_width=28, module_height=7)
        serial_bytes = panel.set_content(matrix)
        cases.append({
            "name": name,
            "layout": layout,
            "module_width": 28,
            "module_height": 7,
            "matrix": matrix,
            "expected_hex": serial_bytes.hex(),
        })

    # Side-by-side 56x7 layout (one row, addresses 1 and 2)
    layout2 = [[1, 2]]
    matrix2 = checker(7, 56)
    panel2 = Panel(layout=layout2, module_width=28, module_height=7)
    cases.append({
        "name": "checker_56x7_side_by_side",
        "layout": layout2,
        "module_width": 28,
        "module_height": 7,
        "matrix": matrix2,
        "expected_hex": panel2.set_content(matrix2).hex(),
    })

    return cases


def gen_pack_bits_cases() -> list[dict[str, object]]:
    cases: list[dict[str, object]] = []
    for name, bits in [
        ("empty", []),
        ("single_bit_0", [1]),
        ("eight_alternating", [1, 0, 1, 0, 1, 0, 1, 0]),
        ("nine_bits_last_on", [0, 0, 0, 0, 0, 0, 0, 0, 1]),
        ("twelve_all_on", [1] * 12),
    ]:
        cases.append({
            "name": name,
            "bits": bits,
            "expected_hex": pack_bits_little_endian(bits).hex(),
        })
    return cases


def main() -> None:
    write("hardware_panel_cases.json", gen_panel_cases())
    write("hardware_pack_bits_cases.json", gen_pack_bits_cases())


if __name__ == "__main__":
    main()
