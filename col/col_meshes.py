import bpy
from .col_batch import Batch
from ..util import objectsInCollectionInOrder

collisionTypes = [
    ("-1", "UNKNOWN", ""),
    ("3", "Block Actors", "If modifier is enabled, this will not block players who are jumping (e.g. to prevent accidentally walking off ledges)."),
    ("88", "Water", ""),
    ("127", "Grabbable Block All", ""),
    ("255", "Block All", "")
]

# Identified by NSA Cloud
surfaceTypes = [
    ("-1", "UNKNOWN", ""),
    ("0", "Concrete1", ""),
    ("1", "Dirt", ""),
    ("2", "Concrete2", ""),
    ("3", "Metal Floor", ""),
    ("4", "Rubble", ""),
    ("5", "Metal Grate", ""),
    ("6", "Gravel", ""),
    ("7", "Rope Bridge", ""),
    ("8", "Grass", ""),
    ("9", "Wood Plank", ""),
    ("11", "Water", ""),
    ("12", "Sand", ""),
    ("13", "Rocky Gravel 1", ""),
    ("15", "Mud", ""),
    ("16", "Rocky Gravel 2", ""),
    ("17", "Concrete 3", ""),
    ("18", "Bunker Floor", ""),
    ("22", "Concrete 4", ""),
    ("23", "Car", ""),
    ("24", "Flowers", "")
]

class Mesh:
    def __init__(self, meshBlenderObject, nameGroups, batchOffset):
        meshIndex = meshBlenderObject.name.split("-")[0]

        self.collisionType = int(meshBlenderObject.collisionType)
        if self.collisionType == -1:
            self.collisionType = meshBlenderObject["UNKNOWN_collisionType"]
        self.slidable = int(meshBlenderObject.slidable == True)
        self.unknownByte = meshBlenderObject["unknownByte"]
        self.surfaceType = int(meshBlenderObject.surfaceType)
        if self.surfaceType == -1:
            self.surfaceType = meshBlenderObject["UNKNOWN_surfaceType"]

        self.nameIndex = nameGroups.get_nameIndex(meshBlenderObject.name.split("-")[1])
        self.batchType = 2
        self.batchOffset = batchOffset

        self.totalBatchesStructSize = 0
        currentBatchOffset = batchOffset

        # Get the batches for this mesh
        self.batches = []
        for obj in objectsInCollectionInOrder("COL"):
            if obj.type == 'MESH':
                if obj.name.split("-")[0] == meshIndex:
                    newBatch = Batch(obj, currentBatchOffset)
                    self.batches.append(newBatch)
                    currentBatchOffset += newBatch.structSize
                    self.totalBatchesStructSize += newBatch.structSize

        self.batchCount = len(self.batches)

class Meshes:
    def __init__(self, meshesStartOffset, nameGroups):
        
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
        self.meshes = []
        for obj in meshBlenderObjs:
            newMesh = Mesh(obj, nameGroups, currentBatchOffset)
            self.meshes.append(newMesh)
            currentBatchOffset += newMesh.totalBatchesStructSize

        self.structSize = self.meshes[-1].batches[-1].offsetIndices + (self.meshes[-1].batches[-1].indexCount * 2) # I was lazy

from ..util import *

def write_col_meshes(col_file, data):
    col_file.seek(data.offsetMeshes)

    for mesh in data.meshes.meshes:
        write_byte(col_file, mesh.collisionType)
        write_byte(col_file, mesh.slidable)
        write_byte(col_file, mesh.unknownByte)
        write_byte(col_file, mesh.surfaceType)

        write_uInt32(col_file, mesh.nameIndex)
        write_uInt32(col_file, mesh.batchType)
        write_uInt32(col_file, mesh.batchOffset)
        write_uInt32(col_file, mesh.batchCount)
    
    for mesh in data.meshes.meshes:
        col_file.seek(mesh.batchOffset)
        for batch in mesh.batches:
            write_Int32(col_file, batch.boneIndex)
            write_uInt32(col_file, batch.offsetVertices)
            write_uInt32(col_file, batch.vertexCount)
            write_uInt32(col_file, batch.offsetIndices)
            write_uInt32(col_file, batch.indexCount)

            col_file.seek(batch.offsetVertices)
            for vertex in batch.vertices:
                for val in vertex:
                    write_float(col_file, val)

            col_file.seek(batch.offsetIndices)
            for index in batch.indices:
                write_uInt16(col_file, index)