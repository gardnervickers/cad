# Open up http://127.0.0.1:32323/ for an interactive 3d model viewer
import build123d as bd
import yacv_server as yacv
import hello_world.util.skadis_hook as skadis

yacv.yacv.startup_complete.wait()

yacv.yacv.shown_object_names()
yacv.clear()
yacv.show()
