from blender2nier.util import *

headerSize = 136 + 8

def create_wmb_header(wmb_file, data):

    print('Creating header:')
    write_string(wmb_file, 'WMB3')                              # id
    write_uInt32(wmb_file, 538312982)                           # version
    write_Int32(wmb_file, 0)                                    # unknownA
    write_Int16(wmb_file, 8)                                    # flags
    write_Int16(wmb_file, 0)                                    # unknownTerminator
    write_xyz(wmb_file, [0.5, 0.5, 0.5])                        # boundingBox: x y z    TODO
    write_xyz(wmb_file, [0.5, 0.5, 0.5])                        #              u v w    TODO

    write_uInt32(wmb_file, headerSize)                          # offsetBones
    print(' + offsetBones: ', headerSize)

    numBones = len(data.bones.bones)
    write_uInt32(wmb_file, numBones)                            # numBones
    print(' + numBones: ', numBones)

    offsetBoneIndexTranslateTable = (headerSize + 8) + data.bones_Size
    write_uInt32(wmb_file, offsetBoneIndexTranslateTable)       # offsetBoneIndexTranslateTable
    print(' + offsetBoneIndexTranslateTable: ', offsetBoneIndexTranslateTable)

    boneTranslateTableSize = data.bones_Size + 8
    write_uInt32(wmb_file, boneTranslateTableSize)              # boneTranslateTableSize TODO
    print(' + boneTranslateTableSize: ', boneTranslateTableSize)

    offsetVertexGroups = offsetBoneIndexTranslateTable + boneTranslateTableSize
    write_uInt32(wmb_file, offsetVertexGroups)                  # offsetVertexGroups
    print(' + offsetVertexGroups: ', offsetVertexGroups)

    numVertexGroups = len(data.vertexGroups.vertexGroups)
    write_uInt32(wmb_file, numVertexGroups)                     # numVertexGroups
    print(' + numVertexGroups: ', numVertexGroups)

    offsetBatches = offsetVertexGroups + data.vertexGroups.vertexGroups_StructSize
    write_uInt32(wmb_file, offsetBatches)                       # offsetBatches
    print(' + offsetBatches: ', offsetBatches)

    bones = data.bones.bones
    print(bones)
    #vertexes = get_vertexes()
