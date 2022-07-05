from ...utils.ioUtils import write_char, write_uInt32


def write_col_header(col_file, data):
    for char in 'COL2':                                         # id
        write_char(col_file, char)

    write_uInt32(col_file, 538251777)                           # version

    print("[>] offsetNameGroups:", data.offsetNameGroups)
    write_uInt32(col_file, data.offsetNameGroups)
    write_uInt32(col_file, data.nameGroupCount)

    print("[>] offsetMeshes:", data.offsetMeshes)
    write_uInt32(col_file, data.offsetMeshes)
    write_uInt32(col_file, data.meshCount)

    print("[>] offsetBoneMap:", data.offsetBoneMap)
    write_uInt32(col_file, data.offsetBoneMap)
    write_uInt32(col_file, data.boneMapCount)

    print("[>] offsetBoneMap2:", data.offsetBoneMap2)
    write_uInt32(col_file, data.offsetBoneMap2)
    write_uInt32(col_file, data.boneMap2Count)

    print("[>] offsetMeshMap:", data.offsetMeshMap)
    write_uInt32(col_file, data.offsetMeshMap)
    write_uInt32(col_file, data.meshMapCount)

    print("[>] offsetColTreeNodes:", data.offsetColTreeNodes)
    write_uInt32(col_file, data.offsetColTreeNodes)
    write_uInt32(col_file, data.colTreeNodeCount)