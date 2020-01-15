import bpy, bmesh, math, mathutils
import numpy as np
import math
from blender2nier.util import Vector3

class c_vertexGroup(object):
    def __init__(self, vertexGroupIndex, vertexesStart):
        self.vertexGroupIndex = vertexGroupIndex
        self.vertexGroupStart = vertexesStart

        def get_blenderObjects(self):
            objs = {}
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    obj_name = obj.name.split('-')
                    if int(obj_name[-1]) == vertexGroupIndex:
                        obj.data.calc_tangents()
                        objs[int(obj_name[0])] = obj

            blenderObjects = []
            for key in sorted (objs):
                blenderObjects.append(objs[key])

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

        if blenderVertices[0][1]['vertexColours_mean'] == None:
            self.vertexFlags = 7                                             # 4, 7, 10, 11
        else:    
            self.vertexFlags = 10

        if self.vertexFlags == 4:                                            # SIZE OF ONE 'vertexesExData' 8, 16, 20
            self.vertexExDataSize = 8       
        elif self.vertexFlags == 7:                                          
            self.vertexExDataSize = 12                                    
        elif self.vertexFlags == 10:
            self.vertexExDataSize = 16
        elif self.vertexFlags == 11:
            self.vertexExDataSize = 20

        def get_boneMap(self):
            boneMap = []
            for obj in bpy.data.objects:
                if obj.type == 'ARMATURE':
                    boneMapRef = obj.data["boneMap"]
                    for val in boneMapRef:
                        boneMap.append(val)
                    return boneMap

        self.boneMap = get_boneMap(self)

        def get_boneSet(self, boneSetIndex):
            boneSet = []
            for obj in bpy.data.objects:
                if obj.type == 'ARMATURE':
                    boneSetArrayRef = obj.data["boneSetArray"][boneSetIndex]
                    for val in boneSetArrayRef:
                        boneSet.append(val)
                    return boneSet

        def get_vertexes(self):
            vertexes = []
            for bvertex_obj in blenderVertices:
                print('   [>] Generating vertexes for object', bvertex_obj[1].name)
                loops = get_blenderLoops(self, bvertex_obj[1])

                boneSet = get_boneSet(self, bvertex_obj[1]["boneSetIndex"])

                for bvertex in bvertex_obj[0]:
                    # XYZ Position
                    position = Vector3(round(bvertex.co.x, 6), round(bvertex.co.y, 6), round(bvertex.co.z, 6))
                    for loop in loops:
                        if loop.vertex_index == bvertex.index:
                            # Tangents
                            tx = np.clip(round(loop.tangent[0]*127.0+127.0), 0, 255)
                            ty = np.clip(round(loop.tangent[1]*127.0+127.0), 0, 255)
                            tz = np.clip(round(loop.tangent[2]*127.0+127.0), 0, 255)
                            sign = np.clip(round(loop.bitangent_sign*127.0+128.0), 0, 255)

                            # UVs
                            uv_coords = get_blenderUVCoords(self, bvertex_obj[1], loop.index)
                            mapping = [uv_coords.x, 1-uv_coords.y]      # NieR uses inverted Y from Blender, thus 1-y

                            # Bone Indexes
                            if self.vertexFlags == 4:
                                mapping2 = mapping
                                color = [0, 0, 0, 255]  
                            else:
                                boneIndexes = []
                                for groupRef in bvertex.groups:
                                    if len(boneIndexes) < 4:
                                        boneGroupName = bvertex_obj[1].vertex_groups[groupRef.group].name
                                        boneID = int(boneGroupName.replace("bone", ""))

                                        boneMapIndx = self.boneMap.index(boneID)
                                        boneSetIndx = boneSet.index(boneMapIndx)
                                        
                                        boneIndexes.append(boneSetIndx)
                                
                                if len(boneIndexes) == 0:
                                    print(len(vertexes) ,"- Vertex Weights Error: Vertex has no assigned groups. At least 1 required. Try using Blender's [Select -> Select All By Trait > Ungrouped Verts] function to find them.")

                                while len(boneIndexes) < 4:
                                    boneIndexes.append(0)

                                mapping2 = boneIndexes

                                # Bone Weights
                                weights = [group.weight for group in bvertex.groups]

                                if len(weights) >  4:
                                    print(len(vertexes), "- Vertex Weights Error: Vertex has weights assigned to more than 4 groups. Try using Blender's [Weights -> Limit Total] function.")

                                normalized_weights = []                                             # Force normalize the weights as Blender's normalization sometimes get some rounding issues.
                                for val in weights:
                                    if val > 0:
                                        normalized_weights.append(float(val)/sum(weights))
                                    else:
                                        normalized_weights.append(0)

                                color = []
                                for val in normalized_weights:
                                    if len(color) < 4:
                                        weight = math.floor(val * 256.0)
                                        if val == 1.0:
                                            weight = 255
                                        color.append(weight)
                                
                                while len(color) < 4:
                                    color.append(0)

                                while sum(color) < 255:                     # MOAR checks to make sure weights are normalized but in bytes. (A bit cheating but these values should make such a minor impact.)
                                    color[0] += 1

                                while sum(color) > 255:                     
                                    color[0] -= 1

                                if sum(color) != 255:                       # If EVEN the FORCED normalization doesn't work, say something :/
                                    print(len(vertexes), "- Vertex Weights Error: Vertex has a total weight not equal to 1.0. Try using Blender's [Weights -> Normalize All] function.")
                                 
                            break                                       # WITHOUT THIS BREAK, EXPORTING COULD TAKE HOURS :DDDDD

                    tangents = [tx, ty, tz, sign] 

                    #print([position.xyz, tangents, mapping, mapping2, color])
                    vertexes.append([position.xyz, tangents, mapping, mapping2, color])
            return vertexes

        def get_vertexesExData(self):
            vertexesExData = []
            for bvertex_obj in blenderVertices:
                for idx, bvertex in enumerate(bvertex_obj[0]):
                    if self.vertexExDataSize == 8:
                        vertexNormal = bvertex.normal

                        nx = vertexNormal[0]*-1
                        ny = vertexNormal[1]*-1
                        nz = vertexNormal[2]*-1
                        dummy = 0
                        vertexExData = [nx, ny, nz, dummy] # Normal xyz + dummy
                        vertexesExData.append(vertexExData)

                    elif self.vertexExDataSize == 12:
                        mapping2 = self.vertexes[idx][2]

                        vertexNormal = bvertex.normal
                        nx = vertexNormal[0]*-1
                        ny = vertexNormal[1]*-1
                        nz = vertexNormal[2]*-1
                        dummy = 0

                        normal = [nx, ny, nz, dummy] # Normal xyz + dummy

                        vertexExData = [mapping2, normal]
                        vertexesExData.append(vertexExData)

                    elif self.vertexExDataSize == 16:
                        mapping2 = self.vertexes[idx][2]
                        if bvertex_obj[1]['vertexColours_mean'] == None:
                            color = [255, 255, 255, 255]
                        else:
                            color = bvertex_obj[1]['vertexColours_mean']                            # TODO Shader Influence Colour thingy

                        vertexNormal = bvertex.normal
                        nx = vertexNormal[0]*-1
                        ny = vertexNormal[1]*-1
                        nz = vertexNormal[2]*-1
                        dummy = 0

                        normal = [nx, ny, nz, dummy] # Normal xyz + dummy

                        vertexExData = [mapping2, color, normal]
                        vertexesExData.append(vertexExData)

                    elif self.vertexExDataSize == 20:
                        mapping2 = self.vertexes[idx][2]
                        
                        if bvertex_obj[1]['vertexColours_mean'] == None:
                            color = [255, 255, 255, 255]
                        else:
                            color = bvertex_obj[1]['vertexColours_mean']                            # TODO Shader Influence Colour thingy

                        vertexNormal = bvertex.normal
                        nx = vertexNormal[0]*-1
                        ny = vertexNormal[1]*-1
                        nz = vertexNormal[2]*-1
                        dummy = 0

                        normal = [nx, ny, nz, dummy] # Normal xyz + dummy

                        mapping3 = mapping2

                        vertexExData = [mapping2, color, normal, mapping3]
                        vertexesExData.append(vertexExData)

            return vertexesExData

        def get_indexes(self):
            indexesOffset = 0
            indexes = []
            for obj in self.blenderObjects:
                for loop in obj.data.loops:
                    indexes.append(loop.vertex_index + indexesOffset)
                indexesOffset += len(obj.data.vertices)
            
            
            # Index Re-ordering
            #i = 1
            #while i < len(indexes)-1:
            #    temp = indexes[i]
            #    indexes[i] = indexes[i+1]
            #    indexes[i+1] = temp
            #    i += 3
            

            return indexes

        self.vertexSize = 28                                            # 28

        self.vertexOffset = self.vertexGroupStart                       # 48 cus it's 30h duhhh

        self.vertexExDataOffset = self.vertexOffset + numVertices * self.vertexSize

        self.unknownOffset = [0, 0]                                      # Don't question it, it's unknown okay?

        self.unknownSize = [0, 0]                                        # THIS IS UNKOWN TOO OKAY? LEAVE ME BE

        self.numVertexes = numVertices                                            

        self.indexBufferOffset = self.vertexExDataOffset + self.numVertexes * self.vertexExDataSize

        self.numIndexes = get_numIndexes(self)

        self.vertexes = get_vertexes(self)

        self.vertexesExData = get_vertexesExData(self)

        self.indexes = get_indexes(self)

        self.vertexGroupSize = (self.numVertexes * self.vertexSize) + (self.numVertexes * self.vertexExDataSize) + (self.numIndexes * 4)
