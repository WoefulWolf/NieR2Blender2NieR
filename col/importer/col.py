# https://github.com/Kerilk/bayonetta_tools/blob/master/binary_templates/Nier%20Automata%20col.bt
from ...utils.ioUtils import to_string, read_uint32, read_int32, read_uint16, read_float, read_uint8


class Header:
    def __init__(self, colFile):
        self.id = colFile.read(4)
        self.version = "%08x" % (read_uint32(colFile))

        self.offsetNames = read_uint32(colFile)
        self.nameCount = read_uint32(colFile)

        self.offsetMeshes = read_uint32(colFile)
        self.meshCount = read_uint32(colFile)

        self.offsetBoneMap = read_uint32(colFile)
        self.boneMapCount = read_uint32(colFile)

        self.offsetBoneMap2 = read_uint32(colFile)
        self.boneMap2Count = read_uint32(colFile)

        self.offsetMeshMap = read_uint32(colFile)
        self.meshMapCount = read_uint32(colFile)

        self.offsetColTreeNodes = read_uint32(colFile)
        self.colTreeNodesCount = read_uint32(colFile)

class NameGroups:
    def __init__(self, colFile, header):
        self.offsetNames = []
        for i in range(header.nameCount):
            self.offsetNames.append(read_uint32(colFile))

        self.names = []
        for offsetName in self.offsetNames:
            colFile.seek(offsetName)
            self.names.append(to_string(colFile.read(256)))

class Batch:
    def __init__(self, colFile, batchType):
        if batchType == 2:
            self.boneIndex = read_int32(colFile)
            self.offsetVertices = read_uint32(colFile)
            self.vertexCount = read_uint32(colFile)
            self.offsetIndices = read_uint32(colFile)
            self.indexCount = read_uint32(colFile)

            returnPos = colFile.tell()

            colFile.seek(self.offsetVertices)
            self.vertices = []
            for i in range(self.vertexCount):
                x = read_float(colFile)
                y = read_float(colFile)
                z = read_float(colFile)
                w = read_float(colFile)
                self.vertices.append([x, y, z])

            colFile.seek(self.offsetIndices)
            self.indices = []
            for i in range(round(self.indexCount / 3)):
                v0 = read_uint16(colFile)
                v1 = read_uint16(colFile)
                v2 = read_uint16(colFile)
                self.indices.append([v2, v1, v0])

            colFile.seek(returnPos)

        elif batchType == 3:
            self.offsetVertices = read_uint32(colFile)
            self.vertexCount = read_uint32(colFile)
            self.offsetIndices = read_uint32(colFile)
            self.indexCount = read_uint32(colFile)

            returnPos = colFile.tell()

            colFile.seek(self.offsetVertices)
            self.vertices = []
            self.boneWeights = []
            self.bones = []
            for i in range(self.vertexCount):
                self.vertices.append([
                    read_float(colFile),
                    read_float(colFile),
                    read_float(colFile),
                ])
                read_float(colFile)     # w

                self.boneWeights.append([
                    read_float(colFile),
                    read_float(colFile),
                    read_float(colFile),
                    read_float(colFile),
                ])

                self.bones.append([
                    read_uint32(colFile),
                    read_uint32(colFile),
                    read_uint32(colFile),
                    read_uint32(colFile),
                ])

            colFile.seek(self.offsetIndices)
            self.indices = []
            for i in range(round(self.indexCount / 3)):
                v0 = read_uint16(colFile)
                v1 = read_uint16(colFile)
                v2 = read_uint16(colFile)
                self.indices.append([v2, v1, v0])

            colFile.seek(returnPos)
        else:
            print("UNKNOWN BATCH TYPE!")

class Mesh:
    def __init__(self, colFile):
        self.collisionType = read_uint8(colFile)
        self.modifier = read_uint8(colFile)
        self.unknownByte = read_uint8(colFile)
        self.surfaceType = read_uint8(colFile)
        
        self.nameIndex = read_uint32(colFile)
        self.batchType = read_uint32(colFile)
        self.offsetBatches = read_uint32(colFile)
        self.batchCount = read_uint32(colFile)

        returnPos = colFile.tell()

        colFile.seek(self.offsetBatches)
        self.batches = []
        for i in range(self.batchCount):
            self.batches.append(Batch(colFile, self.batchType))

        colFile.seek(returnPos)

class ColTreeNode:
    def __init__(self, colFile):
        self.p1 = [read_float(colFile), read_float(colFile), read_float(colFile)]
        self.p2 = [read_float(colFile), read_float(colFile), read_float(colFile)]

        self.left = read_int32(colFile)
        self.right = read_int32(colFile)

        self.offsetMeshIndices = read_uint32(colFile)
        self.meshIndexCount = read_uint32(colFile)

        self.meshIndices = []
        if self.offsetMeshIndices != 0 and self.meshIndexCount != 0:
            returnPos = colFile.tell()
            colFile.seek(self.offsetMeshIndices)
            for i in range(self.meshIndexCount):
                self.meshIndices.append(read_uint32(colFile))
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
                self.meshMaps.append(read_uint32(colFile))

        self.boneMaps = []
        if self.header.boneMapCount > 0:
            colFile.seek(self.header.offsetBoneMap)
            for i in range(self.header.boneMapCount):
                self.boneMaps.append(read_uint32(colFile))

        self.boneMaps2 = []
        if self.header.boneMap2Count > 0:
            colFile.seek(self.header.offsetBoneMap2)
            for i in range(self.header.boneMap2Count):
                self.boneMaps2.append(read_uint32(colFile))

        self.colTreeNodes = []
        if self.header.colTreeNodesCount > 0:
            colFile.seek(self.header.offsetColTreeNodes)
            for i in range(self.header.colTreeNodesCount):
                self.colTreeNodes.append(ColTreeNode(colFile))