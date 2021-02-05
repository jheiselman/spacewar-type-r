import json
import os
import os.path

class LevelManager(object):
    def __init__(self, filepath = "levels"):
        self.filepath = filepath
    
    def load(self, filename):
        fqpn = os.path.join(self.filepath, filename)

        if not os.path.exists(fqpn):
            fqpn = os.path.join(self.filepath, filename + ".lvl")

        with open(fqpn, 'r') as f:
            level_data = json.load(f)

        return Level(level_data, fqpn)


class Level(object):
    def __init__(self, level_data = None, level_file = None):
        self.file = level_file
        try:
            self.name = level_data['name']
            self.max_players = level_data['max_players']
            self.background = level_data['background']
            self.static_entities = level_data['static_entities']
            self.spawn_points = level_data['spawn_points']
            self.next_level = level_data['next_level']
        except:
            self.name = "Unnamed Level"
            self.background = None
            self.max_players = 1
            self.static_entities = {}
            self.spawn_points = {}
            self.next_level = None

    def __repr__(self):
        return str({"name": self.name, "background": self.background, "static_entities": self.static_entities, "spawn_points": self.spawn_points})


if __name__ == "__main__":
    print("Loading level data from ./level1.lvl")
    lm = LevelManager(".")
    level = lm.load("level1.lvl")
    print(str(level))
