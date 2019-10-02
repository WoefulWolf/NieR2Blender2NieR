import bpy, bmesh, math

class c_boneIndexTranslateTable(object):
    def __init__(self, bones):

        def get_firstLevel(self, bones):
            firstLevel_Size = 16               # I 'think' firstLevel is always 16
            firstLevel = [-1] * firstLevel_Size
                           

            for bone in bones.bones:
                if len(bones.bones) == 1:
                    print(bone[0])
                    if bone[0] == 5:
                        firstLevel[0] = 16
            
            print(firstLevel)
            return firstLevel

        self.firstLevel_Size = 16
        self.firstLevel = get_firstLevel(self, bones)


        def get_secondLevel_Size(self):
            secondLevel_Size = 0
            for firstLevel in self.firstLevel:
                if firstLevel != -1:
                    secondLevel_Size += 1
            return secondLevel_Size * 16

        def get_secondLevel(self):
            secondLevel = [-1] * get_secondLevel_Size(self)

            secondLevel[0] = 32             # THIS IS NOT LEGIT, GOT FROM BINARY NEEDS TO BE CHANGED PER MODEL TYPE
            
            print(secondLevel)
            return secondLevel

        self.secondLevel_Size = get_secondLevel_Size(self)
        self.secondLevel = get_secondLevel(self)
        

        def get_thirdLevel_Size(self):
            thirdLevel_Size = 0
            for secondLevel in self.secondLevel:
                if secondLevel != -1:
                    thirdLevel_Size += 1
            return thirdLevel_Size * 16

        def get_thirdLevel(self):
            thirdLevel = [4095] * get_thirdLevel_Size(self)

            for bone in bones.bones:
                thirdLevel[bone[0]] = 0

            print(thirdLevel)
            return thirdLevel

        self.thirdLevel_Size = get_thirdLevel_Size(self)
        self.thirdLevel = get_thirdLevel(self)
        self.boneIndexTranslateTable_StructSize = 16*2 + self.secondLevel_Size*2 + self.thirdLevel_Size*2