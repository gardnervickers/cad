import build123d as bd

# Create a dog bowl with a bunch of random walls in the middle
# to act as a limiter for how fast Ham can chow down

bowl_diameter = 200 # 20cm
bowl_radius = bowl_diameter / 2
bowl_height = 60 # 12cm
bowl_thickness = 8 # 8mm

def bowl_profile() -> bd.Curve:
    base_od = bd.Line((0, 0), (bowl_radius, 0))
    wall_od = bd.Line((0, 0), (0, bowl_height))
    base_id = bd.Pos(Y=bowl_thickness) * bd.Line((bowl_thickness, 0), (bowl_radius, 0))
    wall_id = bd.Pos(X=bowl_thickness) * bd.Line((0, bowl_thickness), (0, bowl_height))
    top_lip = bd.Line(wall_od @ 1, wall_id @ 1)
    centerline = bd.Line(base_od @ 1, base_id @ 1)
    return bd.Plane.XY * bd.Curve([base_od, wall_od, base_id, wall_id, top_lip, centerline])

lines = bowl_profile()
face = bd.make_face(lines)
fillet_vtx = face.vertices().sort_by(bd.Axis.X)[0: -2]
face = bd.fillet(fillet_vtx, 4)


# Shift the whole face over so that the centerline is at the origin
face = bd.Pos(X=-bowl_radius) * face
# revolve around the x axis
bowl = bd.Pos(Z=0) * bd.Rot(X = 90) * bd.revolve(face, axis=bd.Axis.Y, revolution_arc=360)

# Place a circle in the middle to act as a guide for the Text
text_circle: bd.Circle = bd.Plane.XY * bd.Pos(Z=bowl_thickness) * bd.Circle(radius=bowl_radius * 0.6)
text_sk = bd.Text("Chow Down", font_size=65, path=text_circle.wire())
text_ext = bd.extrude(text_sk, amount=bowl_height * 0.25)

# Round off the top of each letter
bowl += text_ext 

