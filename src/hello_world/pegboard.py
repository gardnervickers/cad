from math import floor
from typing import cast
import build123d as bd
import hello_world.util.skadis_hook as skadis
#from yacv_server import show, clear


def skadis_bin(
    bin_width: int, bin_height_back: int, bin_height_front: int, bin_depth: int, bin_wall_thickness: int
) -> bd.Shape:
    """
    Generates a bin for the Skadis pegboard system. This is a square bin. 
    :param bin_width: The width of the bin.
    :param bin_height_back: The height of the back of the bin.
    :param bin_height_front: The height of the front of the bin. The front can be made to be lower than the back to make it easier to see the contents.
    :param bin_depth: The depth of the bin.
    :param bin_wall_thickness: The thickness of the bin walls.
    :return: The bin.
    """
    # Create the bin using a profile.
    bd.Sketch(None)
    path = bd.Curve(
        [
            bd.Line((0, 0), (0, bin_depth)),
            bd.Line((0, bin_depth), (bin_height_back, bin_depth)),
            bd.Line((bin_height_back, bin_depth), (bin_height_front, 0)),
            bd.Line((bin_height_front, 0), (0, 0)),
        ]
    )
    prof = bd.make_face(path.edges())
    bin = bd.extrude(prof, bin_width)
    bin = bin.fillet(4, bin.edges().filter_by(bd.Axis.X))
    # Get the face furthest on the X Axis
    bin = bd.Rot(Y=270, X=0) * bin.hollow(
        faces=[bin.faces().sort_by(bd.Axis.X).last], thickness=bin_wall_thickness, kind=bd.Kind.ARC
    )
    # Make some hooks
    hook_face = bin.faces().sort_by(bd.Axis.Y).last
    hook_plane = bd.Plane(hook_face)
    hook = skadis.Hook().rotate(bd.Axis.Y, 90)
    hook_locs = cast(skadis.HookLocations, hook_plane * skadis.HookLocations(2, 2, spacing=40))
    hooks = bd.Compound([loc * hook for loc in hook_locs])
    bin = bd.Compound.make_compound((bin, hooks))
    return bin



def grid_for_face(face: bd.Face, shape: bd.Sketch, gap: float) -> bd.Sketch:
    """
    Create a grid which covers the supplied face with the given shape.

    Args:
        face (bd.Face): The face to cover.
        shape (bd.Sketch): The shape to use in the grid.
        gap (float): The min gap between shapes in the grid.

    Returns:
        bd.Sketch: A sketch containing the grid of shapes covering the face.
    """
    if not face.is_planar:
        raise ValueError("Face must be planar")

    # Get the face's local plane
    face_plane = bd.Plane(face)

    # Measure the face's dimensions in its local coordinate system
    face_bb = face.bounding_box()
    face_local_min = face_plane.to_local_coords(face_bb.min)
    face_local_max = face_plane.to_local_coords(face_bb.max)
    face_width = face_local_max.X - face_local_min.X
    face_height = face_local_max.Y - face_local_min.Y

    # Measure the shape's dimensions in its local coordinate system
    shape_bb = shape.bounding_box()
    shape_width = shape_bb.max.X - shape_bb.min.X
    shape_height = shape_bb.max.Y - shape_bb.min.Y
    shape_width += 2 * gap
    shape_height += 2 * gap

    # Ensure the shape has non-zero dimensions
    if shape_width <= 0 or shape_height <= 0:
        raise ValueError("Shape must have non-zero width and height")
    # Calculate the number of rows and columns needed
    cols = int(floor(face_width // shape_width)) + 1
    rows = int(floor(face_height // shape_height)) + 1

    # Create the grid in the face's local coordinate system
    grid = bd.GridLocations(
        x_spacing=shape_width,
        y_spacing=shape_height,
        x_count=cols,
        y_count=rows,
        align=(bd.Align.CENTER, bd.Align.CENTER),
    )

    # Apply the grid to the shape in local coordinates
    shapes = [loc * shape for loc in grid]

    # Combine the shapes into a single sketch
    result = bd.Sketch(shapes)

    # Transform the result back to the global coordinate system
    return face_plane * result

def rounded_bin(face_pattern: bd.Sketch = bd.RegularPolygon(radius=6, side_count=6)) -> bd.Solid:
    bin_width = 200 
    circle_radius = 20 
    bin_height = 50 
    bin_thickness = 2
    gap = 2  # gap between patterns 

    bin_base_prof = bd.RectangleRounded(
        width=bin_width,
        height=circle_radius * 2 + 0.1,  # Height of the profile
        radius=circle_radius,
        align=(bd.Align.CENTER, bd.Align.CENTER)  # Center the rectangle
    )
    bin = bd.extrude(bin_base_prof, bin_height, dir=(0,0,1))
    bin = bin.hollow(faces=[bin.faces().sort_by(bd.Axis.Z).last], thickness=bin_thickness)
    bin = bin.solid()

    bin_f: bd.Face = bin.faces().sort_by(bd.Axis.Y).first
    # Shrink the face by 2mm to ensure the pattern does not overlap the edges 
    shrunk_f = bd.offset(bin_f, -4).face()
    # Generate a face for cutting
    cut_face = grid_for_face(shrunk_f, face_pattern, gap)
    cut_ex = bd.extrude(cut_face, bin_thickness + 0.01, dir=(0,1,0), mode=bd.Mode.ADD)
    cut_ex = cut_ex.translate((0, -0.01, 0))
    bin -= cut_ex

    # Next we will put some hooks on the back.
    hook = skadis.Hook()
    hook = hook.rotate(bd.Axis.Y, 90).rotate(bd.Axis.Z, -90)
    hook_plane = bd.Plane(bin.faces().sort_by(bd.Axis.Y).last)
    hook_locs = cast(skadis.HookLocations, hook_plane * skadis.HookLocations(3, 2))
    hooks = bd.Compound([loc * hook for loc in hook_locs])
    bin += hooks
    return bin 

def shelf(width: float, depth: float, thickness: float) -> bd.Solid:
    """
    Create a shelf with the given dimensions and skadis support hooks located on triangular
    supports on the back of the shelf.
    """




