import bpy
from ....utils.util import boneHasID, getAllBonesInOrder, getBoneID

class c_boneIndexTranslateTable(object):
    def __init__(self):

        fullLookup = [0xfff] * 0x1000

        # Get existing boneIDs
        for i, bone in enumerate(getAllBonesInOrder("WMB")):
            if not boneHasID(bone):
                continue
            boneID = getBoneID(bone)
            if not 0 <= boneID < 0x1000: # force re-generate
                continue
            fullLookup[boneID] = i

        # Add new bones that dont have ID
        newBones = []
        for i, bone in enumerate(getAllBonesInOrder("WMB")):
            if boneHasID(bone):
                continue
            for k in range(0x1000 - 1, 0, -1):
                if fullLookup[k] == 0xfff:
                    fullLookup[k] = i
                    
                    new_id = k
                    print("Added new bone to table:", bone.name, "assigning ID", new_id)
                    new_name = "bone" + str(new_id) + "_" + bone.name
                    
                    for obj in bpy.data.collections['WMB'].all_objects:
                        if obj.type == 'MESH':
                            for vgroup in obj.vertex_groups:
                                if vgroup.name == bone.name:
                                    vgroup.name = new_name
                                    break

                    bone.name = new_name
                    newBones.append(bone)
                    break

        self.firstLevel = [-1] * 0x10
        self.secondLevel = []
        self.thirdLevel = []

        # firstLevel -- skip ranges of 0x100 that are completely empty
        curIndex = 0x10
        for i in range(0x10):
            partialLookup = fullLookup[0x100 * i : 0x100 * (i + 1)]
            if all([x == 0xfff for x in partialLookup]):
                continue
            self.firstLevel[i] = curIndex
            curIndex += 0x10

        # secondLevel -- skip ranges of 0x10 that are completely empty
        for i in range(0x10):
            if self.firstLevel[i] == -1:
                continue
            # i corresponds to the start of a chunk of 0x100 bone indexes
            partialLookup = fullLookup[0x100 * i : 0x100 * (i + 1)]
            newSecondLevel = [-1] * 0x10
            for j in range(0x10):
                partialPartialLookup = partialLookup[0x10 * j : 0x10 * (j + 1)]
                if all([x == 0xfff for x in partialPartialLookup]):
                    continue
                newSecondLevel[j] = curIndex
                curIndex += 0x10

            self.secondLevel.extend(newSecondLevel)

        # thirdLevel -- just chunks from fullLookup according to secondLevel
        for i, firstLevelItem in enumerate(self.firstLevel):
            if firstLevelItem == -1:
                continue
            # -0x10 because the first level is considered under the same index system
            secondLevelPortion = self.secondLevel[firstLevelItem - 0x10 : firstLevelItem]
            for j, secondLevelItem in enumerate(secondLevelPortion):
                if secondLevelItem == -1:
                    continue
                self.thirdLevel.extend(fullLookup[i * 0x100 + j * 0x10 : i * 0x100 + (j + 1) * 0x10])

        self.firstLevel_Size = len(self.firstLevel)

        self.secondLevel_Size = len(self.secondLevel)   

        self.thirdLevel_Size = len(self.thirdLevel)

        self.boneIndexTranslateTable_StructSize = self.firstLevel_Size*2 + self.secondLevel_Size*2 + self.thirdLevel_Size*2

        #Print the shit for the XML
        for bone in newBones:
            no = getBoneID(bone)
            if bone.parent in newBones:
                noUp = getBoneID(bone.parent)
            else:
                noUp = 4095
            if bone.children and bone.children[0] in newBones:
                noDown = getBoneID(bone.children[0])
            else:
                noDown = 4095

            out = """<CLOTH_WK>
    <no>{}</no>
    <noUp>{}</noUp>
    <noDown>{}</noDown>
    <noSide>4095</noSide>
    <noPoly>4095</noPoly>
    <noFix>4095</noFix>
    <rotLimit>0.5236</rotLimit>
    <offset>0 -0.1 0</offset>
    <m_OriginalRate>0</m_OriginalRate>
</CLOTH_WK>""".format(no, noUp, noDown)

            print(out)
        print("COPY TO YOUR <CLOTH_WK_LIST> AND REMEMBER TO ADD +{} TO THE <CLOTH_HEADER><m_Num> VALUE!".format(len(newBones)))