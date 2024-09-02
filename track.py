from ursina import *
import json


class ForestTrack(Entity):
    def __init__(self, car, metadata_file):

        with open(metadata_file, 'r') as f:
            data = json.load(f)

        track_model = data["track_model"]
        track_texture = data["track_texture"]
        boundaries_model = data["boundaries_model"]
        origin_position = tuple(data["origin_position"])
        origin_rotation = tuple(data["origin_rotation"])
        origin_scale = tuple(data["origin_scale"])
        finish_line_position = tuple(data["finish_line_position"])
        finish_line_rotation = tuple(data["finish_line_rotation"])
        finish_line_scale = tuple(data["finish_line_scale"])
        details = data["details"]
        
        super().__init__(model = track_model, texture = track_texture,
                         position = origin_position, rotation = origin_rotation, 
                         scale = origin_scale, collider = "mesh")

        self.car = car

        self.finish_line = Entity(model = "cube", position = finish_line_position,
                                  rotation = finish_line_rotation, scale = finish_line_scale, visible = False)
        self.boundaries = Entity(model = boundaries_model,
                                 collider = "mesh",
                                 position = origin_position, rotation = origin_rotation,
                                 scale = origin_scale, visible = False)
        self.track = [
            self.finish_line, self.boundaries
        ]

        self.details = []
        for detail in details:
            self.details.append(Entity(model = detail["model"], texture = detail["texture"],
                            position = origin_position, rotation_y = origin_rotation[1], 
                            scale = origin_scale[1]))

        self.disable()

        for i in self.track:
            i.disable()
        for i in self.details:
            i.disable()
        
        self.played = False
        self.unlocked = False

    def update(self):
        if self.car.simple_intersects(self.finish_line):
            if self.car.anti_cheat == 1:
                self.car.timer_running = True
                self.car.anti_cheat = 0
                if self.car.gamemode != "drift":
                    invoke(self.car.reset_timer, delay = 3)
