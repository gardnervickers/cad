from math import floor
from typing import cast
import build123d as bd
import hello_world.util.skadis_hook as skadis
from yacv_server import show


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
    face_local_min: bd.Vector = cast(bd.Vector, face_plane.to_local_coords(face_bb.min))
    face_local_max: bd.Vector = cast(bd.Vector, face_plane.to_local_coords(face_bb.max))
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
    return cast(bd.Sketch, face_plane * result)

def rounded_bin(face_pattern: bd.Sketch = bd.RegularPolygon(radius=6, side_count=6)) -> bd.Solid:
    bin_width = 150 
    circle_radius = 25 
    bin_height = 110 
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
    shrunk_f = bd.offset(bin_f, -8).face()
    # Generate a face for cutting
    cut_face = grid_for_face(shrunk_f, face_pattern, gap)
    cut_ex = bd.extrude(cut_face, bin_thickness + 0.01, dir=(0,1,0), mode=bd.Mode.ADD)
    cut_ex = cut_ex.translate((0, -0.01, 0))
    bin -= cut_ex

    # Next we will put some hooks on the back.
    hook = skadis.Hook()
    hook = hook.rotate(bd.Axis.Y, 90).rotate(bd.Axis.Z, -90)
    hook_plane = bd.Plane(bin.faces().sort_by(bd.Axis.Y).last)
    hook_locs = cast(skadis.HookLocations, hook_plane * skadis.HookLocations(3, 1))
    hooks = bd.Compound([loc * hook for loc in hook_locs])
    bin += hooks
    return bin 

def shelf_not_working():
    # Alright now lets make a shelf generator. My build volume is 256mm x 256mm x 256mm, so
    # the shelf needs to be smaller than that. Additionally if the skadis hook pattern is 
    # offset every 40mm, then the shelf needs to be a multiple of 40mm. 
    #max_width = floor(256 / 40) * 40

    # The shelf has two parts, the flat piece that items sit on and the triangular supports 
    # which have the skadis hooks on them. 

    hook = skadis.Hook()

    # the depth of the support. This is going to be the length of the longest side of the triangle.
    # It meets the back piece of the support at a right angle. 
    support_depth = 100
    # The height of the support, which attaches to the pegboard. This needs to hold at least 2 hooks,
    # so the min height is going to be 40mm + the hook size. 
    support_height = 40
    support_width = hook.width() 

    # Make support profile
    support_sk: bd.Sketch = bd.Sketch(None)
    support_prof = bd.Triangle(b = support_depth, a = support_height, B=90)
    support_sk += support_prof
    support_inner_prof = bd.offset(support_prof, -support_width)
    support_inner_prof = bd.fillet(support_inner_prof.vertices(), 2)
    support_sk -= support_inner_prof
    support_sk = cast(bd.Sketch, bd.fillet([support_sk.vertices().sort_by(bd.Axis.Y).last], 2))

    # Extrude the support. 
    support_body = bd.extrude(support_sk, support_width)
    support_hook_face = support_body.faces().sort_by(bd.Axis.Y).first
    return support_hook_face
    #support_body += bd.Plane(support_hook_face) * bd.Pos(((support_height * -0.5) + (support_width * 0.5), 0, 0)) * skadis.Hook().rotate(bd.Axis.Y, 90).rotate(bd.Axis.Z, 180)
    # Attach the hooks.


def parts_bin(hook_count: int, base_depth: float, base_height: float = 20, thickness = 2, vtx_shift: float = 0):
    """
    Create a small parts bin which can be placed side-by-side with other bins. 
    :param hook_count: The number of hooks on the front of the bin. This determines the width of the bin,
    :param base_depth: The depth of the bin, from the front to the back.
    :param base_height: The height of the bin, from the top to the bottom.
    :param thickness: The thickness of the bin walls. 
    :param vtx_shift: The amount to shift the vertex of the triangle. This can produce angled front lips which
                      is aesthetically pleasing.
    """
    if hook_count < 1:
        raise ValueError("hook_count must be greater than 0")
    # bins are placed on a pegboard with 40mm spacing. We want bins to be adjacent to each other,
    # so the max width of a bin is 40mm * hook_count. There is some additional space needed to handle
    # the thickness of the hooks. We will overhang each side by 20mm, this should be enough to place
    # bins  next to each other.
    gap = 2
    bin_width: float = (40 * hook_count) - (2 * thickness) - gap
    base_sketch = bd.Sketch(None)
    top_line = bd.Line((0, 0), (0, base_depth))
    vtx = bd.Vector((-base_height, vtx_shift, 0))  
    front_line = bd.Line((0, 0), vtx)
    back_line1 = bd.Line(vtx, (vtx.X, base_depth))
    back_line2 = bd.Line((vtx.X, base_depth), (0, base_depth))
    base_curve = bd.Curve([
        top_line,
        front_line,
        back_line1,
        back_line2
    ])

    base_sketch += bd.make_face(base_curve.edges())
    base_ex = bd.extrude(base_sketch, bin_width)
    inner_base = bd.offset(base_ex, thickness * -1)
    inner_base += bd.extrude(inner_base.faces().sort_by(bd.Axis.X).last, 2 * thickness)
    inner_base = bd.fillet(inner_base.edges(), thickness)
    base = base_ex - inner_base

    hooks = bd.Part(None)
    hook_pattern = skadis.HookLocations(hook_count, 1)
    hook = skadis.Hook().rounded()
    hook = bd.Rot(Y = 90) * bd.Rot(X = 90) * hook
    for loc in hook_pattern:
        hooks += loc * hook

    back_face = base.faces().sort_by(bd.Axis.Y).last
    back_face_len = back_face.edges().sort_by(bd.SortBy.LENGTH).first.length
    # Shift the hooks so they are at the top of the face. If the len is 10, 
    # and hook width is 3, we know the hooks start at 5, so we need to shift up
    # by 2. The formula is thus (back_face_len / 2) - (hook width / 2)
    hook_shift = (back_face_len / 2) - (skadis.Hook.width() / 2) 
    hooks = bd.Plane(back_face) * bd.Rot(Z=90) * bd.Pos(Y=-hook_shift) * hooks
    bin = bd.Compound([base, hooks])
    return bin 

#bins = []
#for i in range(1, 4):
#    bin = parts_bin(i, 80, vtx_shift=10)
#    bins.append(bd.Rot(Y=270) * bin)
#    bd.export_step(bin, f"parts_bin_{i}.step")
#
#bins = bd.pack(bins, padding=4)
#show(bins)


