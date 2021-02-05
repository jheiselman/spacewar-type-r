import math

def radial_collide(item1, item2):
    """ item1 and item2 are 3-tuples in the format of
        (x, y, radius) for each object to test
        """
    x_diff = item1[0] - item2[0]
    y_diff = item1[1] - item2[1]
    hit_radius = item1[2] + item2[2]

    return math.hypot(x_diff, y_diff) < hit_radius