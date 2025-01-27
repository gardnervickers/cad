from typing import cast
import build123d as bd
import hello_world.util.skadis_hook as skadis

def skadis_bin(
    bin_width: int, bin_height_back: int, bin_height_front: int, bin_depth: int, bin_wall_thickness: int
) -> bd.Shape:
    """
    Generates a bin for the Skadis pegboard system.
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

