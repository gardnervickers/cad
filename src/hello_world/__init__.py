from time import time
import build123d as bd
import yacv_server as yacv
import hello_world.util.layout as layout 
import hello_world.desk_cable as desk_cable
yacv.yacv.startup_complete.wait()

def display() -> bd.List[bd.Shape]:
    org = desk_cable.CableOrganizer(10, 4, 4)
    # Time which method is faster
    grid1 = org.create_grid(4, 4)
    return [grid1]

yacv.show(layout.layout_shapes(display()), names=["cyl"])
print(yacv.yacv.shown_object_names())
