from ....utils.ioUtils import write_char, write_Int32, write_uInt32, write_Int16, write_xyz
from ....utils.util import *


def create_wmb_header(wmb_file, data):

    print('Writing header:')
    for char in 'WMB3':                                         # id
        write_char(wmb_file, char)                                 
    write_uInt32(wmb_file, 538312982)                           # version
    write_Int32(wmb_file, 0)                                    # unknownA
    if data.vertexGroups.vertexGroups[0].vertexFlags in [4, 5] and data.numBones > 0:
        write_Int16(wmb_file, 8)                                    # flags
        write_Int16(wmb_file, 0)                                    # referenceBone
    elif data.vertexGroups.vertexGroups[0].vertexFlags in [4, 5, 14]:
        write_Int16(wmb_file, 8)                                    
        write_Int16(wmb_file, -1) 
    else:
        write_Int16(wmb_file, 10)                                    
        write_Int16(wmb_file, -1)
    
    boundingBoxXYZ, boundingBoxUVW = getGlobalBoundingBox()
    write_xyz(wmb_file, boundingBoxXYZ)                        # boundingBox: x y z 
    write_xyz(wmb_file, boundingBoxUVW)                        #              u v w

    offsetBones = data.bones_Offset
    write_uInt32(wmb_file, offsetBones)                          # offsetBones
    print(' + offsetBones: ', hex(offsetBones))

    numBones = data.numBones
    write_uInt32(wmb_file, numBones)                            # numBones
    print(' + numBones: ', numBones)

    offsetBoneIndexTranslateTable = data.boneIndexTranslateTable_Offset
    write_uInt32(wmb_file, offsetBoneIndexTranslateTable)       # offsetBoneIndexTranslateTable
    print(' + offsetBoneIndexTranslateTable: ', hex(offsetBoneIndexTranslateTable))

    if hasattr(data, 'boneIndexTranslateTable'):
        boneTranslateTableSize = data.boneIndexTranslateTable.boneIndexTranslateTable_StructSize
    else:
        boneTranslateTableSize = 0
    write_uInt32(wmb_file, boneTranslateTableSize)              # boneTranslateTableSize
    print(' + boneTranslateTableSize: ', boneTranslateTableSize)

    offsetVertexGroups = data.vertexGroups_Offset
    write_uInt32(wmb_file, offsetVertexGroups)                  # offsetVertexGroups
    print(' + offsetVertexGroups: ', hex(offsetVertexGroups))

    numVertexGroups = len(data.vertexGroups.vertexGroups)
    write_uInt32(wmb_file, numVertexGroups)                     # numVertexGroups
    print(' + numVertexGroups: ', numVertexGroups)

    offsetBatches = data.batches_Offset
    write_uInt32(wmb_file, offsetBatches)                       # offsetBatches
    print(' + offsetBatches: ', hex(offsetBatches))

    numBatches = len(data.batches.batches)
    write_uInt32(wmb_file, numBatches)                          # numBatches
    print(' + numBatches: ', numBatches)

    offsetLods = data.lods_Offset
    write_uInt32(wmb_file, offsetLods)                          # offsetLods
    print(' + offsetLods: ', hex(offsetLods))

    numLods = data.lodsCount                                    
    write_uInt32(wmb_file, numLods)                             # numLods
    print(' + numLods: ', numLods)

    offsetColTreeNodes = data.colTreeNodes_Offset                                      
    write_uInt32(wmb_file, offsetColTreeNodes)                  # offsetColTreeNodes
    print(' + offsetColTreeNodes: ', hex(offsetColTreeNodes))

    numColTreeNodes = data.colTreeNodesCount    
    write_uInt32(wmb_file, numColTreeNodes)                     # numColTreeNodes
    print(' + numColTreeNodes: ', numColTreeNodes)

    offsetBoneMap = data.boneMap_Offset
    write_uInt32(wmb_file, offsetBoneMap)                       # offsetBoneMap
    print(' + offsetBoneMap: ', hex(offsetBoneMap))

    numBoneMap = data.numBoneMap
    write_uInt32(wmb_file, numBoneMap)                          # numBoneMap/boneMapSize
    print(' + numBoneMap: ', numBoneMap)

    offsetBoneSets = data.boneSets_Offset                
    write_uInt32(wmb_file, offsetBoneSets)                      # offsetBoneSets
    print(' + offsetBoneSets: ', hex(offsetBoneSets))

    if hasattr(data, 'boneSet'):
        numBoneSets = len(data.boneSet.boneSet)   
    else:
        numBoneSets = 0                          
    write_uInt32(wmb_file, numBoneSets)                         # numBoneSets
    print(' + numBoneSets: ', numBoneSets)

    offsetMaterials = data.materials_Offset
    write_uInt32(wmb_file, offsetMaterials)                     # offsetMaterials
    print(' + offsetMaterials: ', hex(offsetMaterials))

    numMaterials = len(data.materials.materials)
    write_uInt32(wmb_file, numMaterials)                        # numMaterials
    print(' + numMaterials: ', numMaterials)

    offsetMeshes = data.meshes_Offset
    write_uInt32(wmb_file, offsetMeshes)                        # offsetMeshes
    print(' + offsetMeshes: ', hex(offsetMeshes))

    numMeshes = len(data.meshes.meshes)
    write_uInt32(wmb_file, numMeshes)                           # numMeshes
    print(' + numMeshes: ', numMeshes)

    offsetMeshMaterials = data.meshMaterials_Offset
    write_uInt32(wmb_file, offsetMeshMaterials)                  # offsetMeshMaterials
    print(' + offsetMeshMaterial: ', hex(offsetMeshMaterials))

    numMeshMaterials = len(data.meshMaterials.meshMaterials)
    write_uInt32(wmb_file, numMeshMaterials)                    # numMeshMaterials
    print(' + numMeshMaterials: ', numMeshMaterials)

    offsetUnknown0 = data.unknownWorldData_Offset
    write_uInt32(wmb_file, offsetUnknown0)                      # offsetUnknown0
    print(' + offsetUnknown0: ', hex(offsetUnknown0))

    numUnknown0 = data.unknownWorldDataCount
    write_uInt32(wmb_file, numUnknown0)                          # numUnknown0
    print(' + numUnknown0: ', numUnknown0)