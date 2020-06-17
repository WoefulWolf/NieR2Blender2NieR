import bpy, bmesh, math

class c_boneMap(object):
    def __init__(self, bones):
        boneMap = []
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE':
                boneMap = obj.data['boneMap']
        
        self.boneMap = boneMap

        self.boneMap_StructSize = len(boneMap) * 4