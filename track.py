from ursina import *
import json
from direct.stdpy import thread


class Track(Entity):
    def __init__(self, metadata_file):

        with open(metadata_file, 'r') as f:
            self.data = json.load(f)


        track_model = self.data["track_model"]
        track_texture = self.data["track_texture"]

        origin_position = tuple(self.data["origin_position"])
        origin_rotation = tuple(self.data["origin_rotation"])
        origin_scale = tuple(self.data["origin_scale"])

        self.car_default_reset_position = tuple(self.data["car_default_reset_position"])
        self.car_default_reset_orientation = tuple(self.data["car_default_reset_orientation"])

        finish_line_position = tuple(self.data["finish_line_position"])
        finish_line_rotation = tuple(self.data["finish_line_rotation"])
        finish_line_scale = tuple(self.data["finish_line_scale"])
        
        super().__init__(model = track_model, texture = track_texture,
                         position = origin_position, rotation = origin_rotation, 
                         scale = origin_scale, collider = "mesh")

        self.finish_line = Entity(model = "cube", position = finish_line_position,
                                  rotation = finish_line_rotation, scale = finish_line_scale, visible = False)
        self.track = [ self.finish_line ]

        self.details = []
        for detail in self.data["details"]:
            self.details.append(Entity(model = detail["model"], texture = detail["texture"],
                            position = origin_position, rotation_y = origin_rotation[1], 
                            scale = origin_scale[1]))
        self.obstacles = []
        for obstacle in self.data["obstacles"]:
            self.obstacles.append(Entity(model = obstacle["model"],
                            collider = "mesh",
                            position = origin_position, rotation_y = origin_rotation[1], 
                            scale = origin_scale[1], visible = False))

        self.disable()
        
        self.played = False
        self.unlocked = False

        self.deactivate()

    def deactivate(self):
        for i in self.track:
            i.disable()
        for i in self.details:
            i.disable()
        for i in self.obstacles:
            i.disable()
        self.disable()

    def activate(self, activate_details = True):
        self.enable()
        for i in self.track:
            i.enable()
        for i in self.obstacles:
            i.enable()
        if activate_details:
            for i in self.details:
                i.enable()


    def load_assets(self, global_models = [], global_texs = []):
        def inner_load_assets():
            models_to_load = list(set(global_models + [detail["model"] for detail in self.data["details"]] + [obs["model"] for obs in self.data["obstacles"]]))
            textures_to_load = list(set(global_texs + [detail["texture"] for detail in self.data["details"]] + [obs["texture"] for obs in self.data["obstacles"]]))

            for i, m in enumerate(models_to_load):
                load_model(m)

            for i, t in enumerate(textures_to_load):
                load_texture(t)

        try:
            thread.start_new_thread(function=inner_load_assets, args="")
        except Exception as e:
            print("error starting thread", e)
