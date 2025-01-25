import build123d as bd
def vertical_edges(edge_list: bd.List[bd.Edge]) -> bd.List[bd.Edge]:
    filtered = []
    for edge in edge_list:
        if edge.is_closed:
            continue
        if len(edge.vertices()) != 2:
            continue
        first = edge.vertices()[0]
        second = edge.vertices()[1]
        if first.Z != second.Z and first.X == second.X  and first.Y == second.Y:
            filtered.append(edge)
    return filtered


def hexagon(side_len: float) -> bd.Polygon:
    # generate points
    points = [
        (side_len * bd.cos(i * bd.radians(60)), side_len * bd.sin(i * bd.radians(60)))
        for i in range(6)
    ]
    # create the hexagon
    return bd.Polygon(points, align=bd.Align.CENTER)

class CableOrganizer: 
    # Instantiate a new CableOrganizer which can produce parts used for under-desk cable managment.
    def __init__(self, side_len: int, grid_thickness: int, grid_surface_gap: int, clearance: float = 0.1):
        self.side_len = side_len
        self.grid_thickness = grid_thickness
        self.grid_surface_gap = grid_surface_gap
        self.inner_side_len = side_len * 0.6
        self.inner_hex_height = self.inner_side_len * bd.sqrt(3)
        self.hex_side_width = (side_len - self.inner_side_len) * bd.sqrt(3) / 2
        self.clearance = clearance


    # Creates a 2d hexagon with a hole in the middle. 
    def hex_mount(self) -> bd.Polygon:
        outer = hexagon(self.side_len)
        inner = hexagon(self.inner_side_len)
        return outer - inner
    
    def create_row_points(self, row_num: int, count: int) -> bd.List[bd.Vector]:
        points = []
        # The height of a hexagon is effectively the size
        hex_height = self.side_len * bd.sqrt(3)
        y = 0
        if row_num % 2 == 1:
            y = ((hex_height - self.hex_side_width) / 2)
        rem = count
        # Project wall thickness onto the horizontal axis by the cosine of 30 degrees
        x = row_num * (1.5 * self.side_len - (self.hex_side_width * (bd.sqrt(3)/2)))
        while rem > 0:
            rem -= 1
            points.append((x, y, 0))
            y += hex_height - self.hex_side_width
        return points

    def create_grid_points(self, rows, columns) -> bd.List[bd.Vector]:
        points = []
        for row in range(rows):
            points.extend(self.create_row_points(row, columns))
        return points

    def create_grid(self, rows: int, columns: int)-> bd.Part:
        hexagons = []
        hexmount = self.hex_mount()
        for point in self.create_grid_points(rows, columns):
            hexagons.append(hexmount.translate(point))
        face = bd.Face(None) + hexagons 
        return bd.extrude(face, amount=self.grid_thickness, dir=(0, 0, 1))

    def create_grid2(self, rows: int, columns: int) -> bd.Solid:
        hexmount = self.hex_mount()
        hexmount = bd.extrude(hexmount, amount=self.grid_thickness, dir=(0, 0, 1))
        solid = bd.Solid(None) 
        for point in self.create_grid_points(rows, columns):
            solid += hexmount.translate(point)
        return solid


    # Grid mounts are used to secure the hexagon grid to a surface. Each mount takes up 
    # a single hexagon and has a hole in the center for a screw. The mount goes through
    # the hexagon and extends outwards by half of the side length of the hexagon to allow
    # for multiple mounts to be placed side-by-side without interference.
    def create_grid_mount(self, screw_radius: float) -> bd.Part:
        outer_extension = (self.side_len - self.inner_side_len) / 2
        outer_mount_side_len = self.inner_side_len + outer_extension
        outer_mount_overhang_thickness = self.grid_thickness / 2
        inner_mount = hexagon(self.inner_side_len - self.clearance)
        inner_mount = bd.extrude(inner_mount, amount=self.grid_surface_gap + self.grid_thickness, dir=(0, 0, -1))
        outer_mount = hexagon(outer_mount_side_len)
        outer_mount = bd.extrude(outer_mount, amount=outer_mount_overhang_thickness, dir=(0, 0, 1))
        mount = inner_mount + outer_mount
        if screw_radius == 0:
            return mount
        screw_radius += self.clearance
        mount -= bd.Hole(screw_radius, depth=self.grid_surface_gap + self.grid_thickness)
        mount -= bd.Hole(screw_radius * 2.5, depth=2)
        return mount

    def create_connector_bracket(self, screw_radius: int) -> bd.Part:
        # Connector bracket consists of 3 mouns.
        left = self.create_grid_mount(screw_radius)
        middle = self.create_grid_mount(0)
        right = self.create_grid_mount(screw_radius)
        # Arrange them in a grid pattern.
        points = list(self.create_grid_points(1, 3))
        left = left.translate(points[0])
        middle = middle.translate(points[1])
        right = right.translate(points[2])
        bracket = left + middle + right
        return bracket
