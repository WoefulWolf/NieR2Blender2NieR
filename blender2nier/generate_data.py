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
    currentOffset = 0

    header_Offset = currentOffset
    header_Size = 136
    currentOffset += header_Size
    print('header_Size: ', header_Size)

    bones_Offset = currentOffset
    bones = c_bones()
    bones_Size = bones.bones_StructSize
    currentOffset += bones_Size
    print('bones_Size: ', bones_Size)

    boneIndexTranslateTable_Offset = currentOffset
    boneIndexTranslateTable = c_boneIndexTranslateTable(bones)
    boneIndexTranslateTable_Size = boneIndexTranslateTable.boneIndexTranslateTable_StructSize
    currentOffset += boneIndexTranslateTable_Size
    print('boneIndexTranslateTable_Size: ', boneIndexTranslateTable_Size)

    vertexGroups_Offset = currentOffset
    vertexGroups = c_vertexGroups(vertexGroups_Offset)
    vertexGroups_Size = vertexGroups.vertexGroups_StructSize
    currentOffset += vertexGroups_Size
    print('vertexGroups_Size: ', vertexGroups_Size)

    batches_Offset = currentOffset
    batches = c_batches()
    batches_Size = batches.batches_StructSize
    currentOffset += batches_Size
    print('batches_Size: ', batches_Size)

    lods_Offset = currentOffset
    lods = c_lods(lods_Offset, batches)
    lods_Size = lods.lods_StructSize
    currentOffset += lods_Size
    print('lods_Size: ', lods_Size)

    meshMaterials_Offset = currentOffset
    meshMaterials_Size = len(batches.batches) * 8
    currentOffset += meshMaterials_Size

    boneMap_Offset = currentOffset
    boneMap = c_boneMap(bones)
    boneMap_Size = boneMap.boneMap_StructSize
    currentOffset += boneMap_Size
    print('boneMap_Size: ', boneMap_Size)

    meshes_Offset = currentOffset
    meshes = c_meshes(meshes_Offset, bones)
    meshes_Size = meshes.meshes_StructSize
    currentOffset += meshes_Size

    materials_Offset = currentOffset
    materials = c_materials(materials_Offset)
    materials_Size = materials.materials_StructSize
    currentOffset += materials_Size
    print('materials_Size: ', materials_Size)

    meshMaterials = c_meshMaterials(meshes)
    meshMaterials_Size = meshMaterials.meshMaterials_StructSize