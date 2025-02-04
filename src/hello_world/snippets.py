from ocp_vscode import set_port, show 
import build123d as bd 
import hello_world.util.skadis_hook as skadis


# This is going to be a generic skadis shelf, with the idea being that a shelf
# can transform into a box or tray depending on the wall height. We'll start by
# making the L-bracket on top of which we will place a circle peg for mounting.

# Distance between mounting circles.
tolerance = 0.1 * bd.MM


items = []

def create_hook_plate(width: float, thickness: float): 
    backplate_prof = bd.Rectangle(40 + skadis.Hook.width(), width)
    backplate = bd.extrude(backplate_prof, thickness)
    for loc in bd.Plane(backplate.faces().sort_by(bd.Axis.Z).last) * skadis.HookLocations(2, 1):
        backplate += loc * skadis.Hook()
    return backplate

def create_bracket(thickness: float): 
    # Make a right angle L-bracket.
    bracket_len = 80 
    hook_width = thickness 
    hook_plate = create_hook_plate(hook_width, thickness)
    bracket_height = hook_plate.edges().sort_by(lambda e: e.length).last.length 
    l_bracket_prof = bd.Triangle(a=bracket_height, c=bracket_len, B=90)
    l_bracket_prof = bd.fillet(l_bracket_prof.vertices().sort_by(bd.Axis.Y)[2:3], 2)
    l_bracket_inner = bd.offset(l_bracket_prof, -thickness, kind=bd.Kind.ARC)
    l_bracket_prof -= l_bracket_inner
    l_bracket = bd.extrude(l_bracket_prof, thickness)
    hook_plate = bd.Plane(l_bracket.faces().sort_by(bd.Axis.Y).first) * bd.Rot(Z=180) * hook_plate
    # Now we put our mounting circle on the L-bracket.
    top_bracket_face = l_bracket.faces().sort_by(bd.Axis.X).first
    mc_plane = bd.Plane(top_bracket_face)
    mc_circle = mc_plane * bd.Circle((thickness / 2) - tolerance)
    mc_circle = bd.extrude(mc_circle, thickness)
    bracket = bd.Rot(Y=90) * (l_bracket + hook_plate + mc_circle)
    return bracket

def rear_vtxs(bracket: bd.Part):
    return bracket.faces().filter_by(bd.Axis.Z)[0].vertices().sort_by(bd.Axis.Y)[2:4].sort_by(bd.Axis.X)

def make_shelf(bottom_bracket, top_bracket, thickness, shelf_depth):
    back_vtx = rear_vtxs(bottom_bracket).first - bd.Vector(18 - thickness, 0, 0)
    items.append(back_vtx)
    front_vtx = rear_vtxs(top_bracket).last + bd.Vector(18 - thickness, 0, 0)
    items.append(front_vtx)
    lines = bd.Curve([
        bd.Line(back_vtx, front_vtx),
        bd.Line(back_vtx, back_vtx + bd.Vector(0, shelf_depth, 0)),
        bd.Line(front_vtx, front_vtx + bd.Vector(0, shelf_depth, 0)),
        bd.Line(back_vtx + bd.Vector(0, shelf_depth, 0), front_vtx + bd.Vector(0, shelf_depth, 0))
        ])
    shelf_prof = bd.make_face(lines)

    bottom_bracket_hole_loc = bottom_bracket.faces().sort_by(bd.Axis.Z).last.center()
    top_bracket_hole_loc = top_bracket.faces().sort_by(bd.Axis.Z).last.center()
    shelf = bd.extrude(shelf_prof, thickness)
    mount_cut = bd.extrude(bd.Circle((thickness / 2)), thickness, dir=(0, 0, -1))
    mc1 = bd.Pos(bottom_bracket_hole_loc.center()) * mount_cut
    mc2 = bd.Pos(top_bracket_hole_loc.center()) * mount_cut
    shelf -= (mc1 + mc2)
    return shelf

def add_side_panels(shelf, thickness, height):
    shelf_depth = shelf.edges().sort_by(bd.Axis.X).last.length
    shelf_top_f = shelf.faces().sort_by(bd.Axis.Z).last
    side_panel_prof = bd.Plane(shelf_top_f) * bd.Rectangle(thickness, shelf_depth)
    dist_edge_dx = side_panel_prof.edges().sort_by(bd.Axis.X).first.distance_to(shelf_top_f.edges().sort_by(bd.Axis.X).first)
    dist_edge_ux = side_panel_prof.edges().sort_by(bd.Axis.X).last.distance_to(shelf_top_f.edges().sort_by(bd.Axis.X).last)
    side_panel_left = side_panel_prof.moved(bd.Location(bd.Vector(-dist_edge_dx, 0, 0)))
    side_panel_right = side_panel_prof.moved(bd.Location(bd.Vector(dist_edge_ux, 0, 0)))
    side_panel_left = bd.extrude(side_panel_left.face(), height)
    side_panel_right = bd.extrude(side_panel_right.face(), height)
    return (side_panel_left, side_panel_right) 

def add_front_panel(shelf, thickness, height):
    shelf_width = shelf.edges().sort_by(bd.Axis.Y).last.length
    shelf_top_f = shelf.faces().sort_by(bd.Axis.Z).last

    front_panel_prof = bd.Plane(shelf_top_f) * bd.Rectangle(shelf_width, thickness)
    dist_edge_y = front_panel_prof.edges().sort_by(bd.Axis.Y).last.distance_to(shelf_top_f.edges().sort_by(bd.Axis.Y).last)
    front_panel_prof = front_panel_prof.moved(bd.Location(bd.Vector(0, dist_edge_y, 0)))
    front_panel = bd.extrude(front_panel_prof.face(), height)
    return front_panel 


shelf_depth = 100 
width_in_brackets = 5 
thickness = 4.8
bottom_bracket = create_bracket(thickness)
top_bracket = bottom_bracket.moved(bd.Location((width_in_brackets * 40, 0, 0)))
shelf = make_shelf(bottom_bracket, top_bracket, thickness, shelf_depth)

walls = add_front_panel(shelf, thickness / 2, 20)
walls += add_side_panels(shelf, thickness / 2, 20)
fillet_edges = []

items.append(bottom_bracket)
items.append(top_bracket)
items.append(shelf)

shelf += walls

#bd.export_step(bd.Compound(items), "shelf.step")
show(items)


