from dataclasses import dataclass
from io import BufferedWriter
from typing import List
import bmesh
import bpy
import numpy as np

from ...utils.ioUtils import write_Int32, write_float, write_uInt32, write_uInt16
from .col_boneMap import BoneMap


class Batch:
    def __init__(self, bObj: bpy.types.Object):
        self.offsetVertices = -1
        self.offsetIndices = -1
        self.dataAlignmentPad = 0
        self.headerStructSize = -1
        self.vertexStructSize = -1
        self.dataStructSize = -1

        self.vertexCount = len(bObj.data.vertices)
        self.indexCount = len(bObj.data.polygons) * 3
        self.indices = []

        bm = bmesh.new()
        bm.from_mesh(bObj.data)
        bm.verts.index_update()
        bm.faces.index_update()

        self.vertexPositions = []
        for vertex in bm.verts:
            vertexVec4 = [vertex.co[0], vertex.co[1], vertex.co[2], 1]
            self.vertexPositions.append(vertexVec4)

        for face in bm.faces:
            for vert in reversed(face.verts):
                self.indices.append(vert.index)

        bm.to_mesh(bObj.data)
        bm.free()

    def setDataOffsets(self, startOffset: int):
        # 16 byte aligned
        self.dataAlignmentPad = (16 - (startOffset % 16)) % 16
        self.offsetVertices = startOffset + self.dataAlignmentPad
        self.offsetIndices = self.offsetVertices + self.vertexStructSize
        self.dataStructSize += self.dataAlignmentPad

    def writeHeaderToFile(self, file: BufferedWriter):
        raise NotImplementedError()

    def writeDataToFile(self, file: BufferedWriter):
        raise NotImplementedError()

class BatchT2(Batch):
    def __init__(self, bObj: bpy.types.Object, boneMap: BoneMap):
        super().__init__(bObj)

        if len(bObj.vertex_groups) == 0:
            self.boneIndex = -1
        else:
            self.boneIndex = boneMap.boneToMapIndex[bObj.vertex_groups[0].name]


        vertexOffset = [0, 0, 0, 0]
        if self.boneIndex != -1:
            boneName = bObj.vertex_groups[0].name
            parentAmtObj = bObj.parent
            bone = parentAmtObj.pose.bones[boneName]
            boneGlobalLoc = parentAmtObj.matrix_world @ bone.matrix @ bone.location
            vertexOffset[:3] = [boneGlobalLoc[0], boneGlobalLoc[2], -boneGlobalLoc[1]]
        
        self.vertices = np.array(self.vertexPositions) - np.array(vertexOffset)

        self.headerStructSize = 5 * 4
        self.vertexStructSize = self.vertexCount * 16
        self.dataStructSize = self.vertexStructSize + self.indexCount * 2

    def writeHeaderToFile(self, file: BufferedWriter):
        write_Int32(file, self.boneIndex)
        write_uInt32(file, self.offsetVertices)
        write_uInt32(file, self.vertexCount)
        write_uInt32(file, self.offsetIndices)
        write_uInt32(file, self.indexCount)

    def writeDataToFile(self, file: BufferedWriter):
        file.seek(self.offsetVertices)
        for vertex in self.vertices:
            for coord in vertex:
                write_float(file, coord)

        file.seek(self.offsetIndices)
        for index in self.indices:
            write_uInt16(file, index)

@dataclass
class RiggedVertexData:
    position: List[float]
    weights: List[float]
    bones: List[int]

class BatchT3(Batch):
    def __init__(self, bObj: bpy.types.Object, boneMap: BoneMap):
        super().__init__(bObj)

        self.vertices: List[RiggedVertexData] = []
        vertex: bpy.types.MeshVertex
        for i, vertex in enumerate(bObj.data.vertices):
            vData = RiggedVertexData(
                position=self.vertexPositions[i],
                weights=[0, 0, 0, 0],
                bones=[0, 0, 0, 0],
            )
            vertexGroup: bpy.types.VertexGroupElement
            for i, vertexGroup in enumerate(vertex.groups):
                vData.weights[i] = vertexGroup.weight
                groupName = bObj.vertex_groups[vertexGroup.group].name
                vData.bones[i] = boneMap.boneToMapIndex[groupName]

            zipped = zip(vData.weights, vData.bones)
            sortedZipped = sorted(list(zipped), key=lambda x: x[0], reverse=True)
            vData.weights, vData.bones = zip(*sortedZipped)

            self.vertices.append(vData)
        
        self.headerStructSize = 4 * 4
        self.vertexStructSize = self.vertexCount * 48
        self.dataStructSize = self.vertexStructSize + self.indexCount * 2

    def writeHeaderToFile(self, file: BufferedWriter):
        write_uInt32(file, self.offsetVertices)
        write_uInt32(file, self.vertexCount)
        write_uInt32(file, self.offsetIndices)
        write_uInt32(file, self.indexCount)

    def writeDataToFile(self, file: BufferedWriter):
        file.seek(self.offsetVertices)
        for vertex in self.vertices:
            for coord in vertex.position:
                write_float(file, coord)
            for weight in vertex.weights:
                write_float(file, weight)
            for bone in vertex.bones:
                write_Int32(file, bone)

        file.seek(self.offsetIndices)
        for index in self.indices:
            write_uInt16(file, index)