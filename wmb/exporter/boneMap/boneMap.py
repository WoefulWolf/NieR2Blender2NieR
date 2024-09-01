import bpy

# I should really just move this in with the boneSets, no ned for shit to be separate
class c_boneMap(object):
    def __init__(self, bones):
        boneMap = []
        for obj in bpy.data.collections['WMB'].all_objects:
            if obj.type == 'ARMATURE':
                boneMap = obj.data['boneMap']
                break
        
        self.boneMap = boneMap
        print("BoneMap Size: ", len(self.boneMap))

        self.boneMap_StructSize = len(boneMap) * 4