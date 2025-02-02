# Module for adding skadis mounting hooks to any face
from typing import Union, cast
import build123d as bd


class Hook(bd.BasePartObject):
    """
    A hook component for Skadis mounting.

    Parameters:
        hook_sq_len (float): Side length of the hook square (default: 4.8).
        board_thickness (float): Thickness of the board (default: 4.6).
        tolerance (float): Clearance tolerance (default: 0.2).
        end_cap_len (float): Length of the end cap (default: 2.0).
        fillet_radius (float): Radius for filleting the hook edges (default: 0.0, meaning no fillet).
    """

    def __init__(
        self, board_thickness: float = 4.6, tolerance: float = 0.2, end_cap_len: float = 2.0, fillet_radius: float = 0.0
    ):
        hook_sq_len = Hook.width()
        # Ensure we're in a valid build context.
        context: bd.BuildPart | None = bd.BuildPart._get_context(self)
        bd.validate_inputs(context, self)

        # Calculate key dimensions.
        protrusion = board_thickness + tolerance + hook_sq_len / 2
        drop = 9 - end_cap_len

        # Create the sweep path.
        path = bd.Curve([bd.Line((0, 0), (0, protrusion)), bd.Line((0, protrusion), (drop, protrusion))])
        # Create the hook profile. (Assumes bd.Rectangle creates a rectangle centered at the origin.)
        profile = cast(bd.Sketch, bd.Plane.XZ * bd.Rectangle(hook_sq_len, hook_sq_len))

        # Sweep the profile along the path to form the main hook body.
        hook_profile = bd.sweep(profile, path=path, transition=bd.Transition.ROUND)

        # Create an end cap via a loft operation.
        end_face = hook_profile.faces().sort_by(bd.Axis.X).last
        end_plane = bd.Plane(end_face).offset(end_cap_len)
        end_cap_sk = end_plane * bd.Pos(0, -hook_sq_len / 4, 0) * bd.Rectangle(hook_sq_len / 4, hook_sq_len / 4)
        hook_part = hook_profile + bd.loft([bd.Sketch(end_cap_sk), end_face])

        # Rotate the hook into its final orientation.
        # These rotations align the hook with the intended Skadis pegboard layout.
        hook_part = hook_part.rotate(bd.Axis.X, 90).rotate(bd.Axis.Z, 180)

        # Optionally apply a fillet if a positive radius is specified.
        if fillet_radius > 0:
            # This default edge selection is based on sorting edges by the Z axis and filtering by X-position.
            selected_edges = hook_part.edges().sort_by(bd.Axis.Z)[1:].filter_by_position(bd.Axis.X, -100, -1)
            hook_part = bd.fillet(selected_edges, fillet_radius)

        # Re-center the hook so that the attachment point is at the origin.
        attachment_offset = bd.Vector(0, 0, 0)
        hook_part = hook_part.move(bd.Location(-attachment_offset))

        hook_part.label = "SkadisHook"
        super().__init__(hook_part)

    @classmethod
    def width(cls) -> float:
        return 4.8


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

    def __init__(
        self,
        x_count: int,
        y_count: int,
        align: Union[bd.Align, tuple[bd.Align, bd.Align]] = (bd.Align.CENTER, bd.Align.CENTER),
        spacing: int = 40,
        offset: int = 20,
    ):
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
            if self.align[i] == bd.Align.MIN:
                align_offset.append(0.0)
            elif self.align[i] == bd.Align.CENTER:
                align_offset.append(-size[i] / 2)
            elif self.align[i] == bd.Align.MAX:
                align_offset.append(-size[i])
        self.min = bd.Vector(*align_offset)  # bottom left corner
        self.max = self.min + self.size  # top right corner

        # Create local locations.
        # We need to consider the align offset
        local_locations = []
        for i, j in bd.product(range(x_count), range(y_count)):
            shift = 0
            if j % 2 == 1:
                shift = self.offset
            local_locations.append(
                bd.Location(bd.Vector(i * self.spacing + shift + align_offset[0], j * self.spacing + align_offset[1]))
            )

        self.local_locations = bd.Locations._move_to_existing(local_locations)
        self.planes: list[bd.Plane] = []
        super().__init__(self.local_locations)
