import bpy, bmesh, math, mathutils
from blender2nier.util import Vector3
from blender2nier.structs import vertex

class c_vertexGroup(object):
    def __init__(self, vertexGroupIndex, vertexGroupStart):
        self.vertexGroupIndex = vertexGroupIndex
        self.vertexGroupStart = vertexGroupStart

        def get_blenderObjects(self):
            blenderObjectsTemp = []

            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    obj_name = obj.name.split('_')
                    if int(obj_name[-1]) == vertexGroupIndex:
                        blenderObjectsTemp.append(obj)

            blenderObjects = []
            objIndex = 0
            while objIndex <= len(blenderObjectsTemp)-1:
                for obj in blenderObjectsTemp:
                    obj_name = obj.name.split('_')
                    if int(obj_name[-2]) == objIndex:
                        print('blenderObj: ', obj)
                        obj.data.calc_tangents()
                        blenderObjects.append(obj)
                        objIndex += 1 

            return blenderObjects
        
        self.blenderObjects = get_blenderObjects(self)

        def get_numVertices(self):
            numVertices = 0
            for obj in self.blenderObjects:
                numVertices += len(obj.data.vertices)
            return numVertices
        numVertices = get_numVertices(self)

        def get_numIndexes(self):
            numIndexes = 0
            for obj in self.blenderObjects:
                numIndexes += len(obj.data.polygons)
            return numIndexes * 3

        def get_blenderVertices(self):
            blenderVertices = []
            blenderObjects = self.blenderObjects

            for obj in blenderObjects:
                blenderVertices.append([obj.data.vertices, obj])
            return blenderVertices
        blenderVertices = get_blenderVertices(self)

        def get_blenderLoops(self, objOwner):
            blenderLoops = []
            blenderLoops += objOwner.data.loops

            return blenderLoops

        def get_blenderUVCoords(self, objOwner, loopIndex):
            uv_coords = []
            uv_coords = objOwner.data.uv_layers.active.data[loopIndex].uv
            return uv_coords

        def get_vertexes(self):
            vertexes = []
            for bvertex_obj in blenderVertices:
                for bvertex in bvertex_obj[0]:
                    position = Vector3(round(bvertex.co.x, 6), round(bvertex.co.y, 6), round(bvertex.co.z, 6))

                    for loop in get_blenderLoops(self, bvertex_obj[1]):
                        if loop.vertex_index == bvertex.index:
                            tx = round(loop.tangent[0]*127.0+127.0)
                            ty = round(loop.tangent[1]*127.0+127.0)
                            tz = round(loop.tangent[2]*127.0+127.0)
                            sign = round(loop.bitangent_sign*127.0+128.0)

                            uv_coords = get_blenderUVCoords(self, bvertex_obj[1], loop.index)
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
            for bvertex_obj in blenderVertices:
                for bvertex in bvertex_obj[0]:
                    vertexNormal = bvertex.normal

                    nx = round(vertexNormal[0]/2, 6)
                    ny = round(vertexNormal[1], 6)
                    nz = round(vertexNormal[2], 6)
                    dummy = 0
                    vertexExData = [nx, ny, nz, dummy] # Normal xyz + dummy
                    vertexesExData.append(vertexExData)
            return vertexesExData

        def get_indexes(self):
            indexesOffset = 0
            indexes = []
            for obj in self.blenderObjects:
                for loop in obj.data.loops:
                    indexes.append(loop.vertex_index + indexesOffset)
                indexesOffset += len(obj.data.vertices)
            
            i = 1
            while i < len(indexes)-1:
                temp = indexes[i]
                indexes[i] = indexes[i+1]
                indexes[i+1] = temp
                i += 3
            

            return indexes

        self.vertexSize = 28                                            # 28

        self.vertexOffset = self.vertexGroupStart + 48                  # 48 cus it's 30h

        self.vertexExDataOffset = (self.vertexOffset + numVertices * self.vertexSize) + ((self.vertexOffset + numVertices * self.vertexSize) % 16)

        self.unknownOffset = [0, 0]                                      # Don't question it, it's unknown okay?

        self.vertexExDataSize = 8                                        # SIZE OF ONE 'vertexesExData' ENTRY [ 8 if static, 20 if rigged with weights ]

        self.unknownSize = [0, 0]                                        # THIS IS UNKOWN TOO OKAY? LEAVE ME BE

        self.numVertexes = numVertices
    
        self.vertexFlags = 4                                             # I guess this is 4 huh

        self.indexBufferOffset = self.vertexExDataOffset + self.numVertexes * self.vertexExDataSize

        self.numIndexes = get_numIndexes(self)

        self.vertexes = get_vertexes(self)

        self.vertexesExData = get_vertexesExData(self)

        self.indexes = get_indexes(self)

        self.vertexGroupSize = (self.indexBufferOffset + self.numIndexes * 4) - self.vertexGroupStart
