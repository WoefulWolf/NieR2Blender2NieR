from .batches.create_batches import c_batches
from .boneIndexTranslateTable.boneIndexTranslateTable import *
from .boneMap.boneMap import *
from .boneSet.boneSet import *
from .bones.bones import *
from .colTreeNodes.colTreeNodes import *
from .lods.create_lods import *
from .materials.create_materials import *
from .meshes.create_meshes import *
from .meshes.meshMaterials import *
from .unknownWorldData.unknownWorldData import *
from .vertexGroups.create_vertexGroups import *


class c_generate_data(object):
    def __init__(self):
        hasArmature = False
        hasColTreeNodes = False
        hasUnknownWorldData = False

        for obj in bpy.data.collections['WMB'].all_objects:
            if obj.type == 'ARMATURE':
                print('Armature found, exporting bones structures.')
                hasArmature = True

        if 'colTreeNodes' in bpy.context.scene:
            hasColTreeNodes = True

        if 'unknownWorldData' in bpy.context.scene:
            hasUnknownWorldData = True

        # Generate custom boneSets from Blender vertex groups
        if hasArmature:
            self.b_boneSets = c_b_boneSets()

        currentOffset = 0

        self.header_Offset = currentOffset
        self.header_Size = 136
        currentOffset += self.header_Size
        print('header_Size: ', self.header_Size)

        currentOffset += (currentOffset % 16)

        if hasArmature:
            self.boneIndexTranslateTable = c_boneIndexTranslateTable()

            self.bones_Offset = currentOffset
            self.bones = c_bones()
            self.numBones = len(self.bones.bones)
            self.bones_Size = self.bones.bones_StructSize
            currentOffset += self.bones_Size
            print('bones_Size: ', self.bones_Size)

            currentOffset += (currentOffset % 16)

            self.boneIndexTranslateTable_Offset = currentOffset
            self.boneIndexTranslateTable_Size = self.boneIndexTranslateTable.boneIndexTranslateTable_StructSize
            currentOffset += self.boneIndexTranslateTable_Size
            print('boneIndexTranslateTable_Size: ', self.boneIndexTranslateTable_Size)
        else:
            self.bones_Offset = 0
            self.bones = None
            self.numBones = 0
            self.bones_Size = 0
            self.boneIndexTranslateTable_Offset = 0
            self.boneIndexTranslateTable_Size = 0


        currentOffset += (currentOffset % 16)

        self.vertexGroups_Offset = currentOffset
        self.vertexGroups = c_vertexGroups(self.vertexGroups_Offset)
        self.vertexGroupsCount = len(self.vertexGroups.vertexGroups)
        self.vertexGroups_Size = self.vertexGroups.vertexGroups_StructSize
        currentOffset += self.vertexGroups_Size
        print('vertexGroups_Size: ', self.vertexGroups_Size)

        currentOffset += (currentOffset % 16)

        if hasArmature:
            self.boneMap = c_boneMap(self.bones)
            self.numBoneMap = len(self.boneMap.boneMap)
        else:
            self.boneMap = None
            self.numBoneMap = 0

        self.batches_Offset = currentOffset
        self.batches = c_batches(self.vertexGroupsCount)
        self.batches_Size = self.batches.batches_StructSize
        currentOffset += self.batches_Size
        print('batches_Size: ', self.batches_Size)

        currentOffset += 52

        # Generate custom colTreeNodes in time for LOD data
        if hasColTreeNodes:
            self.colTreeNodes = c_colTreeNodes()

        self.lods_Offset = currentOffset
        self.lods = c_lods(self.lods_Offset, self.batches)
        self.lods_Size = self.lods.lods_StructSize
        self.lodsCount = len(self.lods.lods)
        currentOffset += self.lods_Size
        print('lods_Size: ', self.lods_Size)

        currentOffset += 16 - (currentOffset % 16)

        self.meshMaterials_Offset = currentOffset
        self.meshMaterials = c_meshMaterials()
        self.meshMaterials_Size = self.meshMaterials.meshMaterials_StructSize
        currentOffset += self.meshMaterials_Size
        print('meshMaterials_Size: ', self.meshMaterials_Size)

        currentOffset += (currentOffset % 16)

        # ColTreeNodes Data actually gets stored here
        if hasColTreeNodes:
            self.colTreeNodes_Offset = currentOffset
            self.colTreeNodesSize = self.colTreeNodes.colTreeNodesSize
            self.colTreeNodesCount = self.colTreeNodes.colTreeNodesCount
            currentOffset += self.colTreeNodesSize
        else:
            self.colTreeNodes = None
            self.colTreeNodes_Offset = 0
            self.colTreeNodesCount = 0

        currentOffset += (currentOffset % 16)

        if hasArmature:
            self.boneSets_Offset = currentOffset

            if len(self.boneMap.boneMap) > 1:
                self.boneSet = c_boneSet(self.boneMap, self.boneSets_Offset)
                self.boneSet_Size = self.boneSet.boneSet_StructSize
                currentOffset += self.boneSet_Size
            else:
                self.boneSets_Offset = 0

            currentOffset += (currentOffset % 16)

            self.boneMap_Offset = currentOffset
            self.boneMap_Size = self.boneMap.boneMap_StructSize
            currentOffset += self.boneMap_Size
            print('boneMap_Size: ', self.boneMap_Size)
        else:
            self.boneMap_Offset = 0
            self.boneSets_Offset = 0

        self.meshes_Offset = currentOffset
        self.meshes = c_meshes(self.meshes_Offset)
        self.meshes_Size = self.meshes.meshes_StructSize
        currentOffset += self.meshes_Size
        print('meshes_Size: ', self.meshes_Size)
        if not hasArmature:
            for mesh in self.meshes.meshes:
                mesh.numBones = 0

        currentOffset += (currentOffset % 16)

        self.materials_Offset = currentOffset
        self.materials = c_materials(self.materials_Offset)
        self.materials_Size = self.materials.materials_StructSize
        currentOffset += self.materials_Size
        print('materials_Size: ', self.materials_Size)

        if hasUnknownWorldData:
            self.unknownWorldData_Offset = currentOffset
            self.unknownWorldData = c_unknownWorldData()
            self.unknownWorldDataSize = self.unknownWorldData.unknownWorldDataSize
            self.unknownWorldDataCount = self.unknownWorldData.unknownWorldDataCount
            currentOffset += self.unknownWorldDataSize
        else:
            self.unknownWorldData = None
            self.unknownWorldData_Offset = 0
            self.unknownWorldDataCount = 0

        self.meshMaterials.updateLods(self.lods)