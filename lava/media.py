from os import path
from pygame import image

class MediaManager:
    def __init__(self, basedir = '.'):
        self.basedir = basedir
        self.media = {}
    
    def load_image(self, file, directory = ''):
        try:
            return self.media[file]
        except KeyError:
            try:
                fqpn = path.join(self.basedir, directory, file)
            except AttributeError:
                try:
                    fqpn = path.join(self.basedir, file)
                except:
                    print("Error occurred loading %s from %s" % (file, self.basedir))
                    raise SystemExit
        
            image_obj = image.load(fqpn).convert()
            self.media[file] = image_obj
            return image_obj
