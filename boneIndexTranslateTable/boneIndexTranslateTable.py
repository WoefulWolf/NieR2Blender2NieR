import bpy, bmesh, math

class c_boneIndexTranslateTable(object):
    def __init__(self, bones):

        self.firstLevel = []
        self.secondLevel = []
        self.thirdLevel = []

        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE':
                for idx in range(len(obj.data['firstLevel'])):
                    self.firstLevel.append(obj.data['firstLevel'][idx])

                for idx in range(len(obj.data['secondLevel'])):
                    self.secondLevel.append(obj.data['secondLevel'][idx])

                for idx in range(len(obj.data['thirdLevel'])):
                    self.thirdLevel.append(obj.data['thirdLevel'][idx])

        self.firstLevel_Size = len(self.firstLevel)

        self.secondLevel_Size = len(self.secondLevel)   

        self.thirdLevel_Size = len(self.thirdLevel)


        self.boneIndexTranslateTable_StructSize = self.firstLevel_Size*2 + self.secondLevel_Size*2 + self.thirdLevel_Size*2