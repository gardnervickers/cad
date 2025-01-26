# Module for adding skadis mounting hooks to any face
from typing import List, Union
import build123d as bd

HOOK_SQ_LEN = 4.8
BOARD_THICKNESS = 4.6
TOLERANCE = 0.2
COLUMN_SPACING = 40
ROW_SPACING = 40
END_CAP_LEN = 2


def skadis_hook() -> bd.Part:
    """Create an Ikea Skadis hook with proper type annotations."""
    protrusion = BOARD_THICKNESS + TOLERANCE + HOOK_SQ_LEN / 2
    drop = 9 - END_CAP_LEN

    # Path construction
    path = bd.Curve([bd.Line((0, 0), (0, protrusion)), bd.Line((0, protrusion), (drop, protrusion))])

    # Profile and sweep
    profile = bd.Plane.XZ * bd.RectangleRounded(HOOK_SQ_LEN, HOOK_SQ_LEN, 0.4)
    hook_profile = bd.sweep(profile, path=path, transition=bd.Transition.ROUND)

    # End cap construction
    end_face = hook_profile.faces().sort_by(bd.Axis.X).last
    end_plane = bd.Plane(end_face).offset(END_CAP_LEN)
    end_cap_sk = end_plane * bd.Pos(0, -HOOK_SQ_LEN / 4, 0) * bd.RectangleRounded(HOOK_SQ_LEN / 4, HOOK_SQ_LEN / 4, 0.2)

    return (hook_profile + bd.loft([end_cap_sk, end_face])).rotate(bd.Axis.Y, 90)


def skadis_hook_pattern_row(row: int, columns: int) -> List[tuple[float, float]]:
    column_spacing = 40
    points = []
    shift = 0
    if row % 2 == 1:
        shift = 20
    for column in range(columns):
        points.append((column * column_spacing + shift, row * column_spacing))
    return points


# Returns an array of points following the skadis hook
# pattern in 2d.
def skadis_hook_pattern(columns: int, rows: int) -> List[List[tuple[float, float]]]:
    # Each row is a list of points seperated by column_spacing
    # Each row is seperated by row_spacing, with each odd row offset by row_offset.
    points = []
    for row in range(rows):
        points.append(skadis_hook_pattern_row(row, columns))
    return points


def make_hooks(face: bd.Face, count: int, skip=0) -> bd.Compound:
    """Create a grid of hooks aligned to a face with proper transformations."""
    hook = skadis_hook()
    per_side = count // 2

    # Generate translation vectors
    translations = []
    for i in range(per_side):
        if i % skip == 0:
            continue
        translations.extend([(COLUMN_SPACING * i, 0, 0), (-COLUMN_SPACING * i, 0, 0)])
    for b in range(per_side):
        if b % skip == 0:
            continue
        translations.extend(
            [
                (COLUMN_SPACING * b + 20, 0, -20),
                (-COLUMN_SPACING * b - 20, 0, -20),
                (COLUMN_SPACING * b + 20, 0, 20),
                (-COLUMN_SPACING * b - 20, 0, 20),
            ]
        )

    # Create and transform hooks
    hooks = [hook.translate(t) for t in translations]
    return bd.Plane(face) * bd.Rot(X=90, Y=90) * bd.Compound(hooks)

