from io import BufferedWriter

import bpy

from .col_batch import BatchT2, BatchT3
from .col_boneMap import BoneMap
from .col_namegroups import NameGroup
from ...utils.ioUtils import write_uInt32, write_byte


class Mesh:
    def __init__(self, meshIndex: int, objs: list[bpy.types.Object], nameGroups: NameGroup, batchOffset: int, boneMap: BoneMap):
        bObj = objs[0]

        self.collisionType = int(bObj.col_mesh_props.col_type)
        if self.collisionType == -1:
            self.collisionType = bObj.col_mesh_props.unk_col_type
        self.modifier = int(bObj.col_mesh_props.modifier)
        self.unknownByte = bObj.col_mesh_props.unk_byte
        self.surfaceType = int(bObj.col_mesh_props.surface_type)
        if self.surfaceType == -1:
            self.surfaceType = bObj.col_mesh_props.unk_surface_type

        self.nameIndex = nameGroups.get_nameIndex(getMeshName(bObj))
        self.batchType = 2 if len(bObj.vertex_groups) <= 1 else 3
        self.batchOffset = batchOffset

        self.totalBatchesStructSize = 0
        batchesDataOffset = batchOffset

        # Get the batches for this mesh
        self.batches = []
        for obj in objs:
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
        meshGroups = getColMeshGroups("COL")

        # Get meshes
        batchesStartOffset = meshesStartOffset + (len(meshGroups) * 20)
        currentBatchOffset = batchesStartOffset
        totalMeshesSize = 0
        self.meshes = []
        for meshIdx, group in enumerate(meshGroups):
            obj = group[0]
            newMesh = Mesh(meshIdx, group, nameGroups, currentBatchOffset, boneMap if len(obj.vertex_groups) <= 1 else boneMap2)
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
