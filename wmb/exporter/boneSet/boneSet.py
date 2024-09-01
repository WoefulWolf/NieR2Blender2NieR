import bpy
from ....utils.util import getBoneIndexByName

class c_boneSet(object):
    def __init__(self, boneMap, boneSets_Offset):

        def get_blender_boneSets(self):
            b_boneSets = []
            for obj in bpy.data.collections['WMB'].all_objects:
                if obj.type == 'ARMATURE':
                    for boneSet in obj.data['boneSetArray']:
                        b_boneSets.append(boneSet)
            
            return b_boneSets

        def get_boneSets(self, b_boneSets, boneSets_Offset):
            boneSets = []

            b_offset = boneSets_Offset + len(b_boneSets) * 8

            for b_boneSet in b_boneSets:
                numBoneIndexes = len(b_boneSet)

                boneSets.append([b_offset, numBoneIndexes, b_boneSet])
                b_offset += len(b_boneSet) * 2

            return boneSets
        
        blender_boneSets = get_blender_boneSets(self)

        self.boneSet = get_boneSets(self, blender_boneSets, boneSets_Offset)

        def get_boneSet_StructSize(self):
            boneSet_StructSize = len(self.boneSet) * 8
            for boneSet in self.boneSet:
                boneSet_StructSize += len(boneSet[2]) * 2
            return boneSet_StructSize


        self.boneSet_StructSize = get_boneSet_StructSize(self)

class c_b_boneSets(object):
    def __init__(self):
        # Find Armature
        for obj in bpy.data.collections['WMB'].all_objects:
            if obj.type == 'ARMATURE':
                amt = obj

        # Generate boneMap
        boneMap = []
        for obj in bpy.data.collections['WMB'].all_objects:
            if obj.type == 'MESH':
                for group in obj.vertex_groups:
                    boneID = getBoneIndexByName("WMB", group.name)
                    if boneID not in boneMap:
                        #print("Adding ID to boneMap: " + str(boneID))
                        if boneID != None:
                            boneMap.append(boneID)

        # Set boneMap to armature
        boneMap = sorted(boneMap)
        for obj in bpy.data.collections['WMB'].all_objects:
            if obj.type == 'ARMATURE':
                obj.data['boneMap'] = boneMap
                break

        # Get boneSets
        b_boneSets = []
        for obj in bpy.data.collections['WMB'].all_objects:
            if obj.type == 'MESH':
                vertex_group_bones = []
                if obj['boneSetIndex'] != -1:
                    for group in obj.vertex_groups:
                        boneID = getBoneIndexByName("WMB", group.name)
                        if boneID != None:
                            boneMapIndex = boneMap.index(boneID)
                            vertex_group_bones.append(boneMapIndex)
                        
                    if vertex_group_bones not in b_boneSets:
                        b_boneSets.append(vertex_group_bones)
                        obj["boneSetIndex"] = len(b_boneSets)-1
                    else:
                        obj["boneSetIndex"] = b_boneSets.index(vertex_group_bones)

        amt.data['boneSetArray'] = b_boneSets
