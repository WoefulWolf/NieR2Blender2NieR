import bpy


class c_boneIndexTranslateTable(object):
    def __init__(self, bones):

        self.firstLevel = []
        self.secondLevel = []
        self.thirdLevel = []

        for obj in bpy.data.collections['WMB'].all_objects:
            if obj.type == 'ARMATURE':
                self.firstLevel = obj.data['firstLevel']
                self.secondLevel = obj.data['secondLevel']
                self.thirdLevel = obj.data['thirdLevel']

        self.firstLevel_Size = len(self.firstLevel)

        self.secondLevel_Size = len(self.secondLevel)   

        self.thirdLevel_Size = len(self.thirdLevel)


        self.boneIndexTranslateTable_StructSize = self.firstLevel_Size*2 + self.secondLevel_Size*2 + self.thirdLevel_Size*2