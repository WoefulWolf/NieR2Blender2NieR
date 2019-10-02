import bpy, bmesh, math, mathutils

class c_batch(object):
    def __init__(self, obj, vertexGroupIndex, indexStart, prev_numVertexes):
        self.vertexGroupIndex = vertexGroupIndex
        self.boneSetIndex = -1
        self.vertexStart = 0
        self.indexStart = indexStart
        self.numVertexes = len(obj.data.vertices) + prev_numVertexes
        self.numIndexes = len(obj.data.polygons) * 3
        self.numPrimitives = len(obj.data.polygons)
