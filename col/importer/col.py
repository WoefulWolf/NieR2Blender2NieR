# https://github.com/Kerilk/bayonetta_tools/blob/master/binary_templates/Nier%20Automata%20col.bt

from ...util import *

class Header:
    def __init__(self, colFile):
        self.id = colFile.read(4)
        self.version = "%08x" % (to_uint(colFile.read(4)))

        self.offsetNames = to_uint(colFile.read(4))
        self.nameCount = to_uint(colFile.read(4))

        self.offsetMeshes = to_uint(colFile.read(4))
        self.meshCount = to_uint(colFile.read(4))

        self.offsetBoneMap = to_uint(colFile.read(4))
        self.boneMapCount = to_uint(colFile.read(4))

        self.offsetBoneMap2 = to_uint(colFile.read(4))
        self.boneMap2Count = to_uint(colFile.read(4))

        self.offsetMeshMap = to_uint(colFile.read(4))
        self.meshMapCount = to_uint(colFile.read(4))

        self.offsetColTreeNodes = to_uint(colFile.read(4))
        self.colTreeNodesCount = to_uint(colFile.read(4))

class NameGroups:
    def __init__(self, colFile, header):
        self.offsetNames = []
        for i in range(header.nameCount):
            self.offsetNames.append(to_uint(colFile.read(4)))

        self.names = []
        for offsetName in self.offsetNames:
            colFile.seek(offsetName)
            self.names.append(to_string(colFile.read(256)))

class Batch:
    def __init__(self, colFile, batchType):
        if batchType == 2:
            self.boneIndex = to_int(colFile.read(4))
            self.offsetVertices = to_uint(colFile.read(4))
            self.vertexCount = to_uint(colFile.read(4))
            self.offsetIndices = to_uint(colFile.read(4))
            self.indexCount = to_uint(colFile.read(4))

            returnPos = colFile.tell()

            colFile.seek(self.offsetVertices)
            self.vertices = []
            self.vec4Vertices = []
            for i in range(self.vertexCount):
                x = to_float(colFile.read(4))
                y = to_float(colFile.read(4))
                z = to_float(colFile.read(4))
                w = to_float(colFile.read(4))
                self.vertices.append([x, y, z])
                self.vec4Vertices.append([x, y, z, w])

            colFile.seek(self.offsetIndices)
            self.indices = []
            self.rawIndices = []
            for i in range(round(self.indexCount / 3)):
                v0 = to_ushort(colFile.read(2))
                v1 = to_ushort(colFile.read(2))
                v2 = to_ushort(colFile.read(2))
                self.rawIndices.append(v0)
                self.rawIndices.append(v1)
                self.rawIndices.append(v2)
                self.indices.append([v2, v1, v0])

            colFile.seek(returnPos)

        elif batchType == 3:
            self.offsetVertices = to_uint(colFile.read(4))
            self.vertexCount = to_uint(colFile.read(4))
            self.offsetIndices = to_uint(colFile.read(4))
            self.indexCount = to_uint(colFile.read(4))

            returnPos = colFile.tell()
        else:
            print("UNKNOWN BATCH TYPE!")

class Mesh:
    def __init__(self, colFile):
        self.collisionType = to_uint(colFile.read(1))
        self.slidable = to_uint(colFile.read(1))
        self.unknownByte = to_uint(colFile.read(1))
        self.surfaceType = to_uint(colFile.read(1))
        
        self.nameIndex = to_uint(colFile.read(4))
        self.batchType = to_uint(colFile.read(4))
        self.offsetBatches = to_uint(colFile.read(4))
        self.batchCount = to_uint(colFile.read(4))

        returnPos = colFile.tell()

        colFile.seek(self.offsetBatches)
        self.batches = []
        for i in range(self.batchCount):
            self.batches.append(Batch(colFile, self.batchType))

        colFile.seek(returnPos)

class ColTreeNode:
    def __init__(self, colFile):
        self.p1 = [to_float(colFile.read(4)), to_float(colFile.read(4)), to_float(colFile.read(4))]
        self.p2 = [to_float(colFile.read(4)), to_float(colFile.read(4)), to_float(colFile.read(4))]

        self.left = to_int(colFile.read(4))
        self.right = to_int(colFile.read(4))

        self.offsetMeshIndices = to_uint(colFile.read(4))
        self.meshIndexCount = to_uint(colFile.read(4))

        self.meshIndices = []
        if self.offsetMeshIndices != 0 and self.meshIndexCount != 0:
            returnPos = colFile.tell()
            colFile.seek(self.offsetMeshIndices)
            for i in range(self.meshIndexCount):
                self.meshIndices.append(to_uint(colFile.read(4)))
            colFile.seek(returnPos)

class Col:
    def __init__(self, colFile):
        self.header = Header(colFile)

        colFile.seek(self.header.offsetNames)
        self.nameGroups = NameGroups(colFile, self.header)

        colFile.seek(self.header.offsetMeshes)
        self.meshes = []
        for i in range(self.header.meshCount):
            self.meshes.append(Mesh(colFile))

        self.meshMaps = []
        if self.header.meshMapCount > 0:
            colFile.seek(self.header.offsetMeshMap)
            for i in range(self.header.meshMapCount):
                self.meshMaps.append(to_uint(colFile.read(4)))

        self.boneMaps = []
        if self.header.boneMapCount > 0:
            colFile.seek(self.header.offsetBoneMap)
            for i in range(self.header.boneMapCount):
                self.boneMaps.append(to_uint(colFile.read(4)))

        self.boneMaps2 = []
        if self.header.boneMap2Count > 0:
            colFile.seek(self.header.offsetBoneMap2)
            for i in range(self.header.boneMap2Count):
                self.boneMaps2.append(to_uint(colFile.read(4)))

        self.colTreeNodes = []
        if self.header.colTreeNodesCount > 0:
            colFile.seek(self.header.offsetColTreeNodes)
            for i in range(self.header.colTreeNodesCount):
                self.colTreeNodes.append(ColTreeNode(colFile))