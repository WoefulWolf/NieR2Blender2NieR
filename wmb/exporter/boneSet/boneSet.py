import bpy
from ....utils.util import getBoneIndices, getIndexLookup, getAllMeshObjectsInOrder, getMeshName
from ..meshes.mesh import getMeshGroupBones

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
        boneIndices = getBoneIndices("WMB")
        amt = next(obj for obj in bpy.data.collections['WMB'].all_objects if obj.type == 'ARMATURE')
        meshes = getAllMeshObjectsInOrder('WMB')

        meshBones = []
        for obj in meshes:
            vertex_group_bones = []
            if not hasattr(obj, 'boneSetIndex') or obj['boneSetIndex'] != -1:
                for group in obj.vertex_groups:
                    boneID = boneIndices.get(group.name)
                    if boneID != None:
                        vertex_group_bones.append(boneID)
            meshBones.append(vertex_group_bones)

        # Generate boneMap
        usedBones = {boneID for bones in meshBones for boneID in bones}
        meshNames = set()
        for obj in meshes:
            if getMeshName(obj) not in meshNames:
                meshNames.add(getMeshName(obj))
                usedBones.update(getMeshGroupBones(obj))

        # Set boneMap to armature
        boneMap = sorted(usedBones)
        boneMapIndices = getIndexLookup(boneMap)
        amt.data['boneMap'] = boneMap

        # Get boneSets
        b_boneSets = []
        for obj, bones in zip(meshes, meshBones):
            if len(bones) == 0:
                continue
            vertex_group_bones = [boneMapIndices[boneID] for boneID in bones]

            if vertex_group_bones not in b_boneSets:
                b_boneSets.append(vertex_group_bones)
                obj["boneSetIndex"] = len(b_boneSets)-1
            else:
                obj["boneSetIndex"] = b_boneSets.index(vertex_group_bones)

        amt.data['boneSetArray'] = b_boneSets
        self.boneSets = b_boneSets
