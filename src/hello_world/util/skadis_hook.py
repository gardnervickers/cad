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

class SkadisLocations(bd.LocationList):
    """Location Context: Hook placement matching the Ikea Skadis pattern

    Creates a context of grid location for a Part or Sketch
    x_count (int): number of horizontal points
    y_count (int): number of vertical points
    align (Union[Align, tuple[Align, Align]]): align min, center or max of object
        Defaults to (Align.CENTER, Align.CENTER)

    Example:
        locations = SkadisLocations(3, 4, align=Align.CENTER)
        test = []
        for loc in iter(locations):
            hook = skadis.skadis_hook()
            test.append(hook.rotate(bd.Axis.X, 90).move(loc))
    """
    def __init__(self, x_count: int, y_count: int, 
                 align: Union[bd.Align, tuple[bd.Align, bd.Align]] = (bd.Align.CENTER, bd.Align.CENTER),
                 spacing: int = 40,
                 offset: int = 20):
        self.x_count = x_count
        self.y_count = y_count
        self.align = bd.tuplify(align, 2)
        self.spacing = spacing 
        self.offset = offset 
        # Determine the grid size. If there is more than one row, then we add 
        # an offset to the X axis of _offset_.
        size = [self.spacing * (self.x_count - 1), self.spacing * (self.y_count - 1)]
        if self.y_count > 1:
            size[0] += self.offset
        self.size = bd.Vector(*size)
        align_offset = []
        for i in range(2):
            if self.align[1] == bd.Align.MIN:
                align_offset.append(0.0)
            elif self.align[i] == bd.Align.CENTER:
                align_offset.append(size[i] / 2)
            elif self.align[i] == bd.Align.MAX:
                align_offset.append(-size[i])
        self.min = bd.Vector(*align_offset) # bottom left corner
        self.max = self.min + self.size # top right corner

        # Create local locations.
        local_locations = []
        for y in range(y_count):
            shift = 0
            if y % 2 == 1:
                shift = self.offset
            for x in range(x_count):
                local_locations.append(bd.Location(bd.Vector(x * self.spacing + shift, y * self.spacing)))
        self.local_locations = bd.Locations(local_locations).local_locations
        self.planes: list[bd.Plane] = []
        super().__init__(self.local_locations)

