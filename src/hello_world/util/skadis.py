
from typing import List
from ocp_vscode import show, show_all
from build123d import *
from app.hook import skadis_hook

bin_width = 22 * 10 # 30 cm
bin_height_back = 15 * 10 # 15 cm
bin_height_front = 10 * 10 # 10 cm
bin_depth = bin_height_back
bin_wall_thickness = 4 

# Create the bin using a profile.

path: Curve = Curve() + [
    Line((0, 0), (0, bin_depth)),
    Line((0, bin_depth), (bin_height_back, bin_height_back)),
    Line((bin_height_back, bin_height_back), (bin_height_front, 0)),
    Line((bin_height_front, 0), (0, 0)),
]
bin = extrude(make_face(path), bin_width)
bin = bin.fillet(4, bin.edges().filter_by(Axis.X))
# Get the face furthes on the X axis
bin = Rot(Y=270, X=0) * bin.hollow(faces=[bin.faces().sort_by(Axis.X).last], thickness=bin_wall_thickness, kind=Kind.INTERSECTION)

def make_hooks(face: Face, count) -> List[Solid]:
    hook: Part = skadis_hook()
    hook = Plane(face) * Rot(X=90, Y=90) * hook
    per_side = count // 2
    hooks = []
    for i in range(per_side):
        hooks.append(hook.translate((40 * i, 0, 0)))
        hooks.append(hook.translate((-40 * i, 0, 0)))
    for b in range(2):
        hooks.append(hook.translate((40 * b + 20, 0, -20)))
        hooks.append(hook.translate((-40 * b - 20, 0, -20)))
    for b in range(2):
        hooks.append(hook.translate((40 * b + 20, 0, 20)))
        hooks.append(hook.translate((-40 * b - 20, 0, 20)))
    return hooks

hooks = Compound(make_hooks(bin.faces().sort_by(Axis.Y).last, 6))
bin = Compound.make_compound((bin, hooks))

show(bin)
export_stl(bin, "skadis_bin.stl")
