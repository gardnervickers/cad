
from math import floor
import build123d as bd 
import hello_world.util.skadis_hook as skadis


# Distance between mounting circles.
tolerance = 0.1 * bd.MM


items = []

class SkadisShelf():

    def __init__(self, width: int, depth: float, thickness: float):
        """
        Args:
            width (int): width of the shelf in multiples of 40mm (the skadis hook dimensions)
            depth (float): depth of the shelf
            thickness (float): thickness of the shelf
        """
        # Width here is going to be center-to-center width of both skadis hooks and pegs
        # Find the nearest multiple of 40mm 
        self.width = floor(width / 40) * 40
        self.shelf_width = width
        self.depth = depth * bd.MM
        self.thickness = thickness * bd.MM
        self.tolerance = 0.2 * bd.MM
        self.fillet_radius = 2 * bd.MM
        self.peg_diameter = 2 * bd.MM


    def build(self):
        brackets = self.__make_brackets()
        peg_dist = self.bracket_peg_distance(brackets)
        shelf = self.__make_shelf(peg_dist)
        # Bring up the shelf to the top of the brackets.
        shelf = shelf.move(bd.Location((0, 0, 0))) 
        bracket_top_f = brackets.faces().sort_by(bd.Axis.Z, reverse=True).filter_by(lambda f: f.edges().__len__() > 3)[0: 2]
        shelf = shelf.move(bd.Location((0, -42, bracket_top_f[0].center().Z)))

        return [shelf, brackets]

    def bracket_peg_distance(self, brackets):
        top_4_faces = brackets.faces().sort_by(bd.Axis.Z, reverse=True)[0:4]
        pegs = top_4_faces.sort_by(bd.Axis.Y)[0:2]
        left_peg = pegs[0]
        right_peg = pegs[1]
        return left_peg.center().X - right_peg.center().X

    def __make_hook_plate(self):
        locs = skadis.HookLocations(2, 2)
        locs = list(locs)[0:3]
        part = bd.Part(None)
        for log in locs:
            part += skadis.Hook().move(log)
        part = bd.Rot(Z=90) * part
        part = part.clean()
        vtx = part.vertices().filter_by(lambda v: v.Z <= 0.001)

        x_min = vtx.sort_by(bd.Axis.X).first
        x_max = vtx.sort_by(bd.Axis.X).last
        y_min = vtx.sort_by(bd.Axis.Y).first
        y_max = vtx.sort_by(bd.Axis.Y).last

        ## Make a rectangle to fit the vertices.
        rect = bd.Plane.XY * bd.Rectangle(x_max.X - x_min.X, y_max.Y - y_min.Y)
        inner_rect = bd.offset(rect, -6)
        inner_rect = bd.fillet(inner_rect.vertices(), self.fillet_radius)
        part = bd.Plane.XY * bd.Pos(Y=10) * part
        rect = bd.offset(rect, 2, kind=bd.Kind.INTERSECTION)
        rect -= inner_rect
        rect = bd.extrude(rect, self.thickness, dir=(0, 0, -1))
        part = bd.Compound([part, rect], label="hook_plate")
        part = bd.Rot(X=90, Y=180) * part
        return part

    def __make_bracket(self):
        # Make the bracket len half the depth of the bin
        len = max(self.depth * 0.8, 50)
        plate = self.__make_hook_plate()
        plate_f = plate.faces().sort_by(bd.Axis.Y).first
        vtxs = plate_f.vertices().sort_by(bd.Axis.X)[0:2]
        top_vtx = vtxs.sort_by(bd.Axis.Z).last
        bottom_vtx = vtxs.sort_by(bd.Axis.Z).first
        point_vtx = top_vtx + bd.Vector(0, -len, 0)
        # create a sketch plane normal to the face plane, between the two top and 
        # bottom vertices of the hook plate.
        e1 = bd.Edge.make_line(top_vtx, bottom_vtx)
        e2 = bd.Edge.make_line(bottom_vtx, point_vtx)
        e3 = bd.Edge.make_line(top_vtx, point_vtx)
        bracket_prof = bd.make_face([e1, e2, e3])
        bracket_prof_inner = bd.offset(bracket_prof, -self.thickness, kind=bd.Kind.ARC)
        bracket_prof_inner = bd.fillet(bracket_prof_inner.vertices(), self.fillet_radius)
        bracket_prof -= bracket_prof_inner
        bracket_prof = bd.fillet(bracket_prof.vertices().sort_by(bd.Axis.Y)[0:1], self.fillet_radius)
        bracket = bd.extrude(bracket_prof, self.thickness, dir=(1, 0, 0))
        bracket.label = "bracket"

        # Place the pegs on the L-bracket. 
        bracket_top_f = bracket.faces().sort_by(bd.Axis.Z).last
        if bracket_top_f.edges().sort_by(lambda e: e.length).last.length < 50 * bd.MM:
            raise Exception("Bracket is too short to place pegs. Must be at least 50mm")

        bracket_top_back_edge = bracket_top_f.edges().sort_by(bd.Axis.Y).last.center()
        peg1_loc = bracket_top_back_edge + bd.Vector(0, -20, 0)
        peg2_loc = peg1_loc + bd.Vector(0, -20, 0)
        peg1 = bd.Pos(peg1_loc) * bd.Circle(self.peg_diameter / 2)
        peg2 = bd.Pos(peg2_loc) * bd.Circle(self.peg_diameter / 2)
        peg1 = bd.extrude(peg1, self.thickness, dir=(0, 0, 1))
        peg2 = bd.extrude(peg2, self.thickness, dir=(0, 0, 1))
        bracket += peg1 + peg2 + plate
        return bracket

    # Makes left and right brackets, mirrored.
    def __make_brackets(self): 
        left_bracket = self.__make_bracket()
        left_bracket.label = "left_bracket"
        right_bracket = bd.mirror(left_bracket)
        right_bracket.label = "right_bracket"
        right_bracket = right_bracket.rotate(bd.Axis.Z, 180)
        right_bracket = right_bracket.move(bd.Location((self.width - 40, 0, 0)))
        center = (left_bracket + right_bracket).center()
        brackets = bd.Compound([left_bracket, right_bracket])
        brackets = brackets.move(bd.Location(-center))
        return brackets

    def __make_shelf(self, peg_dist: int):
        border = 6 
        shelf_prof = bd.Sketch(None)
        shelf_prof += bd.Rectangle(self.shelf_width + border * 2, self.depth)
        shelf_inner_prof = bd.offset(shelf_prof, -border)
        shelf_inner_len = shelf_inner_prof.edges().sort_by(bd.Axis.Y).last.length
        shelf_inner_width = shelf_inner_prof.edges().sort_by(bd.Axis.X).last.length
        shelf_prof -= shelf_inner_prof
        rect = bd.Rectangle(5, 5)
        coll = []
        x_count = floor(shelf_inner_len / 10)
        y_count = floor(shelf_inner_width / 10)
        grid = bd.GridLocations(10, 10, x_count, y_count)
        for loc in grid.local_locations:
            coll.append(rect.moved(loc))
        shelf_inner_prof -= coll
        shelf_prof += shelf_inner_prof

        # Add peg holes in the proper locations.
        peg_hole = bd.Circle(self.peg_diameter / 2 + tolerance)
        locs = []
        peg_hole_x_offset = peg_dist / 2
        locs.append(bd.Pos(X=peg_hole_x_offset, Y=(self.depth / 2) - 20) * peg_hole)
        locs.append(bd.Pos(X=-peg_hole_x_offset, Y=(self.depth / 2) - 20) * peg_hole)
        locs.append(bd.Pos(X=peg_hole_x_offset, Y=(self.depth / 2) - 40) * peg_hole)
        locs.append(bd.Pos(X=-peg_hole_x_offset, Y=(self.depth / 2) - 40) * peg_hole)
        shelf_prof -= locs
        shelf_prof = bd.fillet(shelf_prof.vertices().sort_by(bd.Axis.Y)[0:2], self.fillet_radius)
        shelf = bd.extrude(shelf_prof, self.thickness)
        return shelf

