import bpy, bmesh, math

class c_boneMap(object):
    def __init__(self, bones):
        boneMap = []
        for index, bone in enumerate(bones.bones):
            if bone[1] not in [-1, 0]:
                boneMap.append(index)

        if len(boneMap) == 0:
            boneMap.append(0)
        
        self.boneMap = boneMap

        self.boneMap_StructSize = len(boneMap) * 4