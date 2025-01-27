# Module for adding skadis mounting hooks to any face
from typing import Union, cast
import build123d as bd

HOOK_SQ_LEN = 4.8
BOARD_THICKNESS = 4.6
TOLERANCE = 0.2
COLUMN_SPACING = 40
ROW_SPACING = 40
END_CAP_LEN = 2

class Hook(bd.BasePartObject):
    def __init__(self):
        protrusion = BOARD_THICKNESS + TOLERANCE + HOOK_SQ_LEN / 2
        drop = 9 - END_CAP_LEN
        # Path construction
        path = bd.Curve([bd.Line((0, 0), (0, protrusion)), bd.Line((0, protrusion), (drop, protrusion))])
        profile = cast(bd.Sketch, bd.Plane.XZ * bd.RectangleRounded(HOOK_SQ_LEN, HOOK_SQ_LEN, 0.4))
        hook_profile: bd.Part = cast(bd.Part, bd.sweep(profile, path=path, transition=bd.Transition.ROUND))
        end_face = hook_profile.faces().sort_by(bd.Axis.X).last
        end_plane = bd.Plane(end_face).offset(END_CAP_LEN)
        end_cap_sk = end_plane * bd.Pos(0, -HOOK_SQ_LEN / 4, 0) * bd.RectangleRounded(HOOK_SQ_LEN / 4, HOOK_SQ_LEN / 4, 0.2)
        obj = (hook_profile + bd.loft([bd.Sketch(end_cap_sk), end_face])).rotate(bd.Axis.X, -90).rotate(bd.Axis.Y, 90)
        obj.label = "SkadisHook"
        super().__init__(obj)

class HookLocations(bd.LocationList):
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
                align_offset.append(-size[i] / 2)
            elif self.align[i] == bd.Align.MAX:
                align_offset.append(-size[i])
        self.min = bd.Vector(*align_offset) # bottom left corner
        self.max = self.min + self.size # top right corner

        # Create local locations.
        # We need to consider the align offset 
        local_locations = []
        for i, j in bd.product(range(x_count), range(y_count)):
            shift = 0
            if j % 2 == 1:
                shift = self.offset
            local_locations.append(bd.Location(bd.Vector(i * self.spacing + shift + align_offset[0], j * self.spacing + align_offset[1])))

        self.local_locations = bd.Locations._move_to_existing(local_locations)
        self.planes: list[bd.Plane] = []
        super().__init__(self.local_locations)

