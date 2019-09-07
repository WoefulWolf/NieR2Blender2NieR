from blender2nier.util import *
from blender2nier.get_data import *

current_offset = 0

def create_wmb_head(wmb_file):
    print('Creating header:')
    write_string(wmb_file, 'WMB3')                              # id
    write_uInt32(wmb_file, 538312982)                           # version
    write_Int32(wmb_file, 0)                                    # unknownA
    write_Int16(wmb_file, 8)                                    # flags
    write_Int16(wmb_file, 0)                                    # unknownTerminator
    write_xyz(wmb_file, [0.5, 0.5, 0.5])                        # boundingBox: x y z    TODO
    write_xyz(wmb_file, [0.5, 0.5, 0.5])                        #              u v w    TODO

    write_uInt32(wmb_file, header_size)                         # offsetBones
    print(' + offsetBones: ', header_size)

    write_uInt32(wmb_file, get_numBones())                      # numBones
    print(' + numBones: ', get_numBones())

    write_uInt32(wmb_file, get_offsetBoneIndexTranslateTable()) # offsetBoneIndexTranslateTable
    print(' + offsetBoneIndexTranslateTable: ', get_offsetBoneIndexTranslateTable())

    write_uInt32(wmb_file, get_boneTranslateTableSize())        # boneTranslateTableSize
    print(' + boneTranslateTableSize: ', get_boneTranslateTableSize())

    write_uInt32(wmb_file, get_offsetVertexGroups())            # offsetVertexGroups
    print(' + offsetVertexGroups: ', get_offsetVertexGroups())

    write_uInt32(wmb_file, get_numVertexGroups())               # numVertexGroups
    print(' + numVertexGroups: ', get_numVertexGroups())