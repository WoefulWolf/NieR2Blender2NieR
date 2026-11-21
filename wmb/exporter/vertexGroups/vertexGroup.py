import math
from time import time

import bpy
import numpy as np
from ....utils.util import getBoneIndices, getIndexLookup, getMeshVertexGroups, calculateVertexFlags

FIELD_TYPES = {
    'position': ('<f4', 3),
    'tangent': ('u1', 4),
    'normal': ('<f2', 4),
    'color': ('u1', 4),
    'boneIndices': ('u1', 4),
    'boneWeights': ('u1', 4),
}
UV_FIELD_TYPE = ('<f2', 2)

EX_DATA_LAYOUTS = {
    1: [('normal', 'normal')],
    3: [('normal', 'normal')],
    4: [('normal', 'normal')],
    5: [('normal', 'normal'), ('uv3', 2)],
    7: [('uv2', 1), ('normal', 'normal')],
    8: [('uv2', 1), ('normal', 'normal'), ('uv3', 2)],
    10: [('uv2', 1), ('color', 'color'), ('normal', 'normal')],
    11: [('uv2', 1), ('color', 'color'), ('normal', 'normal'), ('uv3', 2)],
    12: [('normal', 'normal'), ('uv3', 2), ('uv4', 3), ('uv5', 4)],
    14: [('normal', 'normal'), ('uv3', 2), ('uv4', 3)],
}

def vertexLayout(vertexFlags):
    layout = [('position', 'position'), ('tangent', 'tangent'), ('uv1', 0)]
    if vertexFlags == 0:
        layout.append(('normal', 'normal'))
    if vertexFlags in {1, 4, 5, 12, 14}:
        layout.append(('uv2', 1))
    if vertexFlags in {7, 8, 10, 11}:
        layout += [('boneIndices', 'boneIndices'), ('boneWeights', 'boneWeights')]
    if vertexFlags in {3, 4, 5, 12, 14}:
        layout.append(('color', 'color'))
    return layout

def layoutType(layout):
    return np.dtype([(name, *(UV_FIELD_TYPE if isinstance(source, int) else FIELD_TYPES[source])) for name, source in layout])

def packRecords(layout, columns, count):
    records = np.zeros(count, layoutType(layout))
    for name, source in layout:
        records[name] = columns[source]
    return records.tobytes()

def getValues(collection, attribute, count, width):
    values = np.empty(count * width, np.float32)
    collection.foreach_get(attribute, values)
    return values.reshape(count, width)

def toHalfFloats(values):
    halves = values.astype('<f2')
    if (np.isinf(halves) & np.isfinite(values)).any():
        raise OverflowError("float too large to pack with e format")
    return halves

def toBytes(values):
    ints = np.asarray(values).astype(np.int64)
    if ((ints < 0) | (ints > 255)).any():
        raise ValueError("byte must be in range(0, 256)")
    return ints.astype(np.uint8)

class c_vertexGroup(object):
    def __init__(self, vertexGroupIndex, vertexesStart):
        self.vertexGroupIndex = vertexGroupIndex
        self.vertexGroupStart = vertexesStart

        def get_blenderObjects(self):
            objs = {}
            
            meshes = getMeshVertexGroups('WMB')[vertexGroupIndex]
            
            blenderObjects = []
            for obj in meshes:
                if len(obj.data.uv_layers) == 0:
                    obj.data.uv_layers.new()
                obj.data.calc_tangents()
                blenderObjects.append(obj)

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
        
        calculated_vertex_flags = calculateVertexFlags(self.blenderObjects[0])
        if calculated_vertex_flags != None:
            self.vertexFlags = calculated_vertex_flags

        if self.vertexFlags == 0:
            self.vertexExDataSize = 0
        if self.vertexFlags in {1, 3, 4}:
            self.vertexExDataSize = 8       
        elif self.vertexFlags in {5, 7}:                                          
            self.vertexExDataSize = 12                                    
        elif self.vertexFlags in {8, 10, 14}:
            self.vertexExDataSize = 16
        elif self.vertexFlags in {11, 12}:
            self.vertexExDataSize = 20

        if not hasattr(self, "vertexFlags") or not hasattr(self, "vertexExDataSize"):
            print(" - Vertex Group Error: Could not determine flags or ExData size!")

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

        def get_boneWeights(bvertex, vertexNumber, groupNames, boneIndices, boneMapIndices, boneSetIndices):
            boneIndexes = []
            boneWeights = []
            # Bone Indices
            for groupRef in bvertex.groups:
                if len(boneIndexes) < 4:
                    boneGroupName = groupNames[groupRef.group]
                    boneID = boneIndices.get(boneGroupName)

                    boneMapIndx = boneMapIndices[boneID]
                    boneSetIndx = boneSetIndices[boneMapIndx]

                    boneIndexes.append(boneSetIndx)

            if len(boneIndexes) == 0:
                print(vertexNumber ,"- Vertex Weights Error: Vertex has no assigned groups. At least 1 required. Try using Blender's [Select -> Select All By Trait > Ungrouped Verts] function to find them.")

            while len(boneIndexes) < 4:
                boneIndexes.append(0)

            # Bone Weights
            weights = [group.weight for group in bvertex.groups]
            weightsSum = sum(weights)

            if len(weights) >  4:
                print(vertexNumber, "- Vertex Weights Error: Vertex has weights assigned to more than 4 groups. Try using Blender's [Weights -> Limit Total] function.")

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
                print(vertexNumber, "- Vertex Weights Error: Vertex has a total weight not equal to 1.0. Try using Blender's [Weights -> Normalize All] function.")

            return boneIndexes, boneWeights

        def get_columns(obj, sources, vertexStart, boneLookups):
            mesh = obj.data
            loopCount = len(mesh.loops)
            loopVertices = np.empty(loopCount, np.int32)
            mesh.loops.foreach_get('vertex_index', loopVertices)
            used, firstLoops = np.unique(loopVertices, return_index=True)
            count = len(used)
            uvSlots = sorted(source for source in sources if isinstance(source, int))

            for uvSlot in uvSlots:
                if uvSlot > len(mesh.uv_layers)-1:
                    print(" - UV Maps Error: Not enough UV Map layers! (Tried accessing UV layer number", uvSlot + 1, "of object", obj.name, "but it does not exist. Adding one!")
                    mesh.uv_layers.new()
            if 'color' in sources and len(mesh.color_attributes) == 0:
                print("Object had no vertex colour layer when one was expected - creating one.")
                mesh.color_attributes.active_color = mesh.color_attributes.new("Col", 'BYTE_COLOR', 'CORNER')

            columns = {}
            positions = getValues(mesh.vertices, 'co', len(mesh.vertices), 3)[used]
            columns['position'] = np.stack((positions[:, 0], positions[:, 2], -positions[:, 1]), axis=1)

            tangents = getValues(mesh.loops, 'tangent', loopCount, 3)[firstLoops].astype(np.float64)
            signs = getValues(mesh.loops, 'bitangent_sign', loopCount, 1)[firstLoops, 0].astype(np.float64)
            columns['tangent'] = toBytes(np.stack((
                tangents[:, 0] * 127 + 127.0,
                tangents[:, 2] * 127 + 127.0,
                -tangents[:, 1] * 127 + 127.0,
                -signs * 127.0 + 128.0,
            ), axis=1))

            if 'normal' in sources:
                normals = getValues(mesh.loops, 'normal', loopCount, 3)[firstLoops].astype(np.float64)
                columns['normal'] = toHalfFloats(np.stack((normals[:, 0], normals[:, 2], -normals[:, 1], np.zeros(count)), axis=1))

            for uvSlot in uvSlots:
                uvs = getValues(mesh.uv_layers[uvSlot].data, 'uv', loopCount, 2)[firstLoops].astype(np.float64)
                columns[uvSlot] = toHalfFloats(np.stack((uvs[:, 0], 1 - uvs[:, 1]), axis=1))

            if 'color' in sources:
                # color_srgb is the byte value / 255 for byte and float color attributes alike
                colorLayer = mesh.color_attributes.active_color or mesh.color_attributes[0]
                if colorLayer.domain == 'POINT':
                    colors = getValues(colorLayer.data, 'color_srgb', len(mesh.vertices), 4)[used].astype(np.float64)
                else:
                    colors = getValues(colorLayer.data, 'color_srgb', loopCount, 4)[firstLoops].astype(np.float64)
                columns['color'] = toBytes(np.clip(colors, 0.0, 1.0) * 255)

            if boneLookups is not None:
                bones = np.zeros((count, 4), np.int64)
                weights = np.zeros((count, 4), np.int64)
                vertices = mesh.vertices
                for row, vertexIndex in enumerate(used.tolist()):
                    bones[row], weights[row] = get_boneWeights(vertices[vertexIndex], vertexStart + row, *boneLookups)
                columns['boneIndices'] = toBytes(bones)
                columns['boneWeights'] = toBytes(weights)

            return columns, count

        def get_vertexesData(self):
            layout = vertexLayout(self.vertexFlags)
            exDataLayout = EX_DATA_LAYOUTS.get(self.vertexFlags, [])
            sources = {source for _, source in layout + exDataLayout}
            vertexBuffers = []
            exDataBuffers = []
            vertexCount = 0
            for obj in self.blenderObjects:
                print('   [>] Generating vertex data for object', obj.name)
                boneLookups = None
                if self.vertexFlags not in {0, 1, 3, 4, 5, 12, 14}:
                    boneSet = get_boneSet(self, obj["boneSetIndex"])
                    if 'boneIndices' in sources:
                        boneLookups = (
                            [group.name for group in obj.vertex_groups],
                            getBoneIndices("WMB"),
                            getIndexLookup(self.boneMap),
                            getIndexLookup(boneSet),
                        )
                if len(obj.data.loops) == 0:
                    continue

                columns, count = get_columns(obj, sources, vertexCount, boneLookups)
                vertexBuffers.append(packRecords(layout, columns, count))
                if exDataLayout:
                    exDataBuffers.append(packRecords(exDataLayout, columns, count))
                vertexCount += count

            return b''.join(vertexBuffers), b''.join(exDataBuffers)

        def get_indexes(self):
            indexes = []
            indexesOffset = 0
            for obj in self.blenderObjects:
                loopVertices = np.empty(len(obj.data.loops), np.int32)
                obj.data.loops.foreach_get('vertex_index', loopVertices)
                indexes.append(loopVertices.astype(np.int64) + indexesOffset)
                indexesOffset += len(obj.data.vertices)
            indexes = np.concatenate(indexes) if indexes else np.zeros(0, np.int64)

            # Reverse this loop order
            triangles = len(indexes) - len(indexes) % 3
            indexes[:triangles] = indexes[:triangles].reshape(-1, 3)[:, [0, 2, 1]].reshape(-1)

            return indexes.astype('<u4').tobytes()

        self.vertexSize = 28                                            # 28

        self.vertexOffset = self.vertexGroupStart                       
        self.vertexExDataOffset = self.vertexOffset + numVertices * self.vertexSize

        self.unknownOffset = [0, 0]                                      # Don't question it, it's unknown okay?

        self.unknownSize = [0, 0]                                        # THIS IS UNKOWN TOO OKAY? LEAVE ME BE

        self.numVertexes = numVertices                                            

        self.indexBufferOffset = self.vertexExDataOffset + self.numVertexes * self.vertexExDataSize

        self.numIndexes = get_numIndexes(self)

        self.vertexBuffer, self.vertexExDataBuffer = get_vertexesData(self)
        
        self.indexBuffer = get_indexes(self)

        self.vertexGroupSize = (self.numVertexes * self.vertexSize) + (self.numVertexes * self.vertexExDataSize) + (self.numIndexes * 4)

def clamp(val, minV, maxV):
    return maxV if val > maxV else \
        minV if val < minV else val
