from blender2nier.bones.bones import *
from blender2nier.boneIndexTranslateTable.boneIndexTranslateTable import *
from blender2nier.vertexGroups.create_vertexGroups import *
from blender2nier.batches.create_batches import *
from blender2nier.lods.lods import *
from blender2nier.boneMap.boneMap import *
from blender2nier.materials.create_materials import *
from blender2nier.meshes.create_meshes import *
from blender2nier.meshes.meshMaterials import *

class c_generate_data(object):
    def __init__(self):
        currentOffset = 0

        self.header_Offset = currentOffset
        self.header_Size = 136
        currentOffset += self.header_Size
        print('header_Size: ', self.header_Size)

        currentOffset += (currentOffset % 16)

        self.bones_Offset = currentOffset
        self.bones = c_bones()
        self.bones_Size = self.bones.bones_StructSize
        currentOffset += self.bones_Size
        print('bones_Size: ', self.bones_Size)

        currentOffset += (currentOffset % 16)

        self.boneIndexTranslateTable_Offset = currentOffset
        self.boneIndexTranslateTable = c_boneIndexTranslateTable(self.bones)
        self.boneIndexTranslateTable_Size = self.boneIndexTranslateTable.boneIndexTranslateTable_StructSize
        currentOffset += self.boneIndexTranslateTable_Size
        print('boneIndexTranslateTable_Size: ', self.boneIndexTranslateTable_Size)

        currentOffset += (currentOffset % 16)

        self.vertexGroups_Offset = currentOffset
        self.vertexGroups = c_vertexGroups(self.vertexGroups_Offset)
        self.vertexGroups_Size = self.vertexGroups.vertexGroups_StructSize
        currentOffset += self.vertexGroups_Size
        print('vertexGroups_Size: ', self.vertexGroups_Size)

        currentOffset += (currentOffset % 16)

        self.batches_Offset = currentOffset
        self.batches = c_batches()
        self.batches_Size = self.batches.batches_StructSize
        currentOffset += self.batches_Size
        print('batches_Size: ', self.batches_Size)

        self.lods_Offset = currentOffset
        self.lods = c_lods(self.lods_Offset, self.batches)
        self.lods_Size = self.lods.lods_StructSize
        currentOffset += self.lods_Size
        print('lods_Size: ', self.lods_Size)

        currentOffset += 16 - (currentOffset % 16)

        self.meshMaterials_Offset = currentOffset
        self.meshMaterials_Size = len(self.batches.batches) * 8
        currentOffset += self.meshMaterials_Size
        print('meshMaterials_Size: ', self.meshMaterials_Size)

        currentOffset += (currentOffset % 16)

        self.boneMap_Offset = currentOffset
        self.boneMap = c_boneMap(self.bones)
        self.boneMap_Size = self.boneMap.boneMap_StructSize
        currentOffset += self.boneMap_Size
        print('boneMap_Size: ', self.boneMap_Size)

        self.meshes_Offset = currentOffset
        self.meshes = c_meshes(self.meshes_Offset, self.bones)
        self.meshes_Size = self.meshes.meshes_StructSize
        currentOffset += self.meshes_Size
        print('meshes_Size: ', self.meshes_Size)

        currentOffset += (currentOffset % 16)

        self.materials_Offset = currentOffset
        self.materials = c_materials(self.materials_Offset)
        self.materials_Size = self.materials.materials_StructSize
        currentOffset += self.materials_Size
        print('materials_Size: ', self.materials_Size)

        self.meshMaterials = c_meshMaterials(self.meshes)
        self.meshMaterials_Size = self.meshMaterials.meshMaterials_StructSize