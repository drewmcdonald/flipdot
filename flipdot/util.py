from flipdot.types import DotMatrix


def prettify_dot_matrix(dot_matrix: DotMatrix) -> str:
    return "\n".join(
        "".join("🟨" if cell else "⬛" for cell in row) for row in dot_matrix
    )
