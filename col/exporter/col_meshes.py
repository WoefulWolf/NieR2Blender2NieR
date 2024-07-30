from io import BufferedWriter

import bpy

from .col_batch import BatchT2, BatchT3
from .col_boneMap import BoneMap
from .col_namegroups import NameGroup
from ...utils.ioUtils import write_uInt32, write_byte


class Mesh:
    def __init__(self, meshBlenderObject: bpy.types.Object, nameGroups: NameGroup, batchOffset: int, boneMap: BoneMap):
        meshIndex = meshBlenderObject.name.split("-")[0]

        self.collisionType = int(meshBlenderObject.collisionType)
        if self.collisionType == -1:
            self.collisionType = meshBlenderObject["UNKNOWN_collisionType"]
        self.modifier = int(meshBlenderObject.colModifier)
        self.unknownByte = meshBlenderObject["unknownByte"]
        self.surfaceType = int(meshBlenderObject.surfaceType)
        if self.surfaceType == -1:
            self.surfaceType = meshBlenderObject["UNKNOWN_surfaceType"]

        self.nameIndex = nameGroups.get_nameIndex(meshBlenderObject.name.split("-")[1])
        self.batchType = 2 if len(meshBlenderObject.vertex_groups) <= 1 else 3
        self.batchOffset = batchOffset

        self.totalBatchesStructSize = 0
        batchesDataOffset = batchOffset

        # Get the batches for this mesh
        self.batches = []
        for obj in objectsInCollectionInOrder("COL"):
            if obj.type == 'MESH':
                if obj.name.split("-")[0] == meshIndex:
                    if self.batchType == 2:
                        newBatch = BatchT2(obj, boneMap)
                    else:
                        newBatch = BatchT3(obj, boneMap)

                    self.batches.append(newBatch)
                    self.totalBatchesStructSize += newBatch.headerStructSize
                    batchesDataOffset += newBatch.headerStructSize

        # data offset are only known after all batches are created
        for batch in self.batches:
            batch.setDataOffsets(batchesDataOffset)
            self.totalBatchesStructSize += batch.dataStructSize
            batchesDataOffset += batch.dataStructSize

        self.batchCount = len(self.batches)
        self.totalStructSize = self.totalBatchesStructSize + 20

class Meshes:
    def __init__(self, meshesStartOffset, nameGroups, boneMap: BoneMap, boneMap2: BoneMap):

        # Get all the mesh indices
        meshBlenderObjs = []
        meshIndices = []
        for obj in objectsInCollectionInOrder("COL"):
            if obj.type == 'MESH':
                meshIndex = obj.name.split("-")[0]
                if meshIndex not in meshIndices:
                    meshIndices.append(meshIndex)
                    meshBlenderObjs.append(obj)

        # Get meshes
        batchesStartOffset = meshesStartOffset + (len(meshIndices) * 20)
        currentBatchOffset = batchesStartOffset
        totalMeshesSize = 0
        self.meshes = []
        for obj in meshBlenderObjs:
            newMesh = Mesh(obj, nameGroups, currentBatchOffset, boneMap if len(obj.vertex_groups) <= 1 else boneMap2)
            self.meshes.append(newMesh)
            currentBatchOffset += newMesh.totalBatchesStructSize
            totalMeshesSize += newMesh.totalStructSize

        self.structSize = totalMeshesSize

from ...utils.util import *

def write_col_meshes(col_file: BufferedWriter, data):
    col_file.seek(data.offsetMeshes)

    for mesh in data.meshes.meshes:
        write_byte(col_file, mesh.collisionType)
        write_byte(col_file, mesh.modifier)
        write_byte(col_file, mesh.unknownByte)
        write_byte(col_file, mesh.surfaceType)

        write_uInt32(col_file, mesh.nameIndex)
        write_uInt32(col_file, mesh.batchType)
        write_uInt32(col_file, mesh.batchOffset)
        write_uInt32(col_file, mesh.batchCount)

    for mesh in data.meshes.meshes:
        col_file.seek(mesh.batchOffset)
        for batch in mesh.batches:
            batch.writeHeaderToFile(col_file)
        for batch in mesh.batches:
            batch.writeDataToFile(col_file)
