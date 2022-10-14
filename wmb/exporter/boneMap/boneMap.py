import bpy


class c_boneMap(object):
    def __init__(self, bones):
        boneMap = []
        #for obj in bpy.data.collections['WMB'].all_objects:
        #    if obj.type == 'ARMATURE':
        #        boneMap = obj.data['boneMap']
        for obj in bpy.data.collections['WMB'].all_objects:
            if obj.type == 'MESH':
                for group in obj.vertex_groups:
                    boneID = int(group.name.replace("bone", ""))
                    if boneID not in boneMap:
                            print("Adding ID to boneMap: " + str(boneID))
                            boneMap.append(boneID)

        boneMap = sorted(boneMap)
        for obj in bpy.data.collections['WMB'].all_objects:
            if obj.type == 'ARMATURE':
                obj.data['boneMap'] = boneMap
                break
        
        self.boneMap = boneMap
        print("BoneMap Size: ", len(self.boneMap))

        self.boneMap_StructSize = len(boneMap) * 4