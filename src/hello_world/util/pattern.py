import build123d as bd

def locations_on_face_edge(face: bd.Face, edge: bd.Wire, spacing: float) -> bd.LocationList:
    """
    Generate a list of locations along the edge of a face.

    :param face: The face to generate locations for.
    :param edge: The edge to generate locations for.
    :param spacing: The spacing between locations.
    :return: A list of locations along the edge of the face.
    """
    len = edge.length
    # Generate some points along the edges
    points = edge.positions(distances=[i for i in range(0, int(len), int(spacing))], position_mode=bd.PositionMode.LENGTH)
    # Generate planes at each point normal to the face.
    ret = []
    for point in points:
        plane = bd.Plane(origin=point, z_dir=face.normal_at(point))
        ret.append(plane.location)
    return bd.LocationList(ret)

#cylinder = bd.Cylinder(radius=30, height=50)
#face = cylinder.faces().sort_by(bd.Axis.Z)[1]
#edge = face.edges().sort_by(bd.Axis.Z)[2]
#for loc in locations_on_face_edge(face, edge, edge.length / 8):
#    loc: bd.Location = loc
#    hole = bd.Rot(Z=180) * bd.Pos(Z=-10) * loc * bd.Hole(10, 10, mode=bd.Mode.SUBTRACT)
#    cylinder -= hole 
#    hole = bd.Rot(Z=180) * bd.Pos(Z=-30) * loc * bd.Hole(10, 10, mode=bd.Mode.SUBTRACT)
#    cylinder -= hole 



