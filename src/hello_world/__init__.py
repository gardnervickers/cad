# Open up http://127.0.0.1:32323/ for an interactive 3d model viewer
import build123d as bd
import yacv_server as yacv
import hello_world.util.skadis_hook as skadis

yacv.yacv.startup_complete.wait()

def skadis_bin(bin_width: int, bin_height_back: int,
               bin_height_front: int, bin_depth: int, bin_wall_thickness: int) -> bd.Shape:
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
    hooks = skadis.make_hooks(hook_face, 6, skip=2)
    bin = bd.Compound.make_compound((bin, hooks))
    return bin


# We are going to make a nice skadis bin
# It will be rounded at the bottom and sit out at
# a 45 degree angle.
def display() -> bd.List[bd.Shape]:
    bin_width = 22 * 10  
    bin_height_back = 15 * 10  # 15 cm
    bin_height_front = 10 * 10  # 10 cm
    bin_depth = bin_height_front
    bin_wall_thickness = 4
    bin = skadis_bin(bin_width, bin_height_back, bin_height_front, bin_depth, bin_wall_thickness)
    return [bin] 

#yacv.clear()
yacv.show(display())
#bd.export_step(display()[0], "skadis_bin.step")
