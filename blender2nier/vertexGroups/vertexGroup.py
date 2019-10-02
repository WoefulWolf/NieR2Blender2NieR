import bpy, bmesh, math, mathutils
from blender2nier.util import Vector3
from blender2nier.structs import vertex

class c_vertexGroup(object):
    def __init__(self, vertexGroupIndex, vertexGroupStart):
        self.vertexGroupIndex = vertexGroupIndex
        self.vertexGroupStart = vertexGroupStart

        # Number of vertices
        def get_numVertices(self):
            numVertices = 0
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    obj_name = obj.name.split('_')
                    if int(obj_name[-1]) == vertexGroupIndex:
                        numVertices += len(obj.data.vertices)
            return numVertices

        def get_numIndexes(self):
            numIndexes = 0
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    obj_name = obj.name.split('_')
                    if int(obj_name[-1]) == vertexGroupIndex:
                        numIndexes += len(obj.data.polygons)
            return numIndexes * 3

        def get_blenderVertices(self):
            blenderVertices = []
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    obj_name = obj.name.split('_')
                    if int(obj_name[-1]) == vertexGroupIndex: 
                        blenderVertices += obj.data.vertices        
            return blenderVertices

        def get_blenderLoops(self):
            blenderLoops = []
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    obj_name = obj.name.split('_')
                    if int(obj_name[-1]) == vertexGroupIndex:
                        obj.data.calc_tangents()
                        blenderLoops += obj.data.loops
            return blenderLoops

        def get_blenderUVCoords(self, loopIndex):
            uv_coords = []
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    obj_name = obj.name.split('_')
                    if int(obj_name[-1]) == vertexGroupIndex:
                        obj.data.calc_tangents()
                        uv_coords = obj.data.uv_layers.active.data[loopIndex].uv
            return uv_coords

        def get_vertexes(self):
            vertexes = []
            for bvertex in get_blenderVertices(self):
                position = Vector3(round(bvertex.co.x, 6), round(bvertex.co.y, 6), round(bvertex.co.z, 6))

                for loop in get_blenderLoops(self):
                    if loop.vertex_index == bvertex.index:
                        tx = round(loop.tangent[0]*127.0+127.0)
                        ty = round(loop.tangent[1]*127.0+127.0)
                        tz = round(loop.tangent[2]*127.0+127.0)
                        sign = round(loop.bitangent_sign*127.0+128.0)

                        uv_coords = get_blenderUVCoords(self, loop.index)
                        mapping = [uv_coords.x, 1-uv_coords.y]      # NieR uses inverted Y from Blender, thus 1-y
                        mapping2 = mapping                                              # These 2 always seem to be the same (I think)
                        break

                tangents = [tx, ty, tz, sign]
                color = [0, 0, 0, 255]   

                #print([position.xyz, tangents, mapping, mapping2, color]) 
                vertexes.append([position.xyz, tangents, mapping, mapping2, color])
            return vertexes

        def get_vertexesExData(self):
            vertexesExData = []
            for bvertex in get_blenderVertices(self):
                vertexNormal = bvertex.normal

                nx = -round(vertexNormal[0]/2, 6)
                ny = -round(vertexNormal[1], 6)
                nz = -round(vertexNormal[2], 6)
                dummy = 0
                vertexExData = [nx, ny, nz, dummy] # Normal xyz + dummy
                vertexesExData.append(vertexExData)
            return vertexesExData

        def get_indexes(self):
            indexes = []
            for loop in get_blenderLoops(self):
                indexes.append(loop.vertex_index)
            return indexes

        self.vertexSize = 28                                            # Always 28?

        self.vertexOffset = self.vertexGroupStart + 48                  # 48 cus it's 30h

        self.vertexExDataOffset = self.vertexOffset + get_numVertices(self) * self.vertexSize

        self.unknownOffset = [0, 0]                                      # Don't question it, it's unknown okay?

        self.vertexExDataSize = 8                                        # SIZE OF ONE 'vertexesExData' ENTRY [ 8 if static, 20 if rigged with weights ]

        self.unknownSize = [0, 0]                                        # THIS IS UNKOWN TOO OKAY? LEAVE ME BE

        self.numVertexes = get_numVertices(self)
    
        self.vertexFlags = 4                                             # I guess this is 4 huh

        self.indexBufferOffset = self.vertexExDataOffset + self.numVertexes * self.vertexExDataSize

        self.numIndexes = get_numIndexes(self)

        self.vertexes = get_vertexes(self)

        self.vertexesExData = get_vertexesExData(self)

        self.indexes = get_indexes(self)

        self.vertexGroupSize = (self.indexBufferOffset + self.numIndexes * 4) - self.vertexGroupStart