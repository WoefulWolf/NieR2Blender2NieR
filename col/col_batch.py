import bpy, bmesh

class Batch:
    def __init__(self, bObj, batchStartOffset):
        self.boneIndex = -1
        self.offsetVertices = batchStartOffset + 5 * 4
        self.vertexCount = len(bObj.data.vertices)
        self.offsetIndices = self.offsetVertices + (self.vertexCount * 16)
        self.indexCount = len(bObj.data.polygons) * 3

        bm = bmesh.new()
        bm.from_mesh(bObj.data)
        bm.verts.index_update()
        bm.faces.index_update()

        self.vertices = []
        for vertex in bm.verts:
            vertexVec4 = [vertex.co[0], vertex.co[1], vertex.co[2], 1]
            self.vertices.append(vertexVec4)

        self.indices = []
        for face in bm.faces:
            for vert in reversed(face.verts):
                self.indices.append(vert.index)

        bm.to_mesh(bObj.data)
        bm.free()

        self.structSize = (5*4) + (self.vertexCount * 16) + (self.indexCount * 2)