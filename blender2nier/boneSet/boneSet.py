import bpy, bmesh, math

class c_boneSet(object):
    def __init__(self, boneMap, boneSet_Offset):

        def get_boneSet(self, boneMap, boneSet_Offset):
            boneSets = []
            numBoneSet = len(boneMap.boneMap)

            offsetBoneSet = boneSet_Offset + numBoneSet * 8
            for index, bone in enumerate(boneMap.boneMap):
                numBoneIndexes = 1
                boneIndexes = index
                boneSets.append([offsetBoneSet, numBoneIndexes, boneIndexes])
                offsetBoneSet += 2
            return boneSets
        
        self.boneSet = get_boneSet(self, boneMap, boneSet_Offset)
        self.boneSet_StructSize = len(self.boneSet) * 10