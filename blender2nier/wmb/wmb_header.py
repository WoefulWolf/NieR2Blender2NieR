from blender2nier.util import *

def create_wmb_header(wmb_file, data):

    print('Creating header:')
    for char in 'WMB3':                                         # id
        write_char(wmb_file, char)                                 
    write_uInt32(wmb_file, 538312982)                           # version
    write_Int32(wmb_file, 0)                                    # unknownA
    if data.vertexGroups.vertexGroups[0].vertexFlags == 4:
        write_Int16(wmb_file, 8)                                    # flags
        write_Int16(wmb_file, 0)                                    # referenceBone
    else:
        write_Int16(wmb_file, 10)                                    
        write_Int16(wmb_file, -1)
    write_xyz(wmb_file, [0.5, 0.5, 0.5])                        # boundingBox: x y z    TODO
    write_xyz(wmb_file, [0.5, 0.5, 0.5])                        #              u v w    TODO

    offsetBones = data.bones_Offset
    write_uInt32(wmb_file, offsetBones)                          # offsetBones
    print(' + offsetBones: ', offsetBones)

    numBones = data.numBones
    write_uInt32(wmb_file, numBones)                            # numBones
    print(' + numBones: ', numBones)

    offsetBoneIndexTranslateTable = data.boneIndexTranslateTable_Offset
    write_uInt32(wmb_file, offsetBoneIndexTranslateTable)       # offsetBoneIndexTranslateTable
    print(' + offsetBoneIndexTranslateTable: ', offsetBoneIndexTranslateTable)

    boneTranslateTableSize = data.bones_Size + 8
    write_uInt32(wmb_file, boneTranslateTableSize)              # boneTranslateTableSize TODO
    print(' + boneTranslateTableSize: ', boneTranslateTableSize)

    offsetVertexGroups = data.vertexGroups_Offset
    write_uInt32(wmb_file, offsetVertexGroups)                  # offsetVertexGroups
    print(' + offsetVertexGroups: ', offsetVertexGroups)

    numVertexGroups = len(data.vertexGroups.vertexGroups)
    write_uInt32(wmb_file, numVertexGroups)                     # numVertexGroups
    print(' + numVertexGroups: ', numVertexGroups)

    offsetBatches = data.batches_Offset
    write_uInt32(wmb_file, offsetBatches)                       # offsetBatches
    print(' + offsetBatches: ', offsetBatches)

    numBatches = len(data.batches.batches)
    write_uInt32(wmb_file, numBatches)                          # numBatches
    print(' + numBatches: ', numBatches)

    offsetLods = data.lods_Offset
    write_uInt32(wmb_file, offsetLods)                          # offsetLods
    print(' + offsetLods: ', offsetLods)

    numLods = 1                                                 # TODO
    write_uInt32(wmb_file, numLods)                             # numLods
    print(' + numLods: ', numLods)

    offsetColTreeNodes = 0                                      # TODO
    write_uInt32(wmb_file, offsetColTreeNodes)                  # offsetColTreeNodes
    print(' + offsetColTreeNodes: ', offsetColTreeNodes)

    numColTreeNodes = 0                                         # TODO
    write_uInt32(wmb_file, numColTreeNodes)                     # numColTreeNodes
    print(' + numColTreeNodes: ', numColTreeNodes)

    offsetBoneMap = data.boneMap_Offset
    write_uInt32(wmb_file, offsetBoneMap)                       # offsetBoneMap
    print(' + offsetBoneMap: ', offsetBoneMap)

    numBoneMap = data.numBoneMap
    write_uInt32(wmb_file, numBoneMap)                          # numBoneMap/boneMapSize
    print(' + numBoneMap: ', numBoneMap)


    offsetBoneSets = data.boneSet_Offset                
    write_uInt32(wmb_file, offsetBoneSets)                      # offsetBoneSets
    print(' + offsetBoneSets: ', offsetBoneSets)

    if hasattr(data, 'boneSet'):
        numBoneSets = len(data.boneSet.boneSet)   
    else:
        numBoneSets = 0                          
    write_uInt32(wmb_file, numBoneSets)                         # numBoneSets
    print(' + numBoneSets: ', numBoneSets)

    offsetMaterials = data.materials_Offset
    write_uInt32(wmb_file, offsetMaterials)                     # offsetMaterials
    print(' + offsetMaterials: ', offsetMaterials)

    numMaterials = len(data.materials.materials)
    write_uInt32(wmb_file, numMaterials)                        # numMaterials
    print(' + numMaterials: ', numMaterials)

    offsetMeshes = data.meshes_Offset
    write_uInt32(wmb_file, offsetMeshes)                        # offsetMeshes
    print(' + offsetMeshes: ', offsetMeshes)

    numMeshes = len(data.meshes.meshes)
    write_uInt32(wmb_file, numMeshes)                           # numMeshes
    print(' + numMeshes: ', numMeshes)

    offsetMeshMaterials = data.meshMaterials_Offset
    write_uInt32(wmb_file, offsetMeshMaterials)                  # offsetMeshMaterials
    print(' + offsetMeshMaterial: ', offsetMeshMaterials)

    numMeshMaterials = len(data.meshMaterials.meshMaterials)
    write_uInt32(wmb_file, numMeshMaterials)                    # numMeshMaterials
    print(' + numMeshMaterials: ', numMeshMaterials)

    offsetUnknown0 = 0
    write_uInt32(wmb_file, offsetUnknown0)                      # offsetUnknown0
    print(' + offsetUnknown0: ', offsetUnknown0)

    numUnknown0 = 0
    write_uInt32(wmb_file, numUnknown0)                          # numUnknown0
    print(' + numUnknown0: ', numUnknown0)