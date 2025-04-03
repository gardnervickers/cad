import random
from build123d.build_common import GridLocations
from build123d.operations_generic import offset
from ocp_vscode import set_port, show, show_all
import build123d as bd
import bd_warehouse.thread as threads
from math import ceil, cos, pi, sin
import numpy as np
import scipy.spatial as sp

set_port(3939)
tolerance = 0.1 * bd.MM


def table():
    table_top_diameter = 35 * bd.CM
    table_top_radius = table_top_diameter / 2
    table_height = 80 * bd.CM
    table_column_diamater = 5 * bd.CM
    table_column_radius = table_column_diamater / 2

    with bd.BuildPart() as part:
        with bd.BuildSketch() as sk_1:
            with bd.BuildLine() as ln_1:
                top = bd.Line((0, 0), (table_top_radius, 0))
                center = bd.Line(top @ 1, bd.Pos(Y=-table_height) * top @ 1)
                bottom = bd.Line(center @ 1, bd.Pos(X=-table_column_radius) * center @ 1)
                # side1 = bd.Line(bottom @ 1, bd.Pos(Y=table_height * 0.5) * bottom @ 1)
                c_start = top @ 0
                c_stop = bottom @ 1
                curve = bd.TangentArc((c_start, c_stop), tangent=center @ 0.5)
            bd.make_face()
            bd.fillet(sk_1.vertices().sort_by(bd.Axis.X)[0:1], 8 * bd.MM)
        bd.revolve(axis=bd.Axis(center))


def hexify(
    face: bd.Face | None = None,
    cell_size: float | None = 10.0,
    cell_width: float = 1.0,
    gap: float = 2.0,
) -> bd.Face:
    context: bd.BuildSketch | None = bd.BuildSketch._get_context()
    # Normalize the face by mapping it to the XY plane
    if face is None:
        if context is not None:
            face = context.sketch_local.face()
        else:
            raise ValueError("No face provided")
    face_bb: bd.BoundBox = face.bounding_box()
    face_size = face_bb.diagonal / 2
    hex_plate = bd.Plane(face) * bd.Rectangle(face_size * 2, face_size * 2)
    print("face_size", face_size)
    # Translate to the face coordinate system
    hex_locations = bd.HexLocations(
        cell_size + gap,
        ceil(face_size / cell_size),
        ceil(face_size / cell_size),
        major_radius=True,
    )
    hex_locations = bd.Plane(hex_plate.face()) * hex_locations
    poly = bd.RegularPolygon(cell_size, 6)
    hex_wires = hex_locations * poly
    hex_outline = hex_plate - hex_wires
    # Invert the hex plate to get the holes
    hex_plate = hex_plate - hex_outline
    hex_plate = hex_plate.intersect(face)
    return hex_plate


def rod():
    ## Testing out threads.
    thread = threads.IsoThread(major_diameter=5, pitch=2, length=15, align=bd.Align.CENTER)
    bolt_body = bd.Cylinder(thread.min_radius, 20)
    # Create a nut
    # nut_hole = bd.Cylinder(5 * 2, 5)

    size = 32
    stepheight = 2
    thickness = 4
    thread = (24, 2)

    sketch = bd.Sketch()
    sketch += bd.RegularPolygon(radius=size / 2, side_count=6, major_radius=False)
    sketch -= bd.Circle(thread[0] / 2)
    nut_blank = bd.extrude(sketch, amount=thickness)
    topf = nut_blank.faces().sort_by(bd.Axis.Z)[-1]
    sketch = bd.Sketch()
    sketch += bd.Circle(size / 2)
    sketch -= bd.Circle(thread[0] / 2)
    sketch = bd.Plane(topf) * sketch
    nut_blank += bd.extrude(sketch, amount=stepheight)
    id_thread = threads.IsoThread(
        major_diameter=thread[0] * 1.05,
        pitch=thread[1],
        length=thickness + stepheight,
        end_finishes=("square", "square"),
        external=False,
    )
    nut = bd.Compound([nut_blank, id_thread])

    # Rod time
    rod_thread = threads.IsoThread(
        major_diameter=thread[0], pitch=thread[1], length=size * 0.6, end_finishes=("square", "square"), external=True
    )
    sketch = bd.Sketch()
    sketch += bd.Circle(rod_thread.min_radius)
    rod_blank = bd.extrude(sketch, amount=rod_thread.length)
    topf = rod_blank.faces().sort_by(bd.Axis.Z)[-1]
    sketch = bd.Sketch()
    sketch += bd.Circle(size / 2)
    sketch = bd.Plane(topf) * sketch
    rod_blank = rod_blank + bd.extrude(sketch, amount=size * 0.5)
    rod = bd.Compound([rod_blank, rod_thread])


def ex():
    ball_diameter = 25
    ball_radius = ball_diameter / 2
    truncation_amount = 5

    ball_sk = bd.Sketch() + bd.Circle(ball_radius)
    top_plane = bd.Plane(origin=(0, ball_radius - truncation_amount, 0), z_dir=(0, 1, 0))
    bottom_plane = bd.Plane(origin=(0, -ball_radius + truncation_amount, 0), z_dir=(0, 1, 0))
    ball_sk = ball_sk.split(top_plane, keep=bd.Keep.BOTTOM)
    ball_sk = ball_sk.split(bottom_plane, keep=bd.Keep.TOP)
    ball_sk = ball_sk.split(bd.Plane.ZY)
    ball = bd.revolve(ball_sk, axis=bd.Axis.Y)
    show_all()


dim, thickness = 25.4 * bd.MM, 2.0 * bd.MM
od = dim + thickness

def sq_tube(length: float):
    """
    Creates a square tube with the given dimension. Defaults to 1 inch.
    """
    sk = bd.Sketch()
    outer = bd.Rectangle(dim, dim)
    inner = bd.offset(outer, -thickness)
    sk += outer
    sk -= inner
    return bd.extrude(sk, amount=length)

def l_bracket(lip: float = 10 * bd.MM):
    """
    Creates a simple L bracket with a lip.
    """
    sk = bd.Sketch()
    sk += bd.Rectangle(od, od + lip, align=(bd.Align.MIN, bd.Align.MAX))
    sk += bd.Pos(Y=-od) * bd.Rectangle(od + lip, od, align=(bd.Align.MIN, bd.Align.MIN))
    bracket = bd.extrude(sk, amount=od) 
    f1 = bracket.faces().sort_by(bd.Axis.Y).first
    f2 = bracket.faces().sort_by(bd.Axis.X).last
    f1_inner = bd.offset(f1, -thickness)
    f2_inner = bd.offset(f2, -thickness)
    f1_inner = bd.extrude(f1_inner, amount=lip * 2, dir=(0, 1, 0))
    bracket -= f1_inner
    f2_inner = bd.extrude(f2_inner, amount=lip * 2, dir=(-1, 0, 0))
    bracket -= f2_inner
    return [bracket]

def points_on_circle(radius: float, count: int) -> list[bd.Pos]:
    """
    Returns a list of points on a circle with the given radius and number of points.
    """
    points = []
    for i in range(count):
        angle = 2 * pi * i / count
        x = radius * cos(angle)
        y = radius * sin(angle)
        points.append(bd.Pos(X=x, Y=y))
    return points

def mosquito_coil_holder():
    """
    Holds mosquito citronella coils.
    """
    inner_diameter = 10 * bd.CM
    wall_thickness = 4 * bd.MM
    outer_diameter = inner_diameter + wall_thickness * 2
    height = 8 * bd.CM
    center_guide = 4 * bd.MM
    center_guide_height = 1 * bd.CM

    body = bd.Cylinder(outer_diameter / 2, height, align=bd.Align.MIN)
    top_f = body.faces().sort_by(bd.Axis.Z)[-1]
    top_sk = bd.Sketch()
    top_sk += bd.Circle(inner_diameter / 2)
    top_sk = bd.Plane(top_f) * top_sk 
    body -= bd.extrude(top_sk, amount=height - wall_thickness, dir=(0, 0, -1))
    inner_f = body.faces().filter_by(lambda f: f.is_planar_face).sort_by(bd.Axis.Z)[1]
    center_guide = bd.Plane(inner_f) * bd.Circle(center_guide / 2)
    body += bd.extrude(center_guide, amount=center_guide_height, dir=(0, 0, 1))
    top_edges = body.edges().sort_by(bd.Axis.Z, reverse=True)[1:6]
    body = body.fillet(2, top_edges)
    bottom_edges = body.edges().sort_by(bd.Axis.Z)[0:1]
    body = body.fillet(2, bottom_edges)

    # Lets make the lid.
    lid =  bd.Cylinder(outer_diameter / 2, wall_thickness)
    lid_lip_plane = bd.Plane(lid.faces().sort_by(bd.Axis.Z).first)
    lid_inner_sk = bd.Sketch()
    lid_inner_sk += bd.Circle(inner_diameter / 2)
    lid_inner_sk = lid_lip_plane * lid_inner_sk
    lid_lip_end_plane = lid_lip_plane.offset(wall_thickness)
    lid_lip_end = lid_lip_end_plane * bd.Circle((inner_diameter / 2) - wall_thickness)
    lip_loft = bd.loft([lid_inner_sk, lid_lip_end])
    lid += lip_loft


    lid_plane = bd.Plane(top_f).offset(10)
    lid = lid_plane * lid

    # Fillet out the lid.
    fillet_edges = []
    fillet_edges.append(lid.edges().sort_by(bd.Axis.Z).last)
    fillet_edges.append(lid.edges().sort_by(bd.Axis.Z).first)
    lid = lid.fillet(2, fillet_edges)

    # Add some feet to the bottom of the body.

    bottom_plane = bd.Plane(body.faces().sort_by(bd.Axis.Z).first)
    # Make a circle for which to place the feet. We'll use the circle to find the 3 equidistant points
    # for the feet.
    # Get the center of the circle.
    points = []
    sk = bd.Sketch()
    r = ((inner_diameter / 2) - wall_thickness * 2)
    points = points_on_circle(r, 3)
    for point in points:
        sk += point * bd.Circle(2) 
    sk = bottom_plane * sk
    feet = bd.extrude(sk, amount=wall_thickness / 2, dir=(0, 0, -1)) 
    body += feet
    feet_edges = body.edges().sort_by(bd.Axis.Z)[0:3]
    body = body.fillet(1.5, feet_edges)

    outer_face = body.faces().filter_by(lambda f: not f.is_planar_face).sort_by(lambda f: f.area).last


    cnt = 40 
    z = 10 
    circles = []
    for zz in range(z):
        if zz == 0:
            continue
        for i in range(cnt):
            position = outer_face.position_at(i / cnt, zz / z)
            normal = outer_face.normal_at(i / cnt, zz/z)
            loc = bd.Location(bd.Plane(position, z_dir=normal))
            circles.append(loc * bd.Sphere(2))
    lid.label = "lid"
    body.label = "body"

    return [lid, body, circles]

res = mosquito_coil_holder()

#bd.export_step(lid, "mosquito_coil_holder_lid.step")
#bd.export_step(body, "mosquito_coil_holder_body.step")
show(res)
