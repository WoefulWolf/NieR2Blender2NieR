import bpy


class c_boneMap(object):
    def __init__(self, bones):
        boneMap = []
        for obj in bpy.data.collections['WMB'].all_objects:
            if obj.type == 'ARMATURE':
                boneMap = obj.data['boneMap']
        
        self.boneMap = boneMap

        self.boneMap_StructSize = len(boneMap) * 4