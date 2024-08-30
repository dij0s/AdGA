from ursina import *
from direct.stdpy import thread

from car import Car
from remote_controller import RemoteController
from raycast_sensor import *


from sun import SunLight

from track import ForestTrack

Text.default_font = "./assets/Roboto.ttf"
Text.default_resolution = 1080 * Text.size

# Window
window.vsync = True # Set to false to uncap FPS limit of 60
app = Ursina(size=(1280,1024))
window.title = "Rally"
window.borderless = False
window.show_ursina_splash = False
window.cog_button.disable()
window.fps_counter.enable()
window.exit_button.disable()

# Starting new thread for assets

def load_assets():
    models_to_load = [
        # Cars
        "sports-car.obj", "muscle-car.obj", "limousine.obj", "lorry.obj", "hatchback.obj", "rally-car.obj",
        # Tracks
        "forest_track.obj", "particles.obj",
        # Track Bounds
        "forest_track_bounds.obj",
        # Track Details
        "trees-forest.obj", "thintrees-forest.obj",
        # Utils
        "line.obj"
    ]

    textures_to_load = [
        # Car Textures
        # Sports Car
        "sports-red.png",
        # Track Textures
        "forest_track.png",
        # Track Detail Textures
        "tree-forest.png", "thintree-forest.png",
        # Particle Textures
        "particle_forest_track.png",
        # Cosmetic Textures + Icons
        "viking_helmet.png", "surfinbird.png", "surfboard.png", "viking_helmet-icon.png", "duck-icon.png",
        "banana-icon.png", "surfinbird-icon.png",
        #Utils
        "red.png"
    ]

    for i, m in enumerate(models_to_load):
        load_model(m)

    for i, t in enumerate(textures_to_load):
        load_texture(t)

try:
    thread.start_new_thread(function = load_assets, args = "")
except Exception as e:
    print("error starting thread", e)


# Car
car = Car()
car.sports_car()

remote_controller = RemoteController(car = car)

# Tracks
forest_track = ForestTrack(car)
car.forest_track = forest_track

# Lighting + shadows
sun = SunLight(direction = (-0.7, -0.9, 0.5), resolution = 3072, car = car)
ambient = AmbientLight(color = Vec4(0.5, 0.55, 0.66, 0) * 0.75)

render.setShaderAuto()

# Sky
Sky(texture = "sky")

car.visible = True
mouse.locked = True

car.position = (12, -35, 76)
car.rotation = (0, 90, 0)
car.reset_count_timer.enable()

car.enable()

car.camera_angle = "top"
car.change_camera = True
car.camera_follow = True

forest_track.enable()
forest_track.played = True

for f in forest_track.track:
    f.enable()
    f.alpha = 255
if car.graphics != "ultra fast":
    for detail in forest_track.details:
        detail.enable()
        detail.alpha = 255


app.run()