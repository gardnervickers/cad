import build123d as bd

def low_voltage_xformer():
    """
    Enclosure for my outdoor low voltage transformer.
    """
    width = 23 * 10 # 25 cm
    height = 10 * 10 # 10 cm
    depth = 10 * 10 # 10 cm
    wall_thickness = 4 # 4 mm
    tolerance = 0.1 # 0.1 mm

    box = bd.Box(width, height, depth)
    box_topf = box.faces().sort_by(bd.Axis.Z)[-1]
    box = bd.offset(box, amount=-wall_thickness, openings=box_topf)
    box = box.fillet(wall_thickness, box.edges().filter_by(bd.Axis.Z))

    lid_plane = bd.Plane(box_topf).offset(wall_thickness)
    lid_sk: bd.Rectangle = lid_plane * bd.Rectangle(width, height)
    lid = bd.extrude(lid_sk, wall_thickness, dir=(0, 0, -1))
    # Add a lip to the lid, where the lip is the inner profile of the box. 
    lid_lip_sk = lid_plane.offset(-wall_thickness) * bd.Rectangle(width - tolerance - 2 * wall_thickness, height - tolerance - 2 * wall_thickness)
    lid_lip = bd.extrude(lid_lip_sk, wall_thickness, dir=(0, 0, -1))
    lid += lid_lip
    lid = lid.fillet(wall_thickness, lid.edges().filter_by(bd.Axis.Z))
    # Add a notch to the lid for easy opening on the side faces.
    notch_face = lid.faces().sort_by(bd.Axis.X).first
    notch_plane = bd.Plane(notch_face)
    notch_sk = bd.Sketch([
       notch_plane * bd.Pos((0, 1, 0)) * bd.Rectangle(height / 2, wall_thickness - 1),
    ])
    notch = bd.extrude(notch_sk, wall_thickness / 2, dir=(1, 0, 0))
    notch += bd.mirror(notch, bd.Plane(box_topf))
    lid -= notch
    box -= notch

    # Lastly, we will slot in some holes for wires on the other side of the box.
    hole_face = lid.faces().sort_by(bd.Axis.X).last
    hole_plane = bd.Plane(hole_face)
    hole = hole_plane * bd.Pos((0, -9.5, 0))* bd.Rectangle(30, 15)
    hole = bd.extrude(hole, wall_thickness * 4, dir=(-1, 0, 0))
    box -= hole
    lid -= hole

    return [box, lid]
