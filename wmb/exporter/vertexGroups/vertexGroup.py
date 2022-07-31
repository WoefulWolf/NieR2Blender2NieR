import math
from time import time

import bpy

class c_vertexGroup(object):
    def __init__(self, vertexGroupIndex, vertexesStart):
        self.vertexGroupIndex = vertexGroupIndex
        self.vertexGroupStart = vertexesStart

        def get_blenderObjects(self):
            objs = {}
            for obj in bpy.data.collections['WMB'].all_objects:
                if obj.type == 'MESH':
                    obj_name = obj.name.split('-')
                    if int(obj_name[-1]) == vertexGroupIndex:
                        if len(obj.data.uv_layers) == 0:
                            obj.data.uv_layers.new()
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

        def get_blenderUVCoords(self, objOwner, loopIndex, uvSlot):
            if uvSlot > len(objOwner.data.uv_layers)-1:
                print(" - UV Maps Error: Not enough UV Map layers! (Tried accessing UV layer number", uvSlot + 1, "of object", objOwner.name, "but it does not exist. Adding one!")
                objOwner.data.uv_layers.new()
            uv_coords = objOwner.data.uv_layers[uvSlot].data[loopIndex].uv
            return [uv_coords.x, 1-uv_coords.y]

        # Has bones = 7, 10, 11
        # 1 UV  = 0
        # 2 UVs = 1, 4, 7, 10
        # 3 UVs = 5, 11
        # 4 UVs = 14
        # 5 UVs = 12
        # Has Color = 4, 5, 10, 11, 12, 14

        if len(self.blenderObjects[0].data.uv_layers) == 1:         # 0
            self.vertexFlags = 0
        elif len(self.blenderObjects[0].data.uv_layers) == 2:       # 1, 4, 7, 10
            if self.blenderObjects[0]['boneSetIndex'] != -1:        # > 7, 10
                if self.blenderObjects[0].data.vertex_colors:       # >> 10
                    self.vertexFlags = 10
                else:                                               # >> 7
                    self.vertexFlags = 7

            else:                                                   # > 1, 4
                if self.blenderObjects[0].data.vertex_colors:       # >> 4
                    self.vertexFlags = 4
                else:                                               # >> 1
                    self.vertexFlags = 1


        elif len(self.blenderObjects[0].data.uv_layers) == 3:       # 5, 11
            if self.blenderObjects[0]['boneSetIndex'] != -1:        # >> 11
                self.vertexFlags = 11
            else:                                                   # >> 5
                self.vertexFlags = 5

        elif len(self.blenderObjects[0].data.uv_layers) == 4:       # 14
            self.vertexFlags = 14
        elif len(self.blenderObjects[0].data.uv_layers) == 5:       # 12
            self.vertexFlags = 12
        else:
            print(" - UV Maps Error: No UV Map found!")

        if self.vertexFlags == 0:
            self.vertexExDataSize = 0
        if self.vertexFlags == 4:                                         
            self.vertexExDataSize = 8       
        elif self.vertexFlags in {5, 7}:                                          
            self.vertexExDataSize = 12                                    
        elif self.vertexFlags in {10, 14}:
            self.vertexExDataSize = 16
        elif self.vertexFlags == 11:
            self.vertexExDataSize = 20


        def get_boneMap(self):
            boneMap = []
            for obj in bpy.data.collections['WMB'].all_objects:
                if obj.type == 'ARMATURE':
                    boneMapRef = obj.data["boneMap"]
                    for val in boneMapRef:
                        boneMap.append(val)
                    return boneMap

        self.boneMap = get_boneMap(self)

        def get_boneSet(self, boneSetIndex):
            boneSet = []
            for obj in bpy.data.collections['WMB'].all_objects:
                if obj.type == 'ARMATURE':
                    boneSetArrayRef = obj.data["boneSetArray"][boneSetIndex]
                    for val in boneSetArrayRef:
                        boneSet.append(val)
                    return boneSet

        def get_vertexesData(self):
            vertexes = []
            vertexesExData = []
            for bvertex_obj in blenderVertices:
                bvertex_obj_obj = bvertex_obj[1]
                print('   [>] Generating vertex data for object', bvertex_obj_obj.name)
                loops = get_blenderLoops(self, bvertex_obj_obj)
                sorted_loops = sorted(loops, key=lambda loop: loop.vertex_index)

                if self.vertexFlags not in {0, 1, 4, 5, 12, 14}:
                    boneSet = get_boneSet(self, bvertex_obj_obj["boneSetIndex"])
                
                previousIndex = -1
                for loop in sorted_loops:
                    if loop.vertex_index == previousIndex:
                        continue

                    previousIndex = loop.vertex_index
            
                    bvertex = bvertex_obj[0][loop.vertex_index]
                    # XYZ Position
                    position = [bvertex.co.x, bvertex.co.y, bvertex.co.z]

                    # Tangents
                    loopTangent = loop.tangent * 127
                    tx = int(loopTangent[0] + 127.0)
                    ty = int(loopTangent[1] + 127.0)
                    tz = int(loopTangent[2] + 127.0)
                    sign = int(-loop.bitangent_sign*127.0+128.0)

                    tangents = [tx, ty, tz, sign]

                    # Normal
                    normal = []
                    if self.vertexFlags == 0:
                        normal = [loop.normal[0], loop.normal[1], loop.normal[2], 0]

                    # UVs
                    uv_maps = []

                    uv1 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 0)
                    uv_maps.append(uv1)

                    if self.vertexFlags in {1, 4, 5, 12, 14}:
                        uv2 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 1)
                        uv_maps.append(uv2)

                    # Bones
                    boneIndexes = []
                    boneWeights = []
                    if self.vertexFlags in {7, 10, 11}:
                        # Bone Indices
                        for groupRef in bvertex.groups:
                            if len(boneIndexes) < 4:
                                boneGroupName = bvertex_obj_obj.vertex_groups[groupRef.group].name
                                boneID = int(boneGroupName.replace("bone", ""))

                                boneMapIndx = self.boneMap.index(boneID)
                                boneSetIndx = boneSet.index(boneMapIndx)
                                
                                boneIndexes.append(boneSetIndx)
                        
                        if len(boneIndexes) == 0:
                            print(len(vertexes) ,"- Vertex Weights Error: Vertex has no assigned groups. At least 1 required. Try using Blender's [Select -> Select All By Trait > Ungrouped Verts] function to find them.")

                        while len(boneIndexes) < 4:
                            boneIndexes.append(0)
                        
                        # Bone Weights
                        weights = [group.weight for group in bvertex.groups]
                        weightsSum = sum(weights)

                        if len(weights) >  4:
                            print(len(vertexes), "- Vertex Weights Error: Vertex has weights assigned to more than 4 groups. Try using Blender's [Weights -> Limit Total] function.")

                        normalized_weights = []                                             # Force normalize the weights as Blender's normalization sometimes get some rounding issues.
                        for val in weights:
                            if val > 0:
                                normalized_weights.append(float(val)/weightsSum)
                            else:
                                normalized_weights.append(0)

                        for val in normalized_weights:
                            if len(boneWeights) < 4:
                                weight = math.floor(val * 256.0)
                                if val == 1.0:
                                    weight = 255
                                boneWeights.append(weight)
                        
                        while len(boneWeights) < 4:
                            boneWeights.append(0)

                        while sum(boneWeights) < 255:                     # MOAR checks to make sure weights are normalized but in bytes. (A bit cheating but these values should make such a minor impact.)
                            boneWeights[0] += 1

                        while sum(boneWeights) > 255:                     
                            boneWeights[0] -= 1

                        if sum(boneWeights) != 255:                       # If EVEN the FORCED normalization doesn't work, say something :/
                            print(len(vertexes), "- Vertex Weights Error: Vertex has a total weight not equal to 1.0. Try using Blender's [Weights -> Normalize All] function.") 

                    color = []
                    if self.vertexFlags in {4, 5, 12, 14}:
                        if len (bvertex_obj_obj.data.vertex_colors) == 0:
                            print("Object had no vertex colour layer when one was expected - creating one.")
                            new_vertex_colors = bvertex_obj_obj.data.vertex_colors.new()
                        loop_color = bvertex_obj_obj.data.vertex_colors.active.data[loop.index].color
                        color = [int(loop_color[0]*255), int(loop_color[1]*255), int(loop_color[2]*255), int(loop_color[3]*255)]

                    vertexes.append([position, tangents, normal, uv_maps, boneIndexes, boneWeights, color])

                    
                    ##################################################
                    ###### Now lets do the extra data shit ###########
                    ##################################################
                    normal = []
                    uv_maps = []
                    color = []
                    if self.vertexFlags in {10, 11}:
                        if len (bvertex_obj_obj.data.vertex_colors) == 0:
                            print("Object had no vertex colour layer when one was expected - creating one.")
                            new_vertex_colors = bvertex_obj_obj.data.vertex_colors.new()

                    if self.vertexFlags in {1, 4, 5, 7, 10, 11, 12, 14}:
                        normal = [loop.normal[0], loop.normal[1], loop.normal[2], 0]
                    
                    if self.vertexFlags == 5:
                        uv3 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 2)
                        uv_maps.append(uv3)

                    elif self.vertexFlags == 7:
                        uv2 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 1)
                        uv_maps.append(uv2)

                    elif self.vertexFlags == 10:
                        uv2 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 1)
                        uv_maps.append(uv2)
                        loop_color = bvertex_obj_obj.data.vertex_colors.active.data[loop.index].color
                        color = [int(loop_color[0]*255), int(loop_color[1]*255), int(loop_color[2]*255), int(loop_color[3]*255)]

                    elif self.vertexFlags == 11:
                        uv2 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 1)
                        uv_maps.append(uv2)
                        loop_color = bvertex_obj_obj.data.vertex_colors.active.data[loop.index].color
                        color = [int(loop_color[0]*255), int(loop_color[1]*255), int(loop_color[2]*255), int(loop_color[3]*255)]
                        uv3 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 1)
                        uv_maps.append(uv3)

                    elif self.vertexFlags == 12:
                        uv2 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 1)
                        uv_maps.append(uv2)
                        uv3 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 2)
                        uv_maps.append(uv3)
                        uv4 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 3)
                        uv_maps.append(uv4)
                        uv5 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 4)
                        uv_maps.append(uv5)

                    elif self.vertexFlags == 14:
                        uv3 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 2)
                        uv_maps.append(uv3)
                        uv4 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 3)
                        uv_maps.append(uv4)
                    
                    vertexExData = [normal, uv_maps, color]
                    vertexesExData.append(vertexExData)
            
            return vertexes, vertexesExData

        def get_indexes(self):
            indexesOffset = 0
            indexes = []
            for obj in self.blenderObjects:
                for loop in obj.data.loops:
                    indexes.append(loop.vertex_index + indexesOffset)
                indexesOffset += len(obj.data.vertices)          

            # Reverse this loop order
            flip_counter = 0
            for i in range(len(indexes)):
                if flip_counter == 2:
                    indexes[i], indexes[i-1] = indexes[i-1], indexes[i]
                    flip_counter = 0
                    continue
                flip_counter += 1

            return indexes

        self.vertexSize = 28                                            # 28

        self.vertexOffset = self.vertexGroupStart                       
        self.vertexExDataOffset = self.vertexOffset + numVertices * self.vertexSize

        self.unknownOffset = [0, 0]                                      # Don't question it, it's unknown okay?

        self.unknownSize = [0, 0]                                        # THIS IS UNKOWN TOO OKAY? LEAVE ME BE

        self.numVertexes = numVertices                                            

        self.indexBufferOffset = self.vertexExDataOffset + self.numVertexes * self.vertexExDataSize

        self.numIndexes = get_numIndexes(self)

        self.vertexes, self.vertexesExData = get_vertexesData(self)
        
        self.indexes = get_indexes(self)

        self.vertexGroupSize = (self.numVertexes * self.vertexSize) + (self.numVertexes * self.vertexExDataSize) + (self.numIndexes * 4)

def clamp(val, minV, maxV):
    return maxV if val > maxV else \
        minV if val < minV else val
