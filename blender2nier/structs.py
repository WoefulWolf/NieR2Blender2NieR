from blender2nier.util import Vector3


class vertex(object):
    def __init__(self, position, tangents, mapping, mapping2, color):
        self.position = position
        self.tangents = tangents
        self.mapping = mapping
        self.mapping2 = mapping2
        self.color = color