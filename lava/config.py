import os
from pygame.locals import *
import json

class ConfigManager(object):
    def __init__(self, filename = "default.cfg", filepath = "."):
        fqpn = os.path.join(filepath, filename)
        f = open(fqpn)
        config_data = json.load(f)
        f.close()
        
        self.process(config_data)

    def process(self, data):
        # set the screen resolution
        self.resolution = (data['Height'], data['Width'])

        # player 1
        self.player1_name = data['Player1Name']
        self.player2_name = data['Player2Name']


        # Key Bindings
        self.keys = {}
        for key in data['Keys']:
            self.keys[key] = eval(data['Keys'][key])


if __name__ == "__main__":
    config = ConfigManager()
    print(config.resolution)
