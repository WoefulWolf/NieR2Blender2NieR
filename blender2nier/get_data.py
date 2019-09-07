import bpy, bmesh, math

header_size = 136 + 8

def get_numBones():
    numBones = 0

    for armature in [ob for ob in bpy.data.objects if ob.type == 'ARMATURE']:
        numBones += len(armature.data.bones)
    return numBones

def get_offsetBoneIndexTranslateTable():
    offsetBoneIndexTranslateTable = (header_size + 8) + (get_numBones() * 88)
    return offsetBoneIndexTranslateTable

def get_boneTranslateTableSize():
    boneTranslateTableSize = get_numBones() * 88 + 8
    return boneTranslateTableSize

def get_offsetVertexGroups():
    offsetVertexGroups = get_boneTranslateTableSize() + get_offsetBoneIndexTranslateTable()
    return offsetVertexGroups


def get_numVertexGroups():
    numVertexGroups = 0
    
    for obj in bpy.data.objects:
        numVertexGroups += len(obj.vertex_groups)
    return numVertexGroups

    