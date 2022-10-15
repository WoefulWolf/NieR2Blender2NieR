import bpy
from ....utils.util import getAllBonesInOrder

class c_boneIndexTranslateTable(object):
    def __init__(self):

        self.firstLevel = []
        self.secondLevel = []
        self.thirdLevel = []

        for obj in bpy.data.collections['WMB'].all_objects:
            if obj.type == 'ARMATURE':
                self.firstLevel = obj.data['firstLevel']
                self.secondLevel = obj.data['secondLevel']
                #print("OG", list(obj.data['thirdLevel']))


        secondLevelRanges = []
        for i, val in enumerate(self.firstLevel):
            if val != -1:
                secondLevelRanges.append(i * 256)

        thirdLevelRanges = []
        counter = 0
        secondLevelIdx = 0
        for i, val in enumerate(self.secondLevel):
            if i % 16 == 0:
                counter = secondLevelRanges[secondLevelIdx]
                secondLevelIdx += 1
            if val != -1:
                thirdLevelRanges.append(counter)
            counter += 16

        # Generate empty table
        newThirdLevel = []
        for val in thirdLevelRanges:
            for i in range(16):
                newThirdLevel.append(4095)
        
        # Populate the third level
        for i, bone in enumerate(getAllBonesInOrder("WMB")):
            if 'ID' not in bone:
                continue
            boneID = bone['ID']         
            for k, domain in enumerate(thirdLevelRanges):
                if boneID >= domain and boneID < domain + 16:
                    newThirdLevel[k * 16 + boneID - domain] = i
                    break

        # Add new bones that dont have ID
        for i, bone in enumerate(getAllBonesInOrder("WMB")):
            if 'ID' not in bone:
                for k in range(len(newThirdLevel) - 1, 0, -1):
                    if newThirdLevel[k] == 4095:
                        newThirdLevel[k] = i
                        bone['ID'] = 4095 - (len(newThirdLevel) - 1 - k)
                        print("Added new bone to table", bone.name, "assigning ID", bone['ID'], "at index", k)
                        break

        self.thirdLevel = newThirdLevel
                
        self.firstLevel_Size = len(self.firstLevel)

        self.secondLevel_Size = len(self.secondLevel)   

        self.thirdLevel_Size = len(self.thirdLevel)

        self.boneIndexTranslateTable_StructSize = self.firstLevel_Size*2 + self.secondLevel_Size*2 + self.thirdLevel_Size*2