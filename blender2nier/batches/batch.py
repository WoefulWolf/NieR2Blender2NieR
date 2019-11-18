import bpy, bmesh, math, mathutils

class c_batch(object):
    def __init__(self, obj, vertexGroupIndex, indexStart, prev_numVertexes, boneSetIndex):
        self.vertexGroupIndex = vertexGroupIndex
        self.boneSetIndex = boneSetIndex
        self.vertexStart = 0
        self.indexStart = indexStart
        self.numVertexes = len(obj.data.vertices) + prev_numVertexes
        self.numIndexes = len(obj.data.loops)
        self.numPrimitives = len(obj.data.polygons)
