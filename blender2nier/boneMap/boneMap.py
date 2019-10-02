import bpy, bmesh, math

class c_boneMap(object):
    def __init__(self, bones):
        boneMap = []
        for index, bone in enumerate(bones.bones):
            boneMap.append(index)
        
        self.boneMap = boneMap
        self.boneMap_StructSize = len(boneMap) * 4